package com.vulnshop.service;

import com.vulnshop.dto.request.ProductCreateRequest;
import com.vulnshop.dto.request.ProductSearchRequest;
import com.vulnshop.dto.request.ProductUpdateRequest;
import com.vulnshop.dto.response.PageResponse;
import com.vulnshop.dto.response.ProductResponse;
import com.vulnshop.entity.Category;
import com.vulnshop.entity.Product;
import com.vulnshop.entity.User;
import com.vulnshop.exception.BadRequestException;
import com.vulnshop.exception.ResourceNotFoundException;
import com.vulnshop.repository.CategoryRepository;
import com.vulnshop.repository.ProductRepository;
import com.vulnshop.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.Comparator;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;

@Service
@Transactional
public class ProductService {

    private final ProductRepository productRepository;
    private final UserRepository userRepository;
    private final CategoryRepository categoryRepository;

    public ProductService(ProductRepository productRepository,
                          UserRepository userRepository,
                          CategoryRepository categoryRepository) {
        this.productRepository = productRepository;
        this.userRepository = userRepository;
        this.categoryRepository = categoryRepository;
    }

    public ProductResponse createProduct(Long sellerId, ProductCreateRequest request) {
        User seller = userRepository.findById(sellerId)
                .orElseThrow(() -> new ResourceNotFoundException("Seller not found: " + sellerId));

        Category category = null;
        if (request.getCategoryId() != null) {
            category = categoryRepository.findById(request.getCategoryId())
                    .orElseThrow(() -> new ResourceNotFoundException("Category not found: " + request.getCategoryId()));
        }

        Product product = Product.builder()
                .name(request.getName())
                .description(request.getDescription())
                .price(request.getPrice())
                .compareAtPrice(request.getCompareAtPrice())
                .sku(request.getSku())
                .stock(request.getStock())
                .imageUrl(request.getImageUrl())
                .weight(request.getWeight())
                .dimensions(request.getDimensions())
                .seller(seller)
                .category(category)
                .tags(request.getTags() != null ? request.getTags() : List.of())
                .build();

        return mapToResponse(productRepository.save(product));
    }

    public ProductResponse updateProduct(Long productId, ProductUpdateRequest request) {
        Product product = productRepository.findById(productId)
                .orElseThrow(() -> new ResourceNotFoundException("Product not found: " + productId));

        if (request.getName() != null) product.setName(request.getName());
        if (request.getDescription() != null) product.setDescription(request.getDescription());
        if (request.getPrice() != null) product.setPrice(request.getPrice());
        if (request.getCompareAtPrice() != null) product.setCompareAtPrice(request.getCompareAtPrice());
        if (request.getSku() != null) product.setSku(request.getSku());
        if (request.getStock() != null) product.setStock(request.getStock());
        if (request.getImageUrl() != null) product.setImageUrl(request.getImageUrl());
        if (request.getWeight() != null) product.setWeight(request.getWeight());
        if (request.getDimensions() != null) product.setDimensions(request.getDimensions());
        if (request.getTags() != null) product.setTags(request.getTags());
        if (request.getCategoryId() != null) {
            Category category = categoryRepository.findById(request.getCategoryId())
                    .orElseThrow(() -> new ResourceNotFoundException("Category not found: " + request.getCategoryId()));
            product.setCategory(category);
        }

        return mapToResponse(productRepository.save(product));
    }

    public void deleteProduct(Long productId) {
        Product product = productRepository.findById(productId)
                .orElseThrow(() -> new ResourceNotFoundException("Product not found: " + productId));
        productRepository.delete(product);
    }

    @Transactional(readOnly = true)
    public ProductResponse getProductById(Long productId) {
        Product product = productRepository.findById(productId)
                .orElseThrow(() -> new ResourceNotFoundException("Product not found: " + productId));
        return mapToResponse(product);
    }

    @Transactional(readOnly = true)
    public PageResponse<ProductResponse> getAllProducts(ProductSearchRequest request) {
        List<Product> all = productRepository.findByIsActiveTrue();

        Stream<Product> stream = all.stream();

        if (request.getQuery() != null && !request.getQuery().isBlank()) {
            String q = request.getQuery().toLowerCase();
            stream = stream.filter(p ->
                    (p.getName() != null && p.getName().toLowerCase().contains(q)) ||
                    (p.getDescription() != null && p.getDescription().toLowerCase().contains(q)));
        }
        if (request.getCategoryId() != null) {
            stream = stream.filter(p -> p.getCategory() != null && p.getCategory().getId().equals(request.getCategoryId()));
        }
        if (request.getMinPrice() != null) {
            stream = stream.filter(p -> p.getPrice().compareTo(request.getMinPrice()) >= 0);
        }
        if (request.getMaxPrice() != null) {
            stream = stream.filter(p -> p.getPrice().compareTo(request.getMaxPrice()) <= 0);
        }

        List<Product> filtered = stream.collect(Collectors.toList());

        // Sort
        Comparator<Product> comparator;
        switch (request.getSortBy()) {
            case "price" -> comparator = Comparator.comparing(Product::getPrice);
            case "averageRating" -> comparator = Comparator.comparingDouble(Product::getAverageRating);
            case "name" -> comparator = Comparator.comparing(Product::getName);
            default -> comparator = Comparator.comparing(Product::getCreatedAt);
        }
        if ("DESC".equalsIgnoreCase(request.getSortDirection())) {
            comparator = comparator.reversed();
        }
        filtered.sort(comparator);

        int total = filtered.size();
        int from = request.getPage() * request.getSize();
        int to = Math.min(from + request.getSize(), total);
        List<ProductResponse> content = (from >= total) ? List.of() :
                filtered.subList(from, to).stream().map(this::mapToResponse).collect(Collectors.toList());

        int totalPages = request.getSize() == 0 ? 1 : (int) Math.ceil((double) total / request.getSize());
        return PageResponse.of(content, total, totalPages, request.getPage(), request.getSize());
    }

    @Transactional(readOnly = true)
    public List<ProductResponse> getProductsByCategory(Long categoryId) {
        return productRepository.findByCategoryId(categoryId).stream()
                .map(this::mapToResponse)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public List<ProductResponse> getProductsBySeller(Long sellerId) {
        return productRepository.findBySellerIdAndIsActive(sellerId, true).stream()
                .map(this::mapToResponse)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public List<ProductResponse> searchProducts(String query) {
        return productRepository.searchByNameOrDescription(query).stream()
                .map(this::mapToResponse)
                .collect(Collectors.toList());
    }

    public ProductResponse updateStock(Long productId, int quantity) {
        Product product = productRepository.findById(productId)
                .orElseThrow(() -> new ResourceNotFoundException("Product not found: " + productId));
        if (quantity < 0) throw new BadRequestException("Stock cannot be negative");
        product.setStock(quantity);
        return mapToResponse(productRepository.save(product));
    }

    @Transactional(readOnly = true)
    public List<ProductResponse> getTopRatedProducts(int limit) {
        return productRepository.findTopByOrderByAverageRatingDesc().stream()
                .limit(limit)
                .map(this::mapToResponse)
                .collect(Collectors.toList());
    }

    public ProductResponse mapToResponse(Product product) {
        return ProductResponse.builder()
                .id(product.getId())
                .name(product.getName())
                .description(product.getDescription())
                .price(product.getPrice())
                .compareAtPrice(product.getCompareAtPrice())
                .sku(product.getSku())
                .stock(product.getStock())
                .imageUrl(product.getImageUrl())
                .thumbnailUrl(product.getThumbnailUrl())
                .weight(product.getWeight())
                .dimensions(product.getDimensions())
                .isActive(product.isActive())
                .averageRating(product.getAverageRating())
                .reviewCount(product.getReviewCount())
                .categoryName(product.getCategory() != null ? product.getCategory().getName() : null)
                .categoryId(product.getCategory() != null ? product.getCategory().getId() : null)
                .sellerName(product.getSeller() != null ?
                        product.getSeller().getFirstName() + " " + product.getSeller().getLastName() : null)
                .sellerId(product.getSeller() != null ? product.getSeller().getId() : null)
                .tags(product.getTags())
                .createdAt(product.getCreatedAt())
                .updatedAt(product.getUpdatedAt())
                .build();
    }
}
