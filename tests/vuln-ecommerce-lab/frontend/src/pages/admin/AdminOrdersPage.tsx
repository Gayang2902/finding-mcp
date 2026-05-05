import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { ShoppingCart, ChevronRight } from 'lucide-react'
import { orderService } from '../../services/orderService'
import { OrderStatus } from '../../types'
import { formatCurrency, formatDate } from '../../utils/formatters'
import { OrderStatusBadge } from '../../components/common/StatusBadge'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import Pagination from '../../components/common/Pagination'
import toast from 'react-hot-toast'

const STATUS_TABS = [
  { label: 'All', value: undefined },
  { label: 'Pending', value: OrderStatus.PENDING },
  { label: 'Processing', value: OrderStatus.PROCESSING },
  { label: 'Shipped', value: OrderStatus.SHIPPED },
  { label: 'Delivered', value: OrderStatus.DELIVERED },
  { label: 'Cancelled', value: OrderStatus.CANCELLED },
]

export default function AdminOrdersPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState<OrderStatus | undefined>(undefined)
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery(
    ['admin-orders', statusFilter, page],
    () => orderService.getAllOrders({ status: statusFilter, page: page - 1, size: 20 }),
    { keepPreviousData: true }
  )

  const updateStatus = useMutation(
    ({ id, status }: { id: number; status: OrderStatus }) => orderService.updateOrderStatus(id, status),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('admin-orders')
        toast.success('Order status updated')
      },
    }
  )

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">All Orders</h1>
        <span className="text-sm text-gray-500">{data?.totalElements ?? 0} orders</span>
      </div>

      {/* Status tabs */}
      <div className="flex gap-1 overflow-x-auto pb-2 mb-6">
        {STATUS_TABS.map((tab) => (
          <button
            key={String(tab.value)}
            onClick={() => { setStatusFilter(tab.value); setPage(1) }}
            className={`flex-shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              statusFilter === tab.value ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
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
      ) : (
        <>
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    <th className="px-4 py-3 text-left">Order</th>
                    <th className="px-4 py-3 text-left">Customer</th>
                    <th className="px-4 py-3 text-left">Date</th>
                    <th className="px-4 py-3 text-left">Status</th>
                    <th className="px-4 py-3 text-left">Update Status</th>
                    <th className="px-4 py-3 text-right">Total</th>
                    <th className="px-4 py-3" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data?.content.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-12 text-gray-400">
                        <ShoppingCart className="w-10 h-10 mx-auto mb-2 opacity-40" />
                        <p>No orders found</p>
                      </td>
                    </tr>
                  ) : (
                    data?.content.map((order) => (
                      <tr key={order.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3">
                          <p className="text-sm font-medium text-indigo-600">#{order.orderNumber}</p>
                          <p className="text-xs text-gray-400">{order.items.length} item(s)</p>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-700">
                          {order.user ? `${order.user.firstName} ${order.user.lastName}` : '—'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500">{formatDate(order.createdAt)}</td>
                        <td className="px-4 py-3">
                          <OrderStatusBadge status={order.status} />
                        </td>
                        <td className="px-4 py-3">
                          <select
                            value={order.status}
                            onChange={(e) => updateStatus.mutate({ id: order.id, status: e.target.value as OrderStatus })}
                            className="text-xs border border-gray-300 rounded-lg px-2 py-1 bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                          >
                            {Object.values(OrderStatus).map((s) => (
                              <option key={s} value={s}>{s}</option>
                            ))}
                          </select>
                        </td>
                        <td className="px-4 py-3 text-right font-semibold text-sm">{formatCurrency(order.total)}</td>
                        <td className="px-4 py-3">
                          <button
                            onClick={() => navigate(`/admin/orders/${order.id}`)}
                            className="p-1.5 text-gray-400 hover:text-indigo-600 transition-colors"
                          >
                            <ChevronRight className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {data && data.totalPages > 1 && (
            <div className="mt-6">
              <Pagination page={page} totalPages={data.totalPages} onPageChange={setPage} />
            </div>
          )}
        </>
      )}
    </div>
  )
}
