import { useState } from 'react'
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react'
import { clsx } from 'clsx'

type AlertType = 'success' | 'error' | 'warning' | 'info'

interface AlertProps {
  type?: AlertType
  title?: string
  message: string
  dismissible?: boolean
  className?: string
}

const typeConfig: Record<AlertType, { icon: React.ReactNode; classes: string }> = {
  success: {
    icon: <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" />,
    classes: 'bg-green-50 border-green-200 text-green-800',
  },
  error: {
    icon: <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />,
    classes: 'bg-red-50 border-red-200 text-red-800',
  },
  warning: {
    icon: <AlertTriangle className="h-5 w-5 text-yellow-500 flex-shrink-0" />,
    classes: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  },
  info: {
    icon: <Info className="h-5 w-5 text-blue-500 flex-shrink-0" />,
    classes: 'bg-blue-50 border-blue-200 text-blue-800',
  },
}

export default function Alert({ type = 'info', title, message, dismissible = false, className }: AlertProps) {
  const [dismissed, setDismissed] = useState(false)
  if (dismissed) return null

  const { icon, classes } = typeConfig[type]

  return (
    <div className={clsx('flex gap-3 rounded-lg border p-4', classes, className)} role="alert">
      {icon}
      <div className="flex-1 min-w-0">
        {title && <p className="text-sm font-semibold">{title}</p>}
        <p className="text-sm">{message}</p>
      </div>
      {dismissible && (
        <button
          onClick={() => setDismissed(true)}
          className="flex-shrink-0 rounded p-0.5 hover:bg-black/10 transition-colors"
          aria-label="Dismiss"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}
