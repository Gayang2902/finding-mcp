import { clsx } from 'clsx'
import { OrderStatus, PaymentStatus, ShippingStatus, ReviewStatus } from '../../types'

type StatusType = OrderStatus | PaymentStatus | ShippingStatus

interface StatusConfig {
  label: string
  classes: string
  active?: boolean
}

// Build config without object-literal duplicate keys by using a Map-style approach.
// Some enum string values overlap (e.g. PENDING, SHIPPED, DELIVERED, REFUNDED),
// so we populate via explicit assignment instead of computed-property object literals.
const statusConfig = new Map<string, StatusConfig>()

// Order statuses
statusConfig.set(OrderStatus.PENDING,    { label: 'Pending',    classes: 'bg-yellow-100 text-yellow-700', active: true })
statusConfig.set(OrderStatus.CONFIRMED,  { label: 'Confirmed',  classes: 'bg-blue-100 text-blue-700' })
statusConfig.set(OrderStatus.PROCESSING, { label: 'Processing', classes: 'bg-indigo-100 text-indigo-700', active: true })
statusConfig.set(OrderStatus.SHIPPED,    { label: 'Shipped',    classes: 'bg-purple-100 text-purple-700' })
statusConfig.set(OrderStatus.DELIVERED,  { label: 'Delivered',  classes: 'bg-green-100 text-green-700' })
statusConfig.set(OrderStatus.CANCELLED,  { label: 'Cancelled',  classes: 'bg-gray-100 text-gray-600' })
statusConfig.set(OrderStatus.REFUNDED,   { label: 'Refunded',   classes: 'bg-orange-100 text-orange-700' })

// Payment statuses (PENDING / REFUNDED overlap with OrderStatus — same config is fine)
statusConfig.set(PaymentStatus.COMPLETED, { label: 'Paid',    classes: 'bg-green-100 text-green-700' })
statusConfig.set(PaymentStatus.FAILED,    { label: 'Failed',  classes: 'bg-red-100 text-red-700' })

// Shipping statuses (SHIPPED / DELIVERED overlap — same config is fine)
statusConfig.set(ShippingStatus.PREPARING,        { label: 'Preparing',        classes: 'bg-gray-100 text-gray-600' })
statusConfig.set(ShippingStatus.IN_TRANSIT,       { label: 'In Transit',       classes: 'bg-blue-100 text-blue-700', active: true })
statusConfig.set(ShippingStatus.OUT_FOR_DELIVERY, { label: 'Out for Delivery', classes: 'bg-indigo-100 text-indigo-700', active: true })
statusConfig.set(ShippingStatus.RETURNED,         { label: 'Returned',         classes: 'bg-orange-100 text-orange-700' })

interface StatusBadgeProps {
  status: StatusType
  pulse?: boolean
  className?: string
}

export default function StatusBadge({ status, pulse, className }: StatusBadgeProps) {
  const config = statusConfig.get(status) ?? { label: status, classes: 'bg-gray-100 text-gray-600' }
  const shouldPulse = pulse ?? config.active

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium',
        config.classes,
        className
      )}
    >
      {shouldPulse && (
        <span className="relative flex h-1.5 w-1.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 bg-current" />
          <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-current" />
        </span>
      )}
      {config.label}
    </span>
  )
}

// Named exports for backward compatibility
function InlineBadge({ color, label }: { color: string; label: string }) {
  const colorMap: Record<string, string> = {
    green:  'bg-green-100 text-green-800',
    yellow: 'bg-yellow-100 text-yellow-800',
    red:    'bg-red-100 text-red-800',
    blue:   'bg-blue-100 text-blue-800',
    purple: 'bg-purple-100 text-purple-800',
    gray:   'bg-gray-100 text-gray-800',
  }
  return (
    <span className={clsx('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium', colorMap[color] ?? colorMap['gray'])}>
      {label}
    </span>
  )
}

export function OrderStatusBadge({ status }: { status: OrderStatus }) {
  const map: Record<OrderStatus, { label: string; color: string }> = {
    [OrderStatus.PENDING]:    { label: 'Pending',    color: 'yellow' },
    [OrderStatus.CONFIRMED]:  { label: 'Confirmed',  color: 'blue' },
    [OrderStatus.PROCESSING]: { label: 'Processing', color: 'purple' },
    [OrderStatus.SHIPPED]:    { label: 'Shipped',    color: 'blue' },
    [OrderStatus.DELIVERED]:  { label: 'Delivered',  color: 'green' },
    [OrderStatus.CANCELLED]:  { label: 'Cancelled',  color: 'gray' },
    [OrderStatus.REFUNDED]:   { label: 'Refunded',   color: 'red' },
  }
  const { label, color } = map[status] ?? { label: status, color: 'gray' }
  return <InlineBadge label={label} color={color} />
}

export function PaymentStatusBadge({ status }: { status: PaymentStatus }) {
  const map: Record<PaymentStatus, { label: string; color: string }> = {
    [PaymentStatus.PENDING]:   { label: 'Pending',  color: 'yellow' },
    [PaymentStatus.COMPLETED]: { label: 'Paid',     color: 'green' },
    [PaymentStatus.FAILED]:    { label: 'Failed',   color: 'red' },
    [PaymentStatus.REFUNDED]:  { label: 'Refunded', color: 'purple' },
  }
  const { label, color } = map[status] ?? { label: status, color: 'gray' }
  return <InlineBadge label={label} color={color} />
}

export function ReviewStatusBadge({ status }: { status: ReviewStatus }) {
  const map: Record<ReviewStatus, { label: string; color: string }> = {
    [ReviewStatus.PENDING]:  { label: 'Pending',  color: 'yellow' },
    [ReviewStatus.APPROVED]: { label: 'Approved', color: 'green' },
    [ReviewStatus.REJECTED]: { label: 'Rejected', color: 'red' },
  }
  const { label, color } = map[status] ?? { label: status, color: 'gray' }
  return <InlineBadge label={label} color={color} />
}
