import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Package, ChevronRight } from 'lucide-react'
import { useMyOrders } from '../hooks/useOrders'
import { OrderStatus } from '../types'
import { formatCurrency, formatDate } from '../utils/formatters'
import { OrderStatusBadge } from '../components/common/StatusBadge'
import LoadingSpinner from '../components/common/LoadingSpinner'
import EmptyState from '../components/common/EmptyState'

const STATUS_TABS = [
  { label: 'All', value: undefined },
  { label: 'Pending', value: OrderStatus.PENDING },
  { label: 'Processing', value: OrderStatus.PROCESSING },
  { label: 'Shipped', value: OrderStatus.SHIPPED },
  { label: 'Delivered', value: OrderStatus.DELIVERED },
  { label: 'Cancelled', value: OrderStatus.CANCELLED },
]

export default function OrderListPage() {
  const navigate = useNavigate()
  const [activeStatus, setActiveStatus] = useState<OrderStatus | undefined>(undefined)
  const { data, isLoading } = useMyOrders(activeStatus)

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">My Orders</h1>

      {/* Status tabs */}
      <div className="flex gap-1 overflow-x-auto pb-2 mb-6">
        {STATUS_TABS.map((tab) => (
          <button
            key={String(tab.value)}
            onClick={() => setActiveStatus(tab.value)}
            className={`flex-shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              activeStatus === tab.value
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner size="lg" />
        </div>
      ) : !data?.content.length ? (
        <EmptyState
          icon={<Package className="w-10 h-10" />}
          title="No orders found"
          description="You haven't placed any orders yet."
          actionLabel="Start Shopping"
          onAction={() => navigate('/products')}
        />
      ) : (
        <div className="space-y-4">
          {data.content.map((order) => (
            <div
              key={order.id}
              onClick={() => navigate(`/orders/${order.id}`)}
              className="bg-white rounded-xl border border-gray-200 p-5 cursor-pointer hover:border-indigo-200 hover:shadow-sm transition-all"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <p className="text-xs text-gray-500 mb-0.5">Order #{order.orderNumber}</p>
                  <p className="text-sm font-medium text-gray-900">{formatDate(order.createdAt)}</p>
                </div>
                <div className="flex items-center gap-3">
                  <OrderStatusBadge status={order.status} />
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                </div>
              </div>

              {/* Items preview */}
              <div className="flex gap-2 mb-3">
                {order.items.slice(0, 3).map((item) => (
                  <div key={item.id} className="w-12 h-12 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                    {item.productImageUrl ? (
                      <img src={item.productImageUrl} alt={item.productName} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Package className="w-5 h-5 text-gray-300" />
                      </div>
                    )}
                  </div>
                ))}
                {order.items.length > 3 && (
                  <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center text-xs text-gray-500 font-medium">
                    +{order.items.length - 3}
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">{order.items.length} item{order.items.length !== 1 ? 's' : ''}</span>
                <span className="font-bold text-gray-900">{formatCurrency(order.total)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
