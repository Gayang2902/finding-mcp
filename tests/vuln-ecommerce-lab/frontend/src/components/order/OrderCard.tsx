import { Link } from 'react-router-dom'
import { format } from 'date-fns'
import { Package, Truck } from 'lucide-react'
import { Order } from '../../types'
import StatusBadge from '../common/StatusBadge'
import Button from '../common/Button'

interface OrderCardProps {
  order: Order
}

export default function OrderCard({ order }: OrderCardProps) {
  const firstItem = order.items[0]
  const extraCount = order.items.length - 1

  return (
    <div className="rounded-xl border border-gray-100 bg-white p-5 shadow-sm hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
        <div>
          <p className="text-xs text-gray-400 mb-0.5">Order</p>
          <p className="text-sm font-bold text-gray-900">#{order.orderNumber}</p>
          <p className="text-xs text-gray-500 mt-0.5">
            {format(new Date(order.createdAt), 'MMM d, yyyy')}
          </p>
        </div>
        <StatusBadge status={order.status} />
      </div>

      {/* Items preview */}
      <div className="flex items-center gap-3 mb-4">
        {firstItem?.productImageUrl ? (
          <img
            src={firstItem.productImageUrl}
            alt={firstItem.productName}
            className="h-14 w-14 rounded-lg object-cover flex-shrink-0 bg-gray-100"
          />
        ) : (
          <div className="h-14 w-14 rounded-lg bg-gray-100 flex items-center justify-center text-gray-300 flex-shrink-0">
            <Package className="h-6 w-6" />
          </div>
        )}
        <div className="min-w-0">
          <p className="text-sm font-medium text-gray-800 line-clamp-1">{firstItem?.productName}</p>
          {extraCount > 0 && (
            <p className="text-xs text-gray-500 mt-0.5">+{extraCount} more item{extraCount !== 1 ? 's' : ''}</p>
          )}
          <p className="text-xs text-gray-500 mt-0.5">
            {order.items.reduce((sum, i) => sum + i.quantity, 0)} item{order.items.length !== 1 ? 's' : ''}
          </p>
        </div>
        <div className="ml-auto text-right flex-shrink-0">
          <p className="text-sm font-bold text-gray-900">${order.total.toFixed(2)}</p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2 pt-3 border-t border-gray-100">
        <Button variant="outline" size="sm" fullWidth>
          <Link to={`/orders/${order.id}`} className="w-full text-center">
            View Details
          </Link>
        </Button>
        {order.shippingInfo?.trackingNumber && (
          <Button variant="secondary" size="sm" fullWidth iconLeft={<Truck className="h-3.5 w-3.5" />}>
            <Link to={`/orders/${order.id}/tracking`} className="w-full text-center">
              Track Order
            </Link>
          </Button>
        )}
      </div>
    </div>
  )
}
