import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Package, MapPin, CreditCard, Truck, XCircle, RefreshCw } from 'lucide-react'
import { useMutation, useQueryClient } from 'react-query'
import { useOrder } from '../hooks/useOrders'
import { orderService } from '../services/orderService'
import { OrderStatus } from '../types'
import { formatCurrency, formatDate, formatDateTime } from '../utils/formatters'
import { OrderStatusBadge, PaymentStatusBadge } from '../components/common/StatusBadge'
import LoadingSpinner from '../components/common/LoadingSpinner'
import toast from 'react-hot-toast'

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>()
  const orderId = Number(id)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: order, isLoading } = useOrder(orderId)

  const cancelOrder = useMutation(() => orderService.cancelOrder(orderId), {
    onSuccess: () => {
      toast.success('Order cancelled')
      queryClient.invalidateQueries(['order', orderId])
    },
  })

  const requestRefund = useMutation(() => orderService.requestRefund(orderId, 'Customer requested refund'), {
    onSuccess: () => {
      toast.success('Refund requested')
      queryClient.invalidateQueries(['order', orderId])
    },
  })

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-96">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!order) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center">
        <p className="text-gray-500">Order not found.</p>
      </div>
    )
  }

  const canCancel = [OrderStatus.PENDING, OrderStatus.CONFIRMED].includes(order.status)
  const canRefund = order.status === OrderStatus.DELIVERED

  const STATUS_STEPS = [
    OrderStatus.PENDING,
    OrderStatus.CONFIRMED,
    OrderStatus.PROCESSING,
    OrderStatus.SHIPPED,
    OrderStatus.DELIVERED,
  ]
  const currentStepIdx = STATUS_STEPS.indexOf(order.status)

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-1 text-gray-500 hover:text-gray-700 text-sm mb-6"
      >
        <ArrowLeft className="w-4 h-4" /> Back to orders
      </button>

      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Order #{order.orderNumber}</h1>
            <p className="text-sm text-gray-500 mt-0.5">Placed on {formatDate(order.createdAt)}</p>
          </div>
          <div className="flex items-center gap-3">
            <OrderStatusBadge status={order.status} />
            {canCancel && (
              <button
                onClick={() => cancelOrder.mutate()}
                disabled={cancelOrder.isLoading}
                className="flex items-center gap-1.5 text-sm text-red-500 border border-red-200 px-3 py-1.5 rounded-lg hover:bg-red-50 disabled:opacity-50"
              >
                <XCircle className="w-4 h-4" />
                Cancel Order
              </button>
            )}
            {canRefund && (
              <button
                onClick={() => requestRefund.mutate()}
                disabled={requestRefund.isLoading}
                className="flex items-center gap-1.5 text-sm text-indigo-500 border border-indigo-200 px-3 py-1.5 rounded-lg hover:bg-indigo-50 disabled:opacity-50"
              >
                <RefreshCw className="w-4 h-4" />
                Request Refund
              </button>
            )}
          </div>
        </div>

        {/* Status timeline */}
        {order.status !== OrderStatus.CANCELLED && order.status !== OrderStatus.REFUNDED && (
          <div className="mt-6">
            <div className="flex items-center">
              {STATUS_STEPS.map((step, i) => (
                <div key={step} className="flex items-center flex-1 last:flex-none">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                    i <= currentStepIdx ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-400'
                  }`}>
                    {i + 1}
                  </div>
                  {i < STATUS_STEPS.length - 1 && (
                    <div className={`flex-1 h-1 mx-1 rounded ${i < currentStepIdx ? 'bg-indigo-600' : 'bg-gray-100'}`} />
                  )}
                </div>
              ))}
            </div>
            <div className="flex justify-between mt-1">
              {STATUS_STEPS.map((step) => (
                <span key={step} className="text-xs text-gray-500 capitalize">{step.toLowerCase()}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left: items */}
        <div className="md:col-span-2 space-y-4">
          {/* Items */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-sm font-semibold text-gray-900 flex items-center gap-2 mb-4">
              <Package className="w-4 h-4 text-gray-500" /> Items ({order.items.length})
            </h2>
            <div className="space-y-4">
              {order.items.map((item) => (
                <div key={item.id} className="flex gap-4">
                  <div className="w-16 h-16 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                    {item.productImageUrl ? (
                      <img src={item.productImageUrl} alt={item.productName} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Package className="w-6 h-6 text-gray-300" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{item.productName}</p>
                    <p className="text-xs text-gray-500">Qty: {item.quantity} × {formatCurrency(item.unitPrice)}</p>
                  </div>
                  <p className="text-sm font-bold text-gray-900">{formatCurrency(item.totalPrice)}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Shipping tracking */}
          {order.shippingInfo && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h2 className="text-sm font-semibold text-gray-900 flex items-center gap-2 mb-4">
                <Truck className="w-4 h-4 text-gray-500" /> Shipping
              </h2>
              <div className="flex gap-4 text-sm mb-4">
                <div>
                  <p className="text-xs text-gray-500">Carrier</p>
                  <p className="font-medium">{order.shippingInfo.carrier}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Tracking #</p>
                  <p className="font-medium font-mono">{order.shippingInfo.trackingNumber}</p>
                </div>
                {order.shippingInfo.estimatedDelivery && (
                  <div>
                    <p className="text-xs text-gray-500">Est. Delivery</p>
                    <p className="font-medium">{formatDate(order.shippingInfo.estimatedDelivery)}</p>
                  </div>
                )}
              </div>
              {order.shippingInfo.events && order.shippingInfo.events.length > 0 && (
                <div className="border-l-2 border-gray-200 pl-4 space-y-3">
                  {order.shippingInfo.events.map((event, i) => (
                    <div key={i}>
                      <p className="text-xs text-gray-500">{formatDateTime(event.timestamp)}</p>
                      <p className="text-sm font-medium">{event.status}</p>
                      <p className="text-xs text-gray-600">{event.description}</p>
                      {event.location && <p className="text-xs text-gray-400">{event.location}</p>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right: summary */}
        <div className="space-y-4">
          {/* Shipping address */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-sm font-semibold text-gray-900 flex items-center gap-2 mb-3">
              <MapPin className="w-4 h-4 text-gray-500" /> Shipping Address
            </h2>
            <div className="text-sm text-gray-600 space-y-0.5">
              <p className="font-medium text-gray-900">{order.shippingAddress.recipientName}</p>
              <p>{order.shippingAddress.street}</p>
              <p>{order.shippingAddress.city}, {order.shippingAddress.state} {order.shippingAddress.postalCode}</p>
              <p>{order.shippingAddress.country}</p>
              {order.shippingAddress.phone && <p>{order.shippingAddress.phone}</p>}
            </div>
          </div>

          {/* Payment */}
          {order.payment && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h2 className="text-sm font-semibold text-gray-900 flex items-center gap-2 mb-3">
                <CreditCard className="w-4 h-4 text-gray-500" /> Payment
              </h2>
              <div className="text-sm space-y-1">
                <div className="flex justify-between">
                  <span className="text-gray-500">Method</span>
                  <span className="font-medium">{order.payment.method.replace('_', ' ')}</span>
                </div>
                {order.payment.cardLast4 && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Card</span>
                    <span className="font-medium">•••• {order.payment.cardLast4}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-500">Status</span>
                  <PaymentStatusBadge status={order.payment.status} />
                </div>
              </div>
            </div>
          )}

          {/* Order totals */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-sm font-semibold text-gray-900 mb-3">Summary</h2>
            <div className="space-y-1.5 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Subtotal</span>
                <span>{formatCurrency(order.subtotal)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Shipping</span>
                <span>{order.shippingCost === 0 ? 'FREE' : formatCurrency(order.shippingCost)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Tax</span>
                <span>{formatCurrency(order.tax)}</span>
              </div>
              {order.discount > 0 && (
                <div className="flex justify-between text-green-600">
                  <span>Discount</span>
                  <span>-{formatCurrency(order.discount)}</span>
                </div>
              )}
              <div className="flex justify-between font-bold border-t border-gray-100 pt-2 mt-2">
                <span>Total</span>
                <span>{formatCurrency(order.total)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
