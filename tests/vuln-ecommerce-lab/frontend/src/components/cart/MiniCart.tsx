import { Link } from 'react-router-dom'
import { ShoppingBag } from 'lucide-react'
import { Cart } from '../../types'
import Button from '../common/Button'

interface MiniCartProps {
  cart?: Cart | null
  onClose?: () => void
}

export default function MiniCart({ cart, onClose }: MiniCartProps) {
  const previewItems = cart?.items.slice(0, 3) ?? []
  const isEmpty = !cart || cart.items.length === 0

  return (
    <div className="w-80 bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-100">
        <h3 className="text-sm font-semibold text-gray-900">
          Cart {cart && cart.itemCount > 0 && `(${cart.itemCount})`}
        </h3>
      </div>

      {isEmpty ? (
        <div className="flex flex-col items-center justify-center py-10 px-4 text-center">
          <ShoppingBag className="h-10 w-10 text-gray-300 mb-3" />
          <p className="text-sm text-gray-500">Your cart is empty</p>
          <Link
            to="/products"
            className="mt-3 text-sm text-indigo-600 hover:text-indigo-700 font-medium transition-colors"
            onClick={onClose}
          >
            Start shopping
          </Link>
        </div>
      ) : (
        <>
          <div className="divide-y divide-gray-50">
            {previewItems.map((item) => (
              <div key={item.id} className="flex gap-3 px-4 py-3">
                <div className="h-12 w-12 flex-shrink-0 rounded-lg overflow-hidden bg-gray-100">
                  {item.product.imageUrl ? (
                    <img
                      src={item.product.imageUrl}
                      alt={item.product.name}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <div className="h-full w-full flex items-center justify-center text-gray-300">
                      <ShoppingBag className="h-5 w-5" />
                    </div>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-gray-800 line-clamp-1">{item.product.name}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {item.quantity} × ${item.price.toFixed(2)}
                  </p>
                </div>
                <p className="text-xs font-semibold text-gray-900 flex-shrink-0">
                  ${(item.quantity * item.price).toFixed(2)}
                </p>
              </div>
            ))}

            {cart && cart.items.length > 3 && (
              <p className="px-4 py-2 text-xs text-gray-400 text-center">
                +{cart.items.length - 3} more item{cart.items.length - 3 !== 1 ? 's' : ''}
              </p>
            )}
          </div>

          <div className="px-4 py-3 border-t border-gray-100 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Total</span>
              <span className="font-semibold text-gray-900">${cart?.total.toFixed(2)}</span>
            </div>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="sm"
                fullWidth
                onClick={onClose}
                // @ts-ignore — rendered as Link via asChild pattern not available; use wrapper
              >
                <Link to="/cart" className="w-full text-center" onClick={onClose}>
                  View Cart
                </Link>
              </Button>
              <Button size="sm" fullWidth onClick={onClose}>
                <Link to="/checkout" className="w-full text-center text-white" onClick={onClose}>
                  Checkout
                </Link>
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
