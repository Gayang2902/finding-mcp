import { Link } from 'react-router-dom'
import { Package } from 'lucide-react'
import { OrderItem } from '../../types'

interface OrderItemRowProps {
  item: OrderItem
}

export default function OrderItemRow({ item }: OrderItemRowProps) {
  return (
    <div className="flex gap-4 py-3 border-b border-gray-100 last:border-0">
      {/* Image */}
      <div className="h-16 w-16 flex-shrink-0 rounded-lg overflow-hidden bg-gray-100">
        {item.productImageUrl ? (
          <img
            src={item.productImageUrl}
            alt={item.productName}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="h-full w-full flex items-center justify-center text-gray-300">
            <Package className="h-6 w-6" />
          </div>
        )}
      </div>

      {/* Details */}
      <div className="flex-1 min-w-0">
        {item.productId ? (
          <Link
            to={`/products/${item.productId}`}
            className="text-sm font-semibold text-gray-800 hover:text-indigo-600 transition-colors line-clamp-2"
          >
            {item.productName}
          </Link>
        ) : (
          <p className="text-sm font-semibold text-gray-800 line-clamp-2">{item.productName}</p>
        )}
        <p className="text-xs text-gray-400 mt-0.5">
          {item.quantity} &times; ${item.unitPrice.toFixed(2)}
        </p>
      </div>

      {/* Total */}
      <div className="text-sm font-semibold text-gray-900 flex-shrink-0 pt-0.5">
        ${item.totalPrice.toFixed(2)}
      </div>
    </div>
  )
}
