import { OrderStatus, PaymentStatus, ShippingStatus, ReviewStatus } from '@/types'

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount)
}

export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(new Date(date))
}

export function formatDateTime(date: string | Date): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(date))
}

export function formatOrderStatus(status: OrderStatus): { label: string; color: string } {
  const map: Record<OrderStatus, { label: string; color: string }> = {
    [OrderStatus.PENDING]:    { label: 'Pending',    color: 'yellow' },
    [OrderStatus.CONFIRMED]:  { label: 'Confirmed',  color: 'blue' },
    [OrderStatus.PROCESSING]: { label: 'Processing', color: 'blue' },
    [OrderStatus.SHIPPED]:    { label: 'Shipped',    color: 'purple' },
    [OrderStatus.DELIVERED]:  { label: 'Delivered',  color: 'green' },
    [OrderStatus.CANCELLED]:  { label: 'Cancelled',  color: 'red' },
    [OrderStatus.REFUNDED]:   { label: 'Refunded',   color: 'gray' },
  }
  return map[status] ?? { label: status, color: 'gray' }
}

export function formatPaymentStatus(status: PaymentStatus): { label: string; color: string } {
  const map: Record<PaymentStatus, { label: string; color: string }> = {
    [PaymentStatus.PENDING]:   { label: 'Pending',   color: 'yellow' },
    [PaymentStatus.COMPLETED]: { label: 'Completed', color: 'green' },
    [PaymentStatus.FAILED]:    { label: 'Failed',    color: 'red' },
    [PaymentStatus.REFUNDED]:  { label: 'Refunded',  color: 'gray' },
  }
  return map[status] ?? { label: status, color: 'gray' }
}

export function formatShippingStatus(status: ShippingStatus): { label: string; color: string } {
  const map: Record<ShippingStatus, { label: string; color: string }> = {
    [ShippingStatus.PREPARING]:        { label: 'Preparing',        color: 'yellow' },
    [ShippingStatus.SHIPPED]:          { label: 'Shipped',          color: 'blue' },
    [ShippingStatus.IN_TRANSIT]:       { label: 'In Transit',       color: 'blue' },
    [ShippingStatus.OUT_FOR_DELIVERY]: { label: 'Out for Delivery', color: 'purple' },
    [ShippingStatus.DELIVERED]:        { label: 'Delivered',        color: 'green' },
    [ShippingStatus.RETURNED]:         { label: 'Returned',         color: 'red' },
  }
  return map[status] ?? { label: status, color: 'gray' }
}

export function formatReviewStatus(status: ReviewStatus): { label: string; color: string } {
  const map: Record<ReviewStatus, { label: string; color: string }> = {
    [ReviewStatus.PENDING]:  { label: 'Pending',  color: 'yellow' },
    [ReviewStatus.APPROVED]: { label: 'Approved', color: 'green' },
    [ReviewStatus.REJECTED]: { label: 'Rejected', color: 'red' },
  }
  return map[status] ?? { label: status, color: 'gray' }
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength).trimEnd() + '…'
}

export function formatRating(rating: number): string {
  return rating.toFixed(1)
}
