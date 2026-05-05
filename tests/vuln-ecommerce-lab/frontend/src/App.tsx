import { Routes, Route } from 'react-router-dom'
import Header from './components/layout/Header'
import Footer from './components/layout/Footer'
import { RequireAuth, RequireAdmin } from './components/common/RequireAuth'

// Pages
import HomePage from './pages/HomePage'
import ProductListPage from './pages/ProductListPage'
import ProductDetailPage from './pages/ProductDetailPage'
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import CartPage from './pages/CartPage'
import CheckoutPage from './pages/CheckoutPage'
import OrderListPage from './pages/OrderListPage'
import OrderDetailPage from './pages/OrderDetailPage'
import ProfilePage from './pages/ProfilePage'
import AddressListPage from './pages/AddressListPage'
import WishlistPage from './pages/WishlistPage'
import NotificationPage from './pages/NotificationPage'
import NotFoundPage from './pages/NotFoundPage'

// Admin pages
import AdminDashboardPage from './pages/admin/AdminDashboardPage'
import AdminUsersPage from './pages/admin/AdminUsersPage'
import AdminOrdersPage from './pages/admin/AdminOrdersPage'
import AdminOrderDetailPage from './pages/admin/AdminOrderDetailPage'
import AdminProductsPage from './pages/admin/AdminProductsPage'
import AdminReviewsPage from './pages/admin/AdminReviewsPage'
import AdminCouponsPage from './pages/admin/AdminCouponsPage'

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1">{children}</main>
      <Footer />
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<Layout><HomePage /></Layout>} />
      <Route path="/products" element={<Layout><ProductListPage /></Layout>} />
      <Route path="/products/:id" element={<Layout><ProductDetailPage /></Layout>} />
      <Route path="/login" element={<Layout><LoginPage /></Layout>} />
      <Route path="/register" element={<Layout><RegisterPage /></Layout>} />

      {/* Protected routes */}
      <Route path="/cart" element={<Layout><RequireAuth><CartPage /></RequireAuth></Layout>} />
      <Route path="/checkout" element={<Layout><RequireAuth><CheckoutPage /></RequireAuth></Layout>} />
      <Route path="/orders" element={<Layout><RequireAuth><OrderListPage /></RequireAuth></Layout>} />
      <Route path="/orders/:id" element={<Layout><RequireAuth><OrderDetailPage /></RequireAuth></Layout>} />
      <Route path="/profile" element={<Layout><RequireAuth><ProfilePage /></RequireAuth></Layout>} />
      <Route path="/addresses" element={<Layout><RequireAuth><AddressListPage /></RequireAuth></Layout>} />
      <Route path="/wishlist" element={<Layout><RequireAuth><WishlistPage /></RequireAuth></Layout>} />
      <Route path="/notifications" element={<Layout><RequireAuth><NotificationPage /></RequireAuth></Layout>} />

      {/* Admin routes */}
      <Route path="/admin" element={<RequireAdmin><AdminDashboardPage /></RequireAdmin>} />
      <Route path="/admin/users" element={<RequireAdmin><AdminUsersPage /></RequireAdmin>} />
      <Route path="/admin/orders" element={<RequireAdmin><AdminOrdersPage /></RequireAdmin>} />
      <Route path="/admin/orders/:id" element={<RequireAdmin><AdminOrderDetailPage /></RequireAdmin>} />
      <Route path="/admin/products" element={<RequireAdmin><AdminProductsPage /></RequireAdmin>} />
      <Route path="/admin/reviews" element={<RequireAdmin><AdminReviewsPage /></RequireAdmin>} />
      <Route path="/admin/coupons" element={<RequireAdmin><AdminCouponsPage /></RequireAdmin>} />

      {/* 404 */}
      <Route path="*" element={<Layout><NotFoundPage /></Layout>} />
    </Routes>
  )
}
