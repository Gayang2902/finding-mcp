import { clsx } from 'clsx'

interface PriceDisplayProps {
  price: number
  compareAtPrice?: number
  currency?: string
  className?: string
  size?: 'sm' | 'md' | 'lg'
}

const sizeClasses = {
  sm: { price: 'text-sm font-semibold', original: 'text-xs', badge: 'text-xs px-1 py-0.5' },
  md: { price: 'text-base font-semibold', original: 'text-sm', badge: 'text-xs px-1.5 py-0.5' },
  lg: { price: 'text-xl font-bold', original: 'text-sm', badge: 'text-xs px-2 py-1' },
}

function formatCurrency(amount: number, currency: string) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount)
}

export default function PriceDisplay({
  price,
  compareAtPrice,
  currency = 'USD',
  className,
  size = 'md',
}: PriceDisplayProps) {
  const hasDiscount = compareAtPrice !== undefined && compareAtPrice > price
  const discountPct = hasDiscount
    ? Math.round(((compareAtPrice - price) / compareAtPrice) * 100)
    : 0
  const s = sizeClasses[size]

  return (
    <div className={clsx('flex items-center gap-2 flex-wrap', className)}>
      <span className={clsx('text-gray-900', s.price)}>
        {formatCurrency(price, currency)}
      </span>
      {hasDiscount && (
        <>
          <span className={clsx('text-gray-400 line-through', s.original)}>
            {formatCurrency(compareAtPrice, currency)}
          </span>
          <span className={clsx('rounded bg-red-100 text-red-600 font-medium', s.badge)}>
            -{discountPct}%
          </span>
        </>
      )}
    </div>
  )
}
