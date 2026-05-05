import { useState } from 'react'
import { Star } from 'lucide-react'
import { clsx } from 'clsx'

type Size = 'sm' | 'md' | 'lg'

interface StarRatingProps {
  rating: number
  maxStars?: number
  interactive?: boolean
  onChange?: (rating: number) => void
  showValue?: boolean
  size?: Size
  className?: string
}

const sizeClasses: Record<Size, string> = {
  sm: 'h-3.5 w-3.5',
  md: 'h-5 w-5',
  lg: 'h-6 w-6',
}

export default function StarRating({
  rating,
  maxStars = 5,
  interactive = false,
  onChange,
  showValue = false,
  size = 'md',
  className,
}: StarRatingProps) {
  const [hovered, setHovered] = useState(0)
  const displayRating = interactive && hovered > 0 ? hovered : rating

  return (
    <div className={clsx('flex items-center gap-0.5', className)}>
      {Array.from({ length: maxStars }, (_, i) => {
        const starValue = i + 1
        const filled = starValue <= Math.floor(displayRating)
        const half = !filled && starValue - 0.5 <= displayRating

        return (
          <button
            key={i}
            type="button"
            disabled={!interactive}
            onClick={() => interactive && onChange?.(starValue)}
            onMouseEnter={() => interactive && setHovered(starValue)}
            onMouseLeave={() => interactive && setHovered(0)}
            className={clsx(
              'transition-transform',
              interactive ? 'cursor-pointer hover:scale-110' : 'cursor-default pointer-events-none'
            )}
            aria-label={`${starValue} star${starValue !== 1 ? 's' : ''}`}
          >
            <Star
              className={clsx(
                sizeClasses[size],
                filled || half
                  ? 'fill-yellow-400 text-yellow-400'
                  : 'fill-gray-200 text-gray-200'
              )}
            />
          </button>
        )
      })}
      {showValue && (
        <span className="ml-1 text-sm font-medium text-gray-600">
          {rating.toFixed(1)}
        </span>
      )}
    </div>
  )
}
