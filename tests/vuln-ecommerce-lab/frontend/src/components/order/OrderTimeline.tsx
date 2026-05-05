import { format } from 'date-fns'
import { clsx } from 'clsx'
import {
  Clock,
  CheckCircle,
  Settings,
  Truck,
  Home,
  XCircle,
  RefreshCw,
} from 'lucide-react'
import { OrderStatus } from '../../types'

interface TimelineStep {
  status: OrderStatus
  label: string
  date?: string
  icon: React.ReactNode
}

interface OrderTimelineProps {
  currentStatus: OrderStatus
  statusHistory?: { status: OrderStatus; timestamp: string }[]
}

const STEPS: Omit<TimelineStep, 'date'>[] = [
  { status: OrderStatus.PENDING, label: 'Order Placed', icon: <Clock className="h-4 w-4" /> },
  { status: OrderStatus.CONFIRMED, label: 'Confirmed', icon: <CheckCircle className="h-4 w-4" /> },
  { status: OrderStatus.PROCESSING, label: 'Processing', icon: <Settings className="h-4 w-4" /> },
  { status: OrderStatus.SHIPPED, label: 'Shipped', icon: <Truck className="h-4 w-4" /> },
  { status: OrderStatus.DELIVERED, label: 'Delivered', icon: <Home className="h-4 w-4" /> },
]

const STATUS_ORDER = [
  OrderStatus.PENDING,
  OrderStatus.CONFIRMED,
  OrderStatus.PROCESSING,
  OrderStatus.SHIPPED,
  OrderStatus.DELIVERED,
]

export default function OrderTimeline({ currentStatus, statusHistory = [] }: OrderTimelineProps) {
  const isCancelled = currentStatus === OrderStatus.CANCELLED
  const isRefunded = currentStatus === OrderStatus.REFUNDED
  const currentIndex = STATUS_ORDER.indexOf(currentStatus)

  function getStepDate(status: OrderStatus) {
    return statusHistory.find((h) => h.status === status)?.timestamp
  }

  if (isCancelled || isRefunded) {
    const Icon = isCancelled ? XCircle : RefreshCw
    const label = isCancelled ? 'Order Cancelled' : 'Order Refunded'
    const color = isCancelled ? 'text-red-600 bg-red-100' : 'text-orange-600 bg-orange-100'

    return (
      <div className="flex items-center gap-3 rounded-xl border border-red-100 bg-red-50 p-4">
        <div className={clsx('flex h-10 w-10 items-center justify-center rounded-full', color)}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-sm font-semibold text-gray-800">{label}</p>
          {getStepDate(currentStatus) && (
            <p className="text-xs text-gray-500">
              {format(new Date(getStepDate(currentStatus)!), 'MMM d, yyyy h:mm a')}
            </p>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="relative">
      {STEPS.map((step, i) => {
        const isCompleted = i < currentIndex
        const isActive = i === currentIndex
        const stepDate = getStepDate(step.status)

        return (
          <div key={step.status} className="flex gap-4 pb-6 last:pb-0">
            {/* Icon + connector */}
            <div className="flex flex-col items-center">
              <div
                className={clsx(
                  'flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full border-2 transition-colors',
                  isCompleted
                    ? 'bg-indigo-600 border-indigo-600 text-white'
                    : isActive
                    ? 'bg-white border-indigo-600 text-indigo-600'
                    : 'bg-white border-gray-200 text-gray-300'
                )}
              >
                {isActive && (
                  <span className="absolute h-9 w-9 rounded-full bg-indigo-400 opacity-30 animate-ping" />
                )}
                {step.icon}
              </div>
              {i < STEPS.length - 1 && (
                <div
                  className={clsx(
                    'w-0.5 flex-1 mt-1',
                    i < currentIndex ? 'bg-indigo-600' : 'bg-gray-200'
                  )}
                  style={{ minHeight: '1.5rem' }}
                />
              )}
            </div>

            {/* Label */}
            <div className="pt-1.5 pb-2">
              <p className={clsx('text-sm font-medium', isActive || isCompleted ? 'text-gray-900' : 'text-gray-400')}>
                {step.label}
              </p>
              {stepDate && (
                <p className="text-xs text-gray-500 mt-0.5">
                  {format(new Date(stepDate), 'MMM d, yyyy h:mm a')}
                </p>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
