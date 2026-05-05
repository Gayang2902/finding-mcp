import { Link } from 'react-router-dom'
import { Trash2, Minus, Plus, AlertTriangle } from 'lucide-react'
import { CartItem } from '../../types'
import PriceDisplay from '../common/PriceDisplay'

interface CartItemRowProps {
  item: CartItem
  onQuantityChange: (itemId: number, quantity: number) => void
  onRemove: (itemId: number) => void
}

export default function CartItemRow({ item, onQuantityChange, onRemove }: CartItemRowProps) {
  const subtotal = item.price * item.quantity
  const isOverStock = item.quantity > item.product.stock

  return (
    <div className="flex gap-4 py-4 border-b border-gray-100 last:border-0">
      {/* Thumbnail */}
      <Link to={`/products/${item.productId}`} className="flex-shrink-0">
        <div className="h-20 w-20 rounded-lg overflow-hidden bg-gray-100">
          {item.product.imageUrl ? (
            <img
              src={item.product.imageUrl}
              alt={item.product.name}
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="h-full w-full flex items-center justify-center text-gray-300 text-xs">
              No image
            </div>
          )}
        </div>
      </Link>

      {/* Details */}
      <div className="flex-1 min-w-0">
        <Link
          to={`/products/${item.productId}`}
          className="text-sm font-semibold text-gray-800 hover:text-indigo-600 transition-colors line-clamp-2"
        >
          {item.product.name}
        </Link>

        <PriceDisplay price={item.price} size="sm" className="mt-1" />

        {isOverStock && (
          <div className="flex items-center gap-1 mt-1 text-xs text-amber-600">
            <AlertTriangle className="h-3.5 w-3.5" />
            Only {item.product.stock} left in stock
          </div>
        )}

        {/* Quantity + Remove */}
        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center rounded-lg border border-gray-200 overflow-hidden">
            <button
              onClick={() => onQuantityChange(item.id, Math.max(1, item.quantity - 1))}
              disabled={item.quantity <= 1}
              className="px-2.5 py-1.5 text-gray-600 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              aria-label="Decrease quantity"
            >
              <Minus className="h-3.5 w-3.5" />
            </button>
            <span className="px-3 py-1.5 text-sm font-medium text-gray-800 min-w-[2rem] text-center border-x border-gray-200">
              {item.quantity}
            </span>
            <button
              onClick={() => onQuantityChange(item.id, item.quantity + 1)}
              className="px-2.5 py-1.5 text-gray-600 hover:bg-gray-100 transition-colors"
              aria-label="Increase quantity"
            >
              <Plus className="h-3.5 w-3.5" />
            </button>
          </div>

          <button
            onClick={() => onRemove(item.id)}
            className="p-1.5 text-gray-400 hover:text-red-500 transition-colors"
            aria-label="Remove item"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Subtotal */}
      <div className="text-sm font-semibold text-gray-900 flex-shrink-0 pt-0.5">
        ${subtotal.toFixed(2)}
      </div>
    </div>
  )
}
