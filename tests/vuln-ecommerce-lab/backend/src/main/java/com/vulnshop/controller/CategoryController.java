package com.vulnshop.controller;

import com.vulnshop.dto.response.CategoryResponse;
import com.vulnshop.service.CategoryService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/categories")
public class CategoryController {

    private final CategoryService categoryService;

    public CategoryController(CategoryService categoryService) {
        this.categoryService = categoryService;
    }

    @GetMapping("/")
    public ResponseEntity<List<CategoryResponse>> getAllCategories() {
        return ResponseEntity.ok(categoryService.getAllCategories());
    }

    @GetMapping("/{slug}")
    public ResponseEntity<CategoryResponse> getCategoryBySlug(@PathVariable String slug) {
        return ResponseEntity.ok(categoryService.getCategoryBySlug(slug));
    }

    // VULN: Missing access control - should be admin only
    // createCategory(name, slug, description, parentId)
    @PostMapping("/")
    public ResponseEntity<CategoryResponse> createCategory(@RequestBody Map<String, String> request) {
        String name = request.get("name");
        String slug = request.get("slug");
        String description = request.get("description");
        Long parentId = request.containsKey("parentId") && request.get("parentId") != null
                ? Long.parseLong(request.get("parentId")) : null;
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(categoryService.createCategory(name, slug, description, parentId));
    }

    // VULN: Missing access control - should be admin only
    // updateCategory(id, name, slug, description)
    @PutMapping("/{id}")
    public ResponseEntity<CategoryResponse> updateCategory(@PathVariable Long id,
                                                            @RequestBody Map<String, String> request) {
        return ResponseEntity.ok(categoryService.updateCategory(
                id,
                request.get("name"),
                request.get("slug"),
                request.get("description")));
    }

    // VULN: Missing access control - should be admin only
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteCategory(@PathVariable Long id) {
        categoryService.deleteCategory(id);
        return ResponseEntity.noContent().build();
    }
}
