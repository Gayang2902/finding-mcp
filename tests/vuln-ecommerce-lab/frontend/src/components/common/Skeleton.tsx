import { clsx } from 'clsx'

type Variant = 'text' | 'circle' | 'rectangle' | 'card'

interface SkeletonProps {
  variant?: Variant
  width?: string
  height?: string
  className?: string
  lines?: number
}

function SkeletonBase({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return <div className={clsx('animate-pulse bg-gray-200 rounded', className)} style={style} />
}

export default function Skeleton({ variant = 'text', width, height, className, lines = 3 }: SkeletonProps) {
  const style: React.CSSProperties = {}
  if (width) style.width = width
  if (height) style.height = height

  if (variant === 'text') {
    return (
      <div className={clsx('space-y-2', className)} style={style}>
        {Array.from({ length: lines }, (_, i) => (
          <SkeletonBase
            key={i}
            className={clsx('h-4 rounded', i === lines - 1 && lines > 1 ? 'w-3/4' : 'w-full')}
          />
        ))}
      </div>
    )
  }

  if (variant === 'circle') {
    return <SkeletonBase className={clsx('rounded-full', className)} style={{ width: width ?? '3rem', height: height ?? '3rem', ...style }} />
  }

  if (variant === 'card') {
    return (
      <div className={clsx('rounded-xl overflow-hidden', className)}>
        <SkeletonBase className="h-48 w-full rounded-none" />
        <div className="p-4 space-y-3">
          <SkeletonBase className="h-4 w-3/4" />
          <SkeletonBase className="h-4 w-1/2" />
          <SkeletonBase className="h-8 w-full" />
        </div>
      </div>
    )
  }

  // rectangle
  return <SkeletonBase className={clsx('rounded-lg', className)} style={{ width: width ?? '100%', height: height ?? '1rem', ...style }} />
}
