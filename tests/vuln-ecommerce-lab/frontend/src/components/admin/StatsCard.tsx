import { clsx } from 'clsx'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface StatsCardProps {
  title: string
  value: string | number
  trend?: number
  icon: React.ReactNode
  colorVariant?: 'indigo' | 'green' | 'yellow' | 'red'
}

const colorMap = {
  indigo: 'bg-indigo-50 text-indigo-600',
  green: 'bg-green-50 text-green-600',
  yellow: 'bg-yellow-50 text-yellow-600',
  red: 'bg-red-50 text-red-600',
}

export default function StatsCard({ title, value, trend, icon, colorVariant = 'indigo' }: StatsCardProps) {
  const isUp = trend !== undefined && trend > 0
  const isDown = trend !== undefined && trend < 0
  const isFlat = trend !== undefined && trend === 0

  return (
    <div className="rounded-xl bg-white border border-gray-100 shadow-sm p-5 flex items-start gap-4">
      <div className={clsx('flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl', colorMap[colorVariant])}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-500 truncate">{title}</p>
        <p className="text-2xl font-bold text-gray-900 mt-0.5">{value}</p>
        {trend !== undefined && (
          <div className={clsx(
            'flex items-center gap-1 text-xs font-medium mt-1',
            isUp && 'text-green-600',
            isDown && 'text-red-500',
            isFlat && 'text-gray-400'
          )}>
            {isUp && <TrendingUp className="h-3.5 w-3.5" />}
            {isDown && <TrendingDown className="h-3.5 w-3.5" />}
            {isFlat && <Minus className="h-3.5 w-3.5" />}
            <span>{isUp ? '+' : ''}{trend}% vs last month</span>
          </div>
        )}
      </div>
    </div>
  )
}
