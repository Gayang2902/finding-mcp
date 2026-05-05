import { useState } from 'react'
import { format } from 'date-fns'
import { Copy, Check, MapPin, Truck, Calendar } from 'lucide-react'
import { clsx } from 'clsx'
import { ShippingInfo } from '../../types'
import StatusBadge from '../common/StatusBadge'

interface TrackingInfoProps {
  shippingInfo: ShippingInfo
}

export default function TrackingInfo({ shippingInfo }: TrackingInfoProps) {
  const [copied, setCopied] = useState(false)

  async function copyTracking() {
    await navigator.clipboard.writeText(shippingInfo.trackingNumber)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="rounded-xl border border-gray-100 bg-white p-5 shadow-sm space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-gray-700">
          <Truck className="h-5 w-5 text-indigo-500" />
          <span className="font-semibold text-gray-900">{shippingInfo.carrier}</span>
        </div>
        <StatusBadge status={shippingInfo.status} />
      </div>

      {/* Tracking number */}
      <div className="flex items-center gap-3 rounded-lg bg-gray-50 px-4 py-3">
        <div className="flex-1 min-w-0">
          <p className="text-xs text-gray-500 mb-0.5">Tracking Number</p>
          <p className="text-sm font-mono font-semibold text-gray-800 truncate">
            {shippingInfo.trackingNumber}
          </p>
        </div>
        <button
          onClick={copyTracking}
          className="flex items-center gap-1.5 rounded-lg bg-white border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 transition-colors shadow-sm"
          aria-label="Copy tracking number"
        >
          {copied ? (
            <><Check className="h-3.5 w-3.5 text-green-500" /> Copied</>
          ) : (
            <><Copy className="h-3.5 w-3.5" /> Copy</>
          )}
        </button>
      </div>

      {/* Estimated delivery */}
      {shippingInfo.estimatedDelivery && (
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Calendar className="h-4 w-4 text-indigo-400 flex-shrink-0" />
          <span>
            Estimated delivery:{' '}
            <span className="font-semibold text-gray-900">
              {format(new Date(shippingInfo.estimatedDelivery), 'EEEE, MMM d, yyyy')}
            </span>
          </span>
        </div>
      )}

      {/* Events timeline */}
      {shippingInfo.events.length > 0 && (
        <div>
          <p className="text-sm font-semibold text-gray-800 mb-3">Shipping History</p>
          <div className="relative">
            {shippingInfo.events.map((event, i) => (
              <div key={i} className="flex gap-3 pb-5 last:pb-0">
                <div className="flex flex-col items-center">
                  <div
                    className={clsx(
                      'h-3 w-3 rounded-full flex-shrink-0 mt-0.5',
                      i === 0 ? 'bg-indigo-600' : 'bg-gray-300'
                    )}
                  />
                  {i < shippingInfo.events.length - 1 && (
                    <div className="w-0.5 flex-1 bg-gray-200 mt-1" style={{ minHeight: '1.25rem' }} />
                  )}
                </div>
                <div className="flex-1 min-w-0 pb-1">
                  <p className={clsx('text-sm font-medium', i === 0 ? 'text-gray-900' : 'text-gray-600')}>
                    {event.description}
                  </p>
                  {event.location && (
                    <p className="flex items-center gap-1 text-xs text-gray-400 mt-0.5">
                      <MapPin className="h-3 w-3" /> {event.location}
                    </p>
                  )}
                  <p className="text-xs text-gray-400 mt-0.5">
                    {format(new Date(event.timestamp), 'MMM d, yyyy h:mm a')}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
