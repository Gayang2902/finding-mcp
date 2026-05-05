package com.vulnshop.config;

import com.vulnshop.entity.*;
import com.vulnshop.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Slf4j
@Component
@org.springframework.core.annotation.Order(1)
@Profile("!test")
@RequiredArgsConstructor
public class DataSeeder implements CommandLineRunner {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @PersistenceContext
    private EntityManager em;

    @Override
    @Transactional
    public void run(String... args) {
        if (userRepository.count() > 0) {
            log.info("Database already seeded, skipping.");
            return;
        }

        log.info("Seeding database...");

        List<User> users = seedUsers();
        List<Category> categories = seedCategories();
        List<Product> products = seedProducts(users, categories);
        List<Address> addresses = seedAddresses(users);
        List<Order> orders = seedOrders(users, products, addresses);
        seedReviews(users, products);
        seedCoupons();
        seedCarts(users, products);
        seedNotifications(users, orders);

        log.info("Database seeding complete.");
    }

    // -------------------------------------------------------------------------
    // Users
    // -------------------------------------------------------------------------
    private List<User> seedUsers() {
        log.info("Seeding users...");
        List<User> users = new ArrayList<>();

        users.add(em.merge(User.builder()
                .email("admin@vulnshop.com")
                .password(passwordEncoder.encode("admin123"))
                .firstName("Admin")
                .lastName("User")
                .phone("555-000-0001")
                .role(Role.ADMIN)
                .enabled(true)
                .build()));

        users.add(em.merge(User.builder()
                .email("seller1@vulnshop.com")
                .password(passwordEncoder.encode("password123"))
                .firstName("Alice")
                .lastName("Smith")
                .phone("555-100-0001")
                .role(Role.SELLER)
                .enabled(true)
                .build()));

        users.add(em.merge(User.builder()
                .email("seller2@vulnshop.com")
                .password(passwordEncoder.encode("password123"))
                .firstName("Bob")
                .lastName("Johnson")
                .phone("555-100-0002")
                .role(Role.SELLER)
                .enabled(true)
                .build()));

        String[] customerFirstNames = {"Charlie", "Diana", "Eve", "Frank", "Grace", "Hank", "Ivy"};
        String[] customerLastNames = {"Brown", "Davis", "Wilson", "Miller", "Moore", "Taylor", "Anderson"};

        for (int i = 1; i <= 7; i++) {
            users.add(em.merge(User.builder()
                    .email("customer" + i + "@vulnshop.com")
                    .password(passwordEncoder.encode("password123"))
                    .firstName(customerFirstNames[i - 1])
                    .lastName(customerLastNames[i - 1])
                    .phone("555-200-000" + i)
                    .role(Role.CUSTOMER)
                    .enabled(true)
                    .build()));
        }

        em.flush();
        log.info("Seeded {} users.", users.size());
        return users;
    }

    // -------------------------------------------------------------------------
    // Categories
    // -------------------------------------------------------------------------
    private List<Category> seedCategories() {
        log.info("Seeding categories...");
        List<Category> all = new ArrayList<>();

        Category electronics = saveCategory("Electronics", "electronics", "Gadgets and tech products", null, 1);
        Category clothing = saveCategory("Clothing", "clothing", "Fashion and apparel", null, 2);
        Category books = saveCategory("Books", "books", "Books and literature", null, 3);
        Category homeGarden = saveCategory("Home & Garden", "home-garden", "Home and garden essentials", null, 4);

        all.add(electronics);
        all.add(clothing);
        all.add(books);
        all.add(homeGarden);

        // Electronics subcategories
        all.add(saveCategory("Phones", "phones", "Smartphones and accessories", electronics, 1));
        all.add(saveCategory("Laptops", "laptops", "Laptops and notebooks", electronics, 2));
        all.add(saveCategory("Accessories", "accessories", "Electronic accessories", electronics, 3));

        // Clothing subcategories
        all.add(saveCategory("Men", "men-clothing", "Men's clothing", clothing, 1));
        all.add(saveCategory("Women", "women-clothing", "Women's clothing", clothing, 2));
        all.add(saveCategory("Kids", "kids-clothing", "Kids' clothing", clothing, 3));

        em.flush();
        log.info("Seeded {} categories.", all.size());
        return all;
    }

    private Category saveCategory(String name, String slug, String description,
                                   Category parent, int displayOrder) {
        Category cat = Category.builder()
                .name(name)
                .slug(slug)
                .description(description)
                .parentCategory(parent)
                .displayOrder(displayOrder)
                .isActive(true)
                .build();
        em.persist(cat);
        return cat;
    }

    // -------------------------------------------------------------------------
    // Products
    // -------------------------------------------------------------------------
    private List<Product> seedProducts(List<User> users, List<Category> categories) {
        log.info("Seeding products...");

        User seller1 = users.get(1); // seller1
        User seller2 = users.get(2); // seller2

        // Find categories by slug
        Category phones = findCat(categories, "phones");
        Category laptops = findCat(categories, "laptops");
        Category accessories = findCat(categories, "accessories");
        Category men = findCat(categories, "men-clothing");
        Category women = findCat(categories, "women-clothing");
        Category kids = findCat(categories, "kids-clothing");
        Category books = findCat(categories, "books");
        Category homeGarden = findCat(categories, "home-garden");

        List<Product> products = new ArrayList<>();

        // Phones
        products.add(saveProduct("iPhone 15 Pro", "Latest Apple flagship with titanium design and A17 Pro chip.",
                "999.00", "1199.00", "APL-IP15PRO", 50, seller1, phones,
                List.of("apple", "smartphone", "ios"), 4.8, 320));
        products.add(saveProduct("Samsung Galaxy S24 Ultra", "Samsung's premium phone with S Pen and 200MP camera.",
                "1199.00", "1399.00", "SAM-GS24U", 35, seller1, phones,
                List.of("samsung", "android", "smartphone"), 4.7, 210));
        products.add(saveProduct("Google Pixel 8", "Pure Android experience with advanced AI features.",
                "699.00", "799.00", "GOO-PX8", 40, seller2, phones,
                List.of("google", "pixel", "android"), 4.5, 95));
        products.add(saveProduct("OnePlus 12", "Fast charging flagship killer with Snapdragon 8 Gen 3.",
                "799.00", "899.00", "OP-12", 25, seller2, phones,
                List.of("oneplus", "android", "flagship"), 4.4, 62));

        // Laptops
        products.add(saveProduct("MacBook Air M3", "Ultra-thin laptop with Apple M3 chip and all-day battery.",
                "1299.00", "1499.00", "APL-MBA-M3", 20, seller1, laptops,
                List.of("apple", "macbook", "laptop"), 4.9, 450));
        products.add(saveProduct("Dell XPS 15", "Premium Windows laptop with OLED display and 12th Gen Intel.",
                "1599.00", "1799.00", "DEL-XPS15", 15, seller1, laptops,
                List.of("dell", "windows", "laptop"), 4.6, 180));
        products.add(saveProduct("Lenovo ThinkPad X1 Carbon", "Business-class ultrabook with legendary keyboard.",
                "1399.00", "1599.00", "LEN-X1C", 12, seller2, laptops,
                List.of("lenovo", "thinkpad", "business"), 4.7, 130));
        products.add(saveProduct("ASUS ROG Zephyrus G14", "Gaming laptop with AMD Ryzen 9 and RTX 4060.",
                "1249.00", "1449.00", "ASU-ROG-G14", 18, seller2, laptops,
                List.of("asus", "gaming", "laptop"), 4.5, 88));

        // Accessories
        products.add(saveProduct("AirPods Pro 2nd Gen", "Apple wireless earbuds with active noise cancellation.",
                "249.00", "279.00", "APL-APP2", 100, seller1, accessories,
                List.of("apple", "earbuds", "wireless"), 4.7, 560));
        products.add(saveProduct("Sony WH-1000XM5", "Industry-leading noise cancelling over-ear headphones.",
                "349.00", "399.00", "SNY-WH1000", 60, seller1, accessories,
                List.of("sony", "headphones", "noise-cancelling"), 4.8, 890));
        products.add(saveProduct("Logitech MX Master 3S", "Advanced wireless mouse for power users.",
                "99.00", "119.00", "LOG-MXM3S", 80, seller2, accessories,
                List.of("logitech", "mouse", "wireless"), 4.6, 340));
        products.add(saveProduct("Anker 65W GaN Charger", "Compact 3-port fast charger for all devices.",
                "45.00", "55.00", "ANK-65W", 200, seller2, accessories,
                List.of("anker", "charger", "usb-c"), 4.5, 210));
        products.add(saveProduct("USB-C Hub 7-in-1", "Multiport hub with HDMI, USB-A, SD card reader.",
                "39.00", "49.00", "USB-HUB7", 150, seller2, accessories,
                List.of("hub", "usb-c", "adapter"), 4.3, 125));

        // Clothing — Men
        products.add(saveProduct("Men's Classic Polo Shirt", "Premium cotton polo for everyday wear.",
                "49.00", "65.00", "CLO-MPL-BLU", 200, seller1, men,
                List.of("polo", "men", "casual"), 4.2, 78));
        products.add(saveProduct("Men's Slim Fit Chinos", "Modern slim-fit chino pants in khaki.",
                "69.00", "89.00", "CLO-MCH-KHK", 120, seller1, men,
                List.of("chinos", "men", "pants"), 4.1, 55));
        products.add(saveProduct("Men's Running Shoes", "Lightweight running shoes with cushioned sole.",
                "129.00", "159.00", "CLO-MRS-BLK", 90, seller2, men,
                List.of("shoes", "running", "sports"), 4.4, 140));

        // Clothing — Women
        products.add(saveProduct("Women's Yoga Leggings", "High-waist compression leggings for yoga and gym.",
                "59.00", "79.00", "CLO-WYL-BLK", 180, seller1, women,
                List.of("leggings", "yoga", "women"), 4.6, 220));
        products.add(saveProduct("Women's Floral Sundress", "Light and breezy summer dress with floral print.",
                "79.00", "99.00", "CLO-WSD-FLR", 80, seller2, women,
                List.of("dress", "summer", "women"), 4.3, 90));

        // Clothing — Kids
        products.add(saveProduct("Kids' Graphic T-Shirt 3-Pack", "Fun graphic tees for kids aged 4-12.",
                "29.00", "39.00", "CLO-KGT-3PK", 300, seller2, kids,
                List.of("kids", "t-shirt", "pack"), 4.4, 65));

        // Books
        products.add(saveProduct("Python Programming: From Zero to Hero", "Comprehensive Python guide for beginners.",
                "49.00", "59.00", "BK-PY-001", 500, seller1, books,
                List.of("python", "programming", "beginner"), 4.7, 410));
        products.add(saveProduct("Clean Code by Robert Martin", "A handbook of agile software craftsmanship.",
                "39.00", "49.00", "BK-CC-001", 300, seller1, books,
                List.of("clean-code", "software", "agile"), 4.8, 780));
        products.add(saveProduct("The Pragmatic Programmer", "Your journey to mastery in software development.",
                "44.00", "54.00", "BK-PP-001", 250, seller2, books,
                List.of("pragmatic", "software", "programming"), 4.7, 560));
        products.add(saveProduct("Designing Data-Intensive Applications", "Deep dive into distributed systems and databases.",
                "54.00", "64.00", "BK-DDIA-001", 180, seller2, books,
                List.of("databases", "distributed", "systems"), 4.9, 920));
        products.add(saveProduct("The Art of War", "Sun Tzu's ancient text on strategy.",
                "12.00", null, "BK-AOW-001", 1000, seller1, books,
                List.of("strategy", "classic", "philosophy"), 4.5, 300));

        // Home & Garden
        products.add(saveProduct("Instant Pot Duo 7-in-1", "Multi-use pressure cooker, slow cooker, rice cooker and more.",
                "89.00", "119.00", "HG-IPD-001", 70, seller2, homeGarden,
                List.of("kitchen", "pressure-cooker", "instant-pot"), 4.7, 1200));
        products.add(saveProduct("Philips Hue Starter Kit", "Smart LED bulbs with hub for color control.",
                "149.00", "199.00", "HG-PHU-001", 45, seller1, homeGarden,
                List.of("smart-home", "led", "lighting"), 4.5, 340));
        products.add(saveProduct("Robot Vacuum Cleaner", "Auto-mapping robot vacuum with Wi-Fi control.",
                "299.00", "399.00", "HG-RVC-001", 30, seller1, homeGarden,
                List.of("robot", "vacuum", "smart-home"), 4.4, 210));
        products.add(saveProduct("Garden Tool Set 5-Piece", "Durable stainless steel garden tools with ergonomic handles.",
                "45.00", "59.00", "HG-GTS-001", 150, seller2, homeGarden,
                List.of("garden", "tools", "outdoor"), 4.3, 88));
        products.add(saveProduct("Ceramic Plant Pot Set", "Modern ceramic pots with drainage holes, set of 3.",
                "35.00", "45.00", "HG-CPP-001", 200, seller2, homeGarden,
                List.of("plants", "pots", "decor"), 4.2, 65));

        // Out of stock product for edge case testing
        products.add(saveProduct("Limited Edition Gaming Chair", "Ergonomic gaming chair — currently sold out.",
                "449.00", "549.00", "CLO-GCH-001", 0, seller1, accessories,
                List.of("gaming", "chair", "ergonomic"), 4.6, 42));

        em.flush();
        log.info("Seeded {} products.", products.size());
        return products;
    }

    private Product saveProduct(String name, String description, String price, String compareAtPrice,
                                 String sku, int stock, User seller, Category category,
                                 List<String> tags, double avgRating, int reviewCount) {
        Product p = Product.builder()
                .name(name)
                .description(description)
                .price(new BigDecimal(price))
                .compareAtPrice(compareAtPrice != null ? new BigDecimal(compareAtPrice) : null)
                .sku(sku)
                .stock(stock)
                .seller(seller)
                .category(category)
                .tags(new ArrayList<>(tags))
                .averageRating(avgRating)
                .reviewCount(reviewCount)
                .isActive(true)
                .build();
        em.persist(p);
        return p;
    }

    private Category findCat(List<Category> categories, String slug) {
        return categories.stream()
                .filter(c -> slug.equals(c.getSlug()))
                .findFirst()
                .orElseThrow(() -> new IllegalStateException("Category not found: " + slug));
    }

    // -------------------------------------------------------------------------
    // Addresses
    // -------------------------------------------------------------------------
    private List<Address> seedAddresses(List<User> users) {
        log.info("Seeding addresses...");
        List<Address> addresses = new ArrayList<>();

        User customer1 = users.get(3);
        User customer2 = users.get(4);

        addresses.add(saveAddress(customer1, AddressLabel.HOME, "Charlie Brown",
                "123 Main St", null, "Austin", "TX", "78701", "USA", "555-201-0001", true));
        addresses.add(saveAddress(customer1, AddressLabel.WORK, "Charlie Brown",
                "456 Office Blvd", "Suite 200", "Austin", "TX", "78702", "USA", "555-201-0002", false));
        addresses.add(saveAddress(customer2, AddressLabel.HOME, "Diana Davis",
                "789 Oak Ave", null, "Seattle", "WA", "98101", "USA", "555-202-0001", true));
        addresses.add(saveAddress(customer2, AddressLabel.OTHER, "Diana Davis",
                "321 Pine Rd", "Apt 5B", "Seattle", "WA", "98102", "USA", "555-202-0002", false));
        addresses.add(saveAddress(users.get(5), AddressLabel.HOME, "Eve Wilson",
                "101 Elm Street", null, "Denver", "CO", "80201", "USA", "555-203-0001", true));

        em.flush();
        log.info("Seeded {} addresses.", addresses.size());
        return addresses;
    }

    private Address saveAddress(User user, AddressLabel label, String fullName,
                                 String street, String street2, String city, String state,
                                 String zip, String country, String phone, boolean isDefault) {
        Address a = Address.builder()
                .user(user)
                .label(label)
                .fullName(fullName)
                .streetAddress(street)
                .streetAddress2(street2)
                .city(city)
                .state(state)
                .zipCode(zip)
                .country(country)
                .phone(phone)
                .isDefault(isDefault)
                .build();
        em.persist(a);
        return a;
    }

    // -------------------------------------------------------------------------
    // Orders
    // -------------------------------------------------------------------------
    private List<Order> seedOrders(List<User> users, List<Product> products, List<Address> addresses) {
        log.info("Seeding orders...");
        List<Order> orders = new ArrayList<>();

        User customer1 = users.get(3);
        User customer2 = users.get(4);
        User customer3 = users.get(5);
        User customer4 = users.get(6);
        User customer5 = users.get(7);

        Address addr1 = addresses.get(0); // customer1 home
        Address addr3 = addresses.get(2); // customer2 home

        // Order 1 — customer1, DELIVERED
        Order o1 = buildOrder(customer1, addr1, addr1, OrderStatus.DELIVERED,
                PaymentMethod.CREDIT_CARD, PaymentStatus.COMPLETED,
                "TRK-001-2024", null, "ORD-" + System.currentTimeMillis() + "-001");
        em.persist(o1);
        addOrderItem(o1, products.get(0), 1, "999.00"); // iPhone 15 Pro
        addOrderItem(o1, products.get(8), 1, "249.00"); // AirPods Pro
        finalizeOrder(o1, "1248.00", "9.99", "125.00", "0.00", "1382.99");
        orders.add(o1);

        // Order 2 — customer1, SHIPPED
        Order o2 = buildOrder(customer1, addr1, addr1, OrderStatus.SHIPPED,
                PaymentMethod.PAYPAL, PaymentStatus.COMPLETED,
                "TRK-002-2024", null, "ORD-" + (System.currentTimeMillis() + 1) + "-002");
        em.persist(o2);
        addOrderItem(o2, products.get(4), 1, "1299.00"); // MacBook Air
        finalizeOrder(o2, "1299.00", "0.00", "129.90", "0.00", "1428.90");
        orders.add(o2);

        // Order 3 — customer2, PENDING
        Order o3 = buildOrder(customer2, addr3, addr3, OrderStatus.PENDING,
                PaymentMethod.CREDIT_CARD, PaymentStatus.PENDING,
                null, null, "ORD-" + (System.currentTimeMillis() + 2) + "-003");
        em.persist(o3);
        addOrderItem(o3, products.get(9), 1, "349.00"); // Sony headphones
        addOrderItem(o3, products.get(10), 1, "99.00"); // Logitech mouse
        finalizeOrder(o3, "448.00", "5.99", "44.80", "0.00", "498.79");
        orders.add(o3);

        // Order 4 — customer2, CANCELLED
        Order o4 = buildOrder(customer2, addr3, addr3, OrderStatus.CANCELLED,
                PaymentMethod.DEBIT_CARD, PaymentStatus.REFUNDED,
                null, "Changed my mind", "ORD-" + (System.currentTimeMillis() + 3) + "-004");
        em.persist(o4);
        addOrderItem(o4, products.get(19), 1, "49.00"); // Python book
        finalizeOrder(o4, "49.00", "3.99", "4.90", "0.00", "57.89");
        orders.add(o4);

        // Order 5 — customer3, DELIVERED with coupon
        Order o5 = buildOrder(customer3, addresses.get(4), addresses.get(4), OrderStatus.DELIVERED,
                PaymentMethod.CREDIT_CARD, PaymentStatus.COMPLETED,
                "TRK-005-2024", null, "ORD-" + (System.currentTimeMillis() + 4) + "-005");
        o5.setCouponCode("SAVE10");
        em.persist(o5);
        addOrderItem(o5, products.get(24), 1, "89.00"); // Instant Pot
        addOrderItem(o5, products.get(27), 1, "45.00"); // Garden Tool Set
        finalizeOrder(o5, "134.00", "7.99", "13.40", "13.40", "141.99");
        orders.add(o5);

        // Order 6 — customer4, SHIPPED
        Order o6 = buildOrder(customer4, addr1, addr1, OrderStatus.SHIPPED,
                PaymentMethod.PAYPAL, PaymentStatus.COMPLETED,
                "TRK-006-2024", null, "ORD-" + (System.currentTimeMillis() + 5) + "-006");
        em.persist(o6);
        addOrderItem(o6, products.get(13), 2, "49.00"); // Polo Shirt x2
        addOrderItem(o6, products.get(14), 1, "69.00"); // Chinos
        finalizeOrder(o6, "167.00", "9.99", "16.70", "0.00", "193.69");
        orders.add(o6);

        // Order 7 — customer5, PENDING
        Order o7 = buildOrder(customer5, addr3, addr3, OrderStatus.PENDING,
                PaymentMethod.CREDIT_CARD, PaymentStatus.PENDING,
                null, null, "ORD-" + (System.currentTimeMillis() + 6) + "-007");
        em.persist(o7);
        addOrderItem(o7, products.get(20), 1, "39.00"); // Clean Code
        addOrderItem(o7, products.get(21), 1, "44.00"); // Pragmatic Programmer
        finalizeOrder(o7, "83.00", "0.00", "8.30", "0.00", "91.30");
        orders.add(o7);

        // Order 8 — customer1, DELIVERED (older order)
        Order o8 = buildOrder(customer1, addr1, addr1, OrderStatus.DELIVERED,
                PaymentMethod.CREDIT_CARD, PaymentStatus.COMPLETED,
                "TRK-008-2023", null, "ORD-" + (System.currentTimeMillis() + 7) + "-008");
        em.persist(o8);
        addOrderItem(o8, products.get(15), 1, "59.00"); // Yoga Leggings
        addOrderItem(o8, products.get(16), 1, "79.00"); // Sundress
        finalizeOrder(o8, "138.00", "5.99", "13.80", "20.00", "137.79");
        orders.add(o8);

        // Order 9 — customer3, SHIPPED
        Order o9 = buildOrder(customer3, addresses.get(4), addresses.get(4), OrderStatus.SHIPPED,
                PaymentMethod.PAYPAL, PaymentStatus.COMPLETED,
                "TRK-009-2024", null, "ORD-" + (System.currentTimeMillis() + 8) + "-009");
        em.persist(o9);
        addOrderItem(o9, products.get(25), 1, "149.00"); // Philips Hue
        finalizeOrder(o9, "149.00", "0.00", "14.90", "0.00", "163.90");
        orders.add(o9);

        // Order 10 — customer2, DELIVERED
        Order o10 = buildOrder(customer2, addr3, addr3, OrderStatus.DELIVERED,
                PaymentMethod.CREDIT_CARD, PaymentStatus.COMPLETED,
                "TRK-010-2024", null, "ORD-" + (System.currentTimeMillis() + 9) + "-010");
        em.persist(o10);
        addOrderItem(o10, products.get(1), 1, "1199.00"); // Galaxy S24
        finalizeOrder(o10, "1199.00", "0.00", "119.90", "0.00", "1318.90");
        orders.add(o10);

        em.flush();
        log.info("Seeded {} orders.", orders.size());
        return orders;
    }

    private Order buildOrder(User user, Address shipping, Address billing,
                              OrderStatus status, PaymentMethod payMethod,
                              PaymentStatus payStatus, String tracking,
                              String notes, String orderNumber) {
        return Order.builder()
                .user(user)
                .shippingAddress(shipping)
                .billingAddress(billing)
                .status(status)
                .paymentMethod(payMethod)
                .paymentStatus(payStatus)
                .trackingNumber(tracking)
                .notes(notes)
                .orderNumber(orderNumber)
                .build();
    }

    private void addOrderItem(Order order, Product product, int qty, String unitPrice) {
        BigDecimal unit = new BigDecimal(unitPrice);
        OrderItem item = OrderItem.builder()
                .order(order)
                .product(product)
                .productName(product.getName())
                .productSku(product.getSku())
                .quantity(qty)
                .unitPrice(unit)
                .totalPrice(unit.multiply(BigDecimal.valueOf(qty)))
                .discount(BigDecimal.ZERO)
                .build();
        order.getItems().add(item);
        em.persist(item);
    }

    private void finalizeOrder(Order order, String subtotal, String shipping,
                                String tax, String discount, String total) {
        order.setSubtotal(new BigDecimal(subtotal));
        order.setShippingCost(new BigDecimal(shipping));
        order.setTaxAmount(new BigDecimal(tax));
        order.setDiscountAmount(new BigDecimal(discount));
        order.setTotalAmount(new BigDecimal(total));
    }

    // -------------------------------------------------------------------------
    // Reviews
    // -------------------------------------------------------------------------
    private void seedReviews(List<User> users, List<Product> products) {
        log.info("Seeding reviews...");

        User c1 = users.get(3);
        User c2 = users.get(4);
        User c3 = users.get(5);
        User c4 = users.get(6);
        User c5 = users.get(7);

        saveReview(c1, products.get(0), 5, "Amazing phone!", "Best iPhone I've ever owned. The titanium frame feels premium.", true);
        saveReview(c2, products.get(0), 4, "Great but pricey", "Excellent performance and camera, just a bit expensive.", false);
        saveReview(c3, products.get(0), 3, "Underwhelmed", "Expected more for the price. Still a good phone though.", false);

        saveReview(c1, products.get(4), 5, "Perfect laptop", "The M3 chip is ridiculously fast. Battery lasts all day easily.", true);
        saveReview(c4, products.get(4), 5, "MacBook believer now", "Switched from Windows and never looking back.", false);

        saveReview(c2, products.get(9), 5, "Best headphones ever", "The noise cancellation is unbelievable. Worth every penny.", true);
        saveReview(c5, products.get(9), 4, "Great sound quality", "Very comfortable for long sessions. The ANC is impressive.", false);
        saveReview(c1, products.get(9), 2, "Disappointed with build", "Sound is great but the plastic feels cheap for $350.", true);

        saveReview(c3, products.get(8), 5, "AirPods Pro are superb", "Best earbuds for iPhone users. Seamless switching.", true);
        saveReview(c4, products.get(8), 4, "Solid noise cancellation", "Great for commuting. Transparency mode is natural.", false);

        saveReview(c1, products.get(19), 5, "Excellent Python book", "Covers everything from basics to advanced topics clearly.", false);
        saveReview(c2, products.get(20), 5, "A must-read", "Every developer should read Clean Code. Changed how I write code.", false);
        saveReview(c3, products.get(21), 5, "Life-changing", "The Pragmatic Programmer is as relevant today as ever.", false);

        saveReview(c5, products.get(24), 4, "Love my Instant Pot", "Makes cooking so much easier. The rice and yogurt functions are great.", true);
        saveReview(c2, products.get(13), 1, "Wrong size delivered", "Ordered a Large but received Small. Very frustrating.", true);

        em.flush();
        log.info("Seeded 15 reviews.");
    }

    private void saveReview(User user, Product product, int rating, String title, String comment, boolean verified) {
        Review r = Review.builder()
                .user(user)
                .product(product)
                .rating(rating)
                .title(title)
                .comment(comment)
                .isVerifiedPurchase(verified)
                .helpfulCount((int) (Math.random() * 50))
                .reportCount(0)
                .status(ReviewStatus.APPROVED)
                .build();
        em.persist(r);
    }

    // -------------------------------------------------------------------------
    // Coupons
    // -------------------------------------------------------------------------
    private void seedCoupons() {
        log.info("Seeding coupons...");

        LocalDateTime now = LocalDateTime.now();

        saveCoupon("SAVE10", "10% off your order", DiscountType.PERCENTAGE,
                "10.00", "50.00", null, null, now.minusDays(30), now.plusDays(365), true);

        saveCoupon("FLAT20", "Flat $20 off orders over $100", DiscountType.FIXED,
                "20.00", "100.00", null, null, now.minusDays(30), now.plusDays(365), true);

        saveCoupon("WELCOME", "15% off your first order", DiscountType.PERCENTAGE,
                "15.00", "0.00", "50.00", null, now.minusDays(1), now.plusDays(180), true);

        // Expired coupon — intentional for edge case testing
        saveCoupon("SUMMER50", "50% off summer sale (expired)", DiscountType.PERCENTAGE,
                "50.00", "0.00", "200.00", null, now.minusDays(180), now.minusDays(1), true);

        // One-time use coupon
        saveCoupon("FREEBIE", "100% off — one use only, up to $50", DiscountType.PERCENTAGE,
                "100.00", "0.00", "50.00", 1, now.minusDays(10), now.plusDays(90), true);

        em.flush();
        log.info("Seeded 5 coupons.");
    }

    private void saveCoupon(String code, String description, DiscountType type,
                             String value, String minOrder, String maxDiscount,
                             Integer usageLimit, LocalDateTime validFrom,
                             LocalDateTime validUntil, boolean active) {
        Coupon c = Coupon.builder()
                .code(code)
                .description(description)
                .discountType(type)
                .discountValue(new BigDecimal(value))
                .minimumOrderAmount(minOrder != null ? new BigDecimal(minOrder) : null)
                .maximumDiscount(maxDiscount != null ? new BigDecimal(maxDiscount) : null)
                .usageLimit(usageLimit)
                .usageCount(0)
                .validFrom(validFrom)
                .validUntil(validUntil)
                .isActive(active)
                .build();
        em.persist(c);
    }

    // -------------------------------------------------------------------------
    // Carts
    // -------------------------------------------------------------------------
    private void seedCarts(List<User> users, List<Product> products) {
        log.info("Seeding carts...");

        User c1 = users.get(3);
        User c2 = users.get(4);
        User c3 = users.get(5);

        Cart cart1 = Cart.builder().user(c1).build();
        em.persist(cart1);
        addCartItem(cart1, products.get(2), 1); // Pixel 8
        addCartItem(cart1, products.get(11), 2); // Anker charger x2

        Cart cart2 = Cart.builder().user(c2).build();
        em.persist(cart2);
        addCartItem(cart2, products.get(22), 1); // DDIA book
        addCartItem(cart2, products.get(23), 1); // Art of War

        Cart cart3 = Cart.builder().user(c3).build();
        em.persist(cart3);
        addCartItem(cart3, products.get(26), 1); // Robot Vacuum
        addCartItem(cart3, products.get(28), 1); // Ceramic Pots

        em.flush();
        log.info("Seeded 3 carts.");
    }

    private void addCartItem(Cart cart, Product product, int quantity) {
        CartItem item = CartItem.builder()
                .cart(cart)
                .product(product)
                .quantity(quantity)
                .priceAtAdd(product.getPrice())
                .build();
        cart.getItems().add(item);
        em.persist(item);
    }

    // -------------------------------------------------------------------------
    // Notifications
    // -------------------------------------------------------------------------
    private void seedNotifications(List<User> users, List<Order> orders) {
        log.info("Seeding notifications...");

        User c1 = users.get(3);
        User c2 = users.get(4);
        User c3 = users.get(5);
        User c4 = users.get(6);
        User c5 = users.get(7);

        // Order status notifications
        saveNotification(c1, "Order Delivered!", "Your order #" + orders.get(0).getOrderNumber() + " has been delivered.", NotificationType.ORDER_STATUS, "/orders/" + orders.get(0).getId(), true);
        saveNotification(c1, "Order Shipped", "Your order #" + orders.get(1).getOrderNumber() + " is on its way!", NotificationType.ORDER_STATUS, "/orders/" + orders.get(1).getId(), false);
        saveNotification(c2, "Order Confirmed", "Your order #" + orders.get(2).getOrderNumber() + " has been confirmed.", NotificationType.ORDER_STATUS, "/orders/" + orders.get(2).getId(), false);
        saveNotification(c2, "Order Cancelled", "Your order #" + orders.get(3).getOrderNumber() + " has been cancelled.", NotificationType.ORDER_STATUS, "/orders/" + orders.get(3).getId(), true);
        saveNotification(c3, "Order Delivered!", "Your order #" + orders.get(4).getOrderNumber() + " has been delivered.", NotificationType.ORDER_STATUS, "/orders/" + orders.get(4).getId(), true);
        saveNotification(c3, "Order Shipped", "Your order #" + orders.get(8).getOrderNumber() + " is on its way!", NotificationType.ORDER_STATUS, "/orders/" + orders.get(8).getId(), false);

        // Promotional notifications
        saveNotification(c1, "Flash Sale — 24 Hours Only!", "Up to 40% off on Electronics. Use code FLASH40 at checkout.", NotificationType.PROMOTION, "/products?category=electronics", false);
        saveNotification(c2, "New Arrivals in Clothing", "Check out our latest summer collection just in.", NotificationType.PROMOTION, "/products?category=clothing", false);
        saveNotification(c4, "Exclusive Member Offer", "You qualify for 20% off your next order. Use MEMBER20.", NotificationType.PROMOTION, "/products", false);

        // System notifications
        saveNotification(c5, "Welcome to VulnShop!", "Thanks for joining. Browse thousands of products and enjoy free shipping on your first order.", NotificationType.SYSTEM, "/products", true);
        saveNotification(c3, "Review Your Recent Purchase", "How was your Instant Pot? Share your experience.", NotificationType.REVIEW, "/reviews/new?product=25", false);

        em.flush();
        log.info("Seeded 11 notifications.");
    }

    private void saveNotification(User user, String title, String message,
                                   NotificationType type, String link, boolean isRead) {
        Notification n = Notification.builder()
                .user(user)
                .title(title)
                .message(message)
                .type(type)
                .link(link)
                .isRead(isRead)
                .build();
        em.persist(n);
    }
}
