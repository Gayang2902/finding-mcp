import { Link } from 'react-router-dom'
import { format } from 'date-fns'
import { Eye } from 'lucide-react'
import { Order, OrderStatus } from '../../types'
import { OrderStatusBadge, PaymentStatusBadge } from '../common/StatusBadge'
import Button from '../common/Button'

interface AdminOrderRowProps {
  order: Order
  onStatusChange?: (orderId: number, status: OrderStatus) => void
}

const ORDER_STATUS_OPTIONS = Object.values(OrderStatus)

export default function AdminOrderRow({ order, onStatusChange }: AdminOrderRowProps) {
  return (
    <tr className="hover:bg-gray-50 transition-colors">
      {/* Order # */}
      <td className="px-4 py-3">
        <span className="text-sm font-mono font-semibold text-indigo-600">#{order.orderNumber}</span>
        <p className="text-xs text-gray-400 mt-0.5">{format(new Date(order.createdAt), 'MMM d, yyyy')}</p>
      </td>

      {/* Customer */}
      <td className="px-4 py-3">
        {order.user ? (
          <div>
            <p className="text-sm font-medium text-gray-800">
              {order.user.firstName} {order.user.lastName}
            </p>
            <p className="text-xs text-gray-400 truncate max-w-[160px]">{order.user.email}</p>
          </div>
        ) : (
          <span className="text-sm text-gray-400">—</span>
        )}
      </td>

      {/* Items / Total */}
      <td className="px-4 py-3">
        <p className="text-sm text-gray-700">{order.items.length} item{order.items.length !== 1 ? 's' : ''}</p>
        <p className="text-sm font-semibold text-gray-900">${order.total.toFixed(2)}</p>
      </td>

      {/* Order status */}
      <td className="px-4 py-3">
        <select
          value={order.status}
          onChange={(e) => onStatusChange?.(order.id, e.target.value as OrderStatus)}
          className="rounded-lg border border-gray-200 px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
          onClick={(e) => e.stopPropagation()}
        >
          {ORDER_STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </td>

      {/* Payment status */}
      <td className="px-4 py-3">
        {order.payment ? (
          <PaymentStatusBadge status={order.payment.status} />
        ) : (
          <span className="text-xs text-gray-400">—</span>
        )}
      </td>

      {/* Actions */}
      <td className="px-4 py-3">
        <Button variant="ghost" size="sm" iconLeft={<Eye className="h-3.5 w-3.5" />}>
          <Link to={`/admin/orders/${order.id}`}>View</Link>
        </Button>
      </td>
    </tr>
  )
}
