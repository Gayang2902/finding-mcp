import { useQuery } from 'react-query'
import { Link } from 'react-router-dom'
import { ShoppingCart, Users, Package, DollarSign, TrendingUp, ArrowRight } from 'lucide-react'
import { adminService } from '../../services/adminService'
import { formatCurrency, formatDate } from '../../utils/formatters'
import { OrderStatusBadge } from '../../components/common/StatusBadge'
import LoadingSpinner from '../../components/common/LoadingSpinner'

export default function AdminDashboardPage() {
  const { data: dashboard, isLoading } = useQuery('admin-dashboard', adminService.getDashboard)

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-96">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  const stats = [
    { label: 'Total Orders', value: dashboard?.totalOrders ?? 0, icon: ShoppingCart, color: 'text-blue-600 bg-blue-100', format: (v: number) => v.toLocaleString() },
    { label: 'Revenue', value: dashboard?.totalRevenue ?? 0, icon: DollarSign, color: 'text-green-600 bg-green-100', format: formatCurrency },
    { label: 'Products', value: dashboard?.totalProducts ?? 0, icon: Package, color: 'text-purple-600 bg-purple-100', format: (v: number) => v.toLocaleString() },
    { label: 'Customers', value: dashboard?.totalCustomers ?? 0, icon: Users, color: 'text-orange-600 bg-orange-100', format: (v: number) => v.toLocaleString() },
  ]

  const topProducts = dashboard?.topProducts ?? []
  const maxRevenue = Math.max(...topProducts.map((p) => p.price * (p.reviewCount || 1)), 1)

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-sm text-gray-500 mt-0.5">Overview of your store</p>
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        {stats.map(({ label, value, icon: Icon, color, format }) => (
          <div key={label} className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm text-gray-500 font-medium">{label}</p>
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
                <Icon className="w-5 h-5" />
              </div>
            </div>
            <p className="text-2xl font-extrabold text-gray-900">{format(value)}</p>
            <p className="text-xs text-green-600 flex items-center gap-1 mt-1">
              <TrendingUp className="w-3 h-3" /> Live data
            </p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent orders */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-900">Recent Orders</h2>
            <Link to="/admin/orders" className="text-sm text-indigo-600 hover:text-indigo-700 flex items-center gap-1">
              View all <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          {!dashboard?.recentOrders?.length ? (
            <p className="text-sm text-gray-500 text-center py-8">No orders yet</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-xs font-medium text-gray-500 border-b border-gray-100">
                    <th className="pb-2 text-left">Order</th>
                    <th className="pb-2 text-left">Customer</th>
                    <th className="pb-2 text-left">Status</th>
                    <th className="pb-2 text-right">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {dashboard.recentOrders.map((order) => (
                    <tr key={order.id} className="text-sm">
                      <td className="py-3">
                        <Link to={`/admin/orders/${order.id}`} className="font-medium text-indigo-600 hover:text-indigo-700">
                          #{order.orderNumber}
                        </Link>
                        <p className="text-xs text-gray-400">{formatDate(order.createdAt)}</p>
                      </td>
                      <td className="py-3 text-gray-700">
                        {order.user ? `${order.user.firstName} ${order.user.lastName}` : '—'}
                      </td>
                      <td className="py-3">
                        <OrderStatusBadge status={order.status} />
                      </td>
                      <td className="py-3 text-right font-semibold">{formatCurrency(order.total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Top products bar chart */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-900">Top Products</h2>
            <Link to="/admin/products" className="text-sm text-indigo-600 hover:text-indigo-700 flex items-center gap-1">
              All <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          {!topProducts.length ? (
            <p className="text-sm text-gray-500 text-center py-8">No products yet</p>
          ) : (
            <div className="space-y-3">
              {topProducts.slice(0, 6).map((product) => {
                const barWidth = Math.round((product.price / maxRevenue) * 100)
                return (
                  <div key={product.id}>
                    <div className="flex justify-between text-xs text-gray-600 mb-0.5">
                      <span className="truncate max-w-[140px]" title={product.name}>{product.name}</span>
                      <span className="font-semibold">{formatCurrency(product.price)}</span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-indigo-500 rounded-full transition-all"
                        style={{ width: `${barWidth}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Quick links */}
      <div className="mt-6 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          { to: '/admin/users', label: 'Manage Users', icon: Users },
          { to: '/admin/orders', label: 'All Orders', icon: ShoppingCart },
          { to: '/admin/products', label: 'Products', icon: Package },
          { to: '/admin/reviews', label: 'Reviews', icon: Package },
          { to: '/admin/coupons', label: 'Coupons', icon: DollarSign },
        ].map(({ to, label, icon: Icon }) => (
          <Link
            key={to}
            to={to}
            className="flex flex-col items-center gap-2 p-4 bg-white rounded-xl border border-gray-200 hover:border-indigo-200 hover:shadow-sm transition-all text-center"
          >
            <Icon className="w-5 h-5 text-indigo-600" />
            <span className="text-xs font-medium text-gray-700">{label}</span>
          </Link>
        ))}
      </div>
    </div>
  )
}
