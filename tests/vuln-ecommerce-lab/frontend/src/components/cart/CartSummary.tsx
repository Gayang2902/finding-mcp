import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Tag, X, Truck, ShoppingBag } from 'lucide-react'
import Button from '../common/Button'
import Input from '../common/Input'

interface AppliedCoupon {
  code: string
  discount: number
}

interface CartSummaryProps {
  subtotal: number
  shippingCost?: number
  tax?: number
  appliedCoupon?: AppliedCoupon | null
  onApplyCoupon?: (code: string) => Promise<void>
  onRemoveCoupon?: () => void
  onCheckout?: () => void
  loading?: boolean
}

export default function CartSummary({
  subtotal,
  shippingCost = 0,
  tax = 0,
  appliedCoupon,
  onApplyCoupon,
  onRemoveCoupon,
  onCheckout,
  loading = false,
}: CartSummaryProps) {
  const [couponInput, setCouponInput] = useState('')
  const [applying, setApplying] = useState(false)

  const discount = appliedCoupon?.discount ?? 0
  const total = Math.max(0, subtotal - discount + shippingCost + tax)

  async function handleApplyCoupon() {
    if (!couponInput.trim() || !onApplyCoupon) return
    setApplying(true)
    try {
      await onApplyCoupon(couponInput.trim())
      setCouponInput('')
    } finally {
      setApplying(false)
    }
  }

  function Row({ label, value, className }: { label: string; value: string; className?: string }) {
    return (
      <div className={`flex justify-between text-sm ${className ?? ''}`}>
        <span className="text-gray-600">{label}</span>
        <span className="font-medium text-gray-900">{value}</span>
      </div>
    )
  }

  return (
    <div className="rounded-2xl border border-gray-100 bg-white p-6 shadow-sm space-y-4">
      <h2 className="text-base font-semibold text-gray-900">Order Summary</h2>

      <Row label="Subtotal" value={`$${subtotal.toFixed(2)}`} />

      {/* Coupon */}
      {!appliedCoupon ? (
        <div className="flex gap-2">
          <Input
            placeholder="Coupon code"
            value={couponInput}
            onChange={(e) => setCouponInput(e.target.value)}
            iconLeft={<Tag className="h-4 w-4" />}
            onKeyDown={(e) => e.key === 'Enter' && handleApplyCoupon()}
          />
          <Button
            variant="outline"
            size="sm"
            onClick={handleApplyCoupon}
            loading={applying}
            disabled={!couponInput.trim()}
            className="flex-shrink-0"
          >
            Apply
          </Button>
        </div>
      ) : (
        <div className="flex items-center justify-between rounded-lg bg-green-50 px-3 py-2">
          <div className="flex items-center gap-2 text-sm text-green-700">
            <Tag className="h-4 w-4" />
            <span className="font-medium">{appliedCoupon.code}</span>
          </div>
          <button
            onClick={onRemoveCoupon}
            className="text-green-600 hover:text-green-800 transition-colors"
            aria-label="Remove coupon"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {discount > 0 && (
        <Row label="Coupon discount" value={`-$${discount.toFixed(2)}`} className="text-green-600" />
      )}

      <div className="flex justify-between text-sm">
        <span className="flex items-center gap-1.5 text-gray-600">
          <Truck className="h-4 w-4" />
          Shipping
        </span>
        <span className="font-medium text-gray-900">
          {shippingCost === 0 ? 'Free' : `$${shippingCost.toFixed(2)}`}
        </span>
      </div>

      {tax > 0 && <Row label="Tax" value={`$${tax.toFixed(2)}`} />}

      <div className="border-t border-gray-100 pt-4">
        <div className="flex justify-between text-base font-semibold text-gray-900">
          <span>Total</span>
          <span>${total.toFixed(2)}</span>
        </div>
      </div>

      <Button
        fullWidth
        loading={loading}
        onClick={onCheckout}
        iconLeft={<ShoppingBag className="h-4 w-4" />}
      >
        Proceed to Checkout
      </Button>

      <Link
        to="/products"
        className="block text-center text-sm text-indigo-600 hover:text-indigo-700 transition-colors"
      >
        Continue Shopping
      </Link>
    </div>
  )
}
