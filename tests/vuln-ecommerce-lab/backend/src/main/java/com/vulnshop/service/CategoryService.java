package com.vulnshop.service;

import com.vulnshop.dto.response.CategoryResponse;
import com.vulnshop.entity.Category;
import com.vulnshop.exception.BadRequestException;
import com.vulnshop.exception.ResourceNotFoundException;
import com.vulnshop.repository.CategoryRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
@Transactional
public class CategoryService {

    private final CategoryRepository categoryRepository;

    public CategoryService(CategoryRepository categoryRepository) {
        this.categoryRepository = categoryRepository;
    }

    public CategoryResponse createCategory(String name, String slug, String description, Long parentId) {
        if (categoryRepository.findBySlug(slug).isPresent()) {
            throw new BadRequestException("Category slug already exists: " + slug);
        }
        Category parent = null;
        if (parentId != null) {
            parent = categoryRepository.findById(parentId)
                    .orElseThrow(() -> new ResourceNotFoundException("Parent category not found: " + parentId));
        }
        Category category = Category.builder()
                .name(name)
                .slug(slug)
                .description(description)
                .parentCategory(parent)
                .build();
        return mapToResponse(categoryRepository.save(category));
    }

    public CategoryResponse updateCategory(Long id, String name, String slug, String description) {
        Category category = categoryRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Category not found: " + id));
        if (name != null) category.setName(name);
        if (slug != null) category.setSlug(slug);
        if (description != null) category.setDescription(description);
        return mapToResponse(categoryRepository.save(category));
    }

    public void deleteCategory(Long id) {
        Category category = categoryRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Category not found: " + id));
        categoryRepository.delete(category);
    }

    @Transactional(readOnly = true)
    public List<CategoryResponse> getAllCategories() {
        return categoryRepository.findAll().stream()
                .map(this::mapToResponse)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public CategoryResponse getCategoryBySlug(String slug) {
        Category category = categoryRepository.findBySlug(slug)
                .orElseThrow(() -> new ResourceNotFoundException("Category not found with slug: " + slug));
        return mapToResponse(category);
    }

    @Transactional(readOnly = true)
    public List<CategoryResponse> getRootCategories() {
        return categoryRepository.findByParentCategoryIsNull().stream()
                .map(this::mapToResponse)
                .collect(Collectors.toList());
    }

    public CategoryResponse mapToResponse(Category category) {
        List<CategoryResponse> subcategories = category.getSubcategories() == null ? List.of() :
                category.getSubcategories().stream()
                        .map(sub -> CategoryResponse.builder()
                                .id(sub.getId())
                                .name(sub.getName())
                                .slug(sub.getSlug())
                                .description(sub.getDescription())
                                .imageUrl(sub.getImageUrl())
                                .subcategories(List.of())
                                .build())
                        .collect(Collectors.toList());

        return CategoryResponse.builder()
                .id(category.getId())
                .name(category.getName())
                .slug(category.getSlug())
                .description(category.getDescription())
                .imageUrl(category.getImageUrl())
                .subcategories(subcategories)
                .build();
    }
}
