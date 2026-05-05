// Enums
export enum Role {
  USER = 'USER',
  SELLER = 'SELLER',
  ADMIN = 'ADMIN',
}

export enum OrderStatus {
  PENDING = 'PENDING',
  CONFIRMED = 'CONFIRMED',
  PROCESSING = 'PROCESSING',
  SHIPPED = 'SHIPPED',
  DELIVERED = 'DELIVERED',
  CANCELLED = 'CANCELLED',
  REFUNDED = 'REFUNDED',
}

export enum PaymentStatus {
  PENDING = 'PENDING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  REFUNDED = 'REFUNDED',
}

export enum PaymentMethod {
  CREDIT_CARD = 'CREDIT_CARD',
  DEBIT_CARD = 'DEBIT_CARD',
  PAYPAL = 'PAYPAL',
  BANK_TRANSFER = 'BANK_TRANSFER',
}

export enum ShippingStatus {
  PREPARING = 'PREPARING',
  SHIPPED = 'SHIPPED',
  IN_TRANSIT = 'IN_TRANSIT',
  OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY',
  DELIVERED = 'DELIVERED',
  RETURNED = 'RETURNED',
}

export enum ReviewStatus {
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
}

export enum NotificationType {
  ORDER_UPDATE = 'ORDER_UPDATE',
  PAYMENT = 'PAYMENT',
  SHIPPING = 'SHIPPING',
  PROMOTION = 'PROMOTION',
  REVIEW = 'REVIEW',
  SYSTEM = 'SYSTEM',
}

export enum DiscountType {
  PERCENTAGE = 'PERCENTAGE',
  FIXED = 'FIXED',
}

// Core entities
export interface User {
  id: number
  email: string
  firstName: string
  lastName: string
  phone?: string
  role: Role
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export interface Category {
  id: number
  name: string
  slug: string
  description?: string
  imageUrl?: string
  parentId?: number
}

export interface Product {
  id: number
  name: string
  description: string
  price: number
  compareAtPrice?: number
  stock: number
  sku: string
  imageUrl?: string
  images?: string[]
  categoryId: number
  category?: Category
  sellerId: number
  seller?: User
  averageRating: number
  reviewCount: number
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export interface CartItem {
  id: number
  productId: number
  product: Product
  quantity: number
  price: number
}

export interface Cart {
  id: number
  userId: number
  items: CartItem[]
  total: number
  itemCount: number
}

export interface OrderItem {
  id: number
  orderId: number
  productId: number
  product?: Product
  productName: string
  productImageUrl?: string
  quantity: number
  unitPrice: number
  totalPrice: number
}

export interface Address {
  id: number
  userId: number
  label?: string
  recipientName: string
  street: string
  city: string
  state: string
  postalCode: string
  country: string
  phone?: string
  isDefault: boolean
}

export interface ShippingEvent {
  status: string
  description: string
  location?: string
  timestamp: string
}

export interface ShippingInfo {
  id: number
  orderId: number
  carrier: string
  trackingNumber: string
  status: ShippingStatus
  estimatedDelivery?: string
  actualDelivery?: string
  events: ShippingEvent[]
}

export interface Payment {
  id: number
  orderId: number
  amount: number
  method: PaymentMethod
  status: PaymentStatus
  transactionId?: string
  cardLast4?: string
  createdAt: string
}

export interface Order {
  id: number
  orderNumber: string
  userId: number
  user?: User
  items: OrderItem[]
  subtotal: number
  shippingCost: number
  tax: number
  discount: number
  total: number
  status: OrderStatus
  shippingAddress: Address
  billingAddress?: Address
  payment?: Payment
  shippingInfo?: ShippingInfo
  couponCode?: string
  notes?: string
  createdAt: string
  updatedAt: string
}

export interface Review {
  id: number
  productId: number
  product?: Product
  userId: number
  user?: User
  rating: number
  title: string
  body: string
  status: ReviewStatus
  helpfulCount: number
  createdAt: string
  updatedAt: string
}

export interface Coupon {
  id: number
  code: string
  description?: string
  discountType: DiscountType
  discountValue: number
  minOrderAmount?: number
  maxDiscountAmount?: number
  usageLimit?: number
  usageCount: number
  isActive: boolean
  expiresAt?: string
  createdAt: string
}

export interface Notification {
  id: number
  userId: number
  type: NotificationType
  title: string
  message: string
  isRead: boolean
  resourceId?: number
  resourceType?: string
  createdAt: string
}

export interface AuditLog {
  id: number
  userId?: number
  user?: User
  action: string
  resource: string
  resourceId?: number
  details?: string
  ipAddress?: string
  createdAt: string
}

// Request / Response types
export interface AuthResponse {
  token: string
  user: User
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  firstName: string
  lastName: string
  phone?: string
}

export interface ProductSearchParams {
  q?: string
  categoryId?: number
  minPrice?: number
  maxPrice?: number
  sortBy?: string
  sortDir?: 'asc' | 'desc'
  page?: number
  size?: number
}

export interface OrderCreateRequest {
  items: { productId: number; quantity: number }[]
  shippingAddressId: number
  billingAddressId?: number
  paymentMethod: PaymentMethod
  couponCode?: string
  notes?: string
}

export interface CartItemRequest {
  productId: number
  quantity: number
}

export interface ReviewCreateRequest {
  productId: number
  rating: number
  title: string
  body: string
}

export interface AddressRequest {
  label?: string
  recipientName: string
  street: string
  city: string
  state: string
  postalCode: string
  country: string
  phone?: string
  isDefault?: boolean
}

export interface CouponApplyRequest {
  code: string
  orderTotal: number
}

export interface PaymentRequest {
  orderId: number
  method: PaymentMethod
  cardNumber?: string
  cardExpiry?: string
  cardCvv?: string
  cardHolder?: string
}

export interface ProfileUpdateRequest {
  firstName: string
  lastName: string
  phone?: string
}

export interface ChangePasswordRequest {
  currentPassword: string
  newPassword: string
  confirmPassword: string
}

export interface PageResponse<T> {
  content: T[]
  totalElements: number
  totalPages: number
  size: number
  number: number
  first: boolean
  last: boolean
}

export interface ApiError {
  status: number
  error: string
  message: string
  path: string
  timestamp: string
}

export interface DashboardStats {
  totalOrders: number
  totalRevenue: number
  totalProducts: number
  totalCustomers: number
  recentOrders: Order[]
  topProducts: Product[]
}
