import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight, ShoppingBag, Shield, Truck, RefreshCw, Star } from 'lucide-react'
import { useTopRatedProducts, useCategories } from '../hooks/useProducts'
import { ProductCard } from '../components/product/ProductCard'
import LoadingSpinner from '../components/common/LoadingSpinner'

const HERO_CATEGORIES = [
  { name: 'Electronics', slug: 'electronics', color: 'bg-blue-100 text-blue-700', emoji: '💻' },
  { name: 'Clothing', slug: 'clothing', color: 'bg-pink-100 text-pink-700', emoji: '👗' },
  { name: 'Books', slug: 'books', color: 'bg-yellow-100 text-yellow-700', emoji: '📚' },
  { name: 'Home & Garden', slug: 'home', color: 'bg-green-100 text-green-700', emoji: '🏡' },
  { name: 'Sports', slug: 'sports', color: 'bg-orange-100 text-orange-700', emoji: '⚽' },
  { name: 'Toys', slug: 'toys', color: 'bg-purple-100 text-purple-700', emoji: '🧸' },
]

const FEATURES = [
  { icon: Truck, title: 'Free Shipping', desc: 'On all orders over $50' },
  { icon: Shield, title: 'Secure Payments', desc: 'Your data is safe with us' },
  { icon: RefreshCw, title: 'Easy Returns', desc: '30-day hassle-free returns' },
  { icon: Star, title: 'Top Quality', desc: 'Handpicked products' },
]

export default function HomePage() {
  const { data: topProducts, isLoading } = useTopRatedProducts(8)
  const { data: categories } = useCategories()
  const navigate = useNavigate()

  return (
    <div>
      {/* Hero */}
      <section className="bg-gradient-to-br from-indigo-600 via-indigo-700 to-purple-700 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 flex flex-col lg:flex-row items-center gap-12">
          <div className="flex-1 text-center lg:text-left">
            <span className="inline-block bg-white/20 text-white text-xs font-semibold px-3 py-1 rounded-full mb-4 uppercase tracking-wider">
              Security Research Lab
            </span>
            <h1 className="text-4xl sm:text-5xl font-extrabold leading-tight mb-4">
              Welcome to <span className="text-yellow-300">VulnShop</span>
            </h1>
            <p className="text-indigo-200 text-lg mb-8 max-w-xl mx-auto lg:mx-0">
              An intentionally vulnerable e-commerce platform. Browse products, place orders, and discover security vulnerabilities in a safe lab environment.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center lg:justify-start">
              <Link
                to="/products"
                className="inline-flex items-center gap-2 bg-white text-indigo-700 font-semibold px-6 py-3 rounded-lg hover:bg-indigo-50 transition-colors"
              >
                <ShoppingBag className="w-5 h-5" />
                Shop Now
              </Link>
              <Link
                to="/register"
                className="inline-flex items-center gap-2 border-2 border-white text-white font-semibold px-6 py-3 rounded-lg hover:bg-white/10 transition-colors"
              >
                Create Account
                <ArrowRight className="w-5 h-5" />
              </Link>
            </div>
          </div>
          <div className="hidden lg:flex flex-1 justify-center">
            <div className="relative w-80 h-80">
              <div className="absolute inset-0 bg-white/10 rounded-3xl backdrop-blur-sm border border-white/20 flex items-center justify-center">
                <ShoppingBag className="w-40 h-40 text-white/40" />
              </div>
              <div className="absolute -top-4 -right-4 bg-yellow-400 text-yellow-900 rounded-2xl px-4 py-2 font-bold text-sm shadow-lg">
                Intentionally Vulnerable
              </div>
              <div className="absolute -bottom-4 -left-4 bg-white text-indigo-700 rounded-2xl px-4 py-2 font-bold text-sm shadow-lg">
                For Security Research
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature badges */}
      <section className="bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 grid grid-cols-2 md:grid-cols-4 gap-6">
          {FEATURES.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="flex items-center gap-3">
              <div className="flex-shrink-0 w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center">
                <Icon className="w-5 h-5 text-indigo-600" />
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-900">{title}</p>
                <p className="text-xs text-gray-500">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Categories */}
      <section className="bg-gray-50 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Shop by Category</h2>
            <Link to="/products" className="text-indigo-600 hover:text-indigo-700 text-sm font-medium flex items-center gap-1">
              All products <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
            {(categories?.length ? categories.slice(0, 6) : HERO_CATEGORIES).map((cat) => (
              <button
                key={cat.slug ?? cat.name}
                onClick={() => navigate(`/products?category=${cat.slug}`)}
                className="flex flex-col items-center gap-2 p-4 bg-white rounded-xl border border-gray-200 hover:border-indigo-300 hover:shadow-sm transition-all"
              >
                <span className="text-2xl">{'emoji' in cat ? cat.emoji : '🛍️'}</span>
                <span className="text-xs font-medium text-gray-700 text-center">{cat.name}</span>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Top rated products */}
      <section className="py-12 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Top Rated Products</h2>
            <Link to="/products?sortBy=rating&sortDir=desc" className="text-indigo-600 hover:text-indigo-700 text-sm font-medium flex items-center gap-1">
              View all <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          {isLoading ? (
            <div className="flex justify-center py-12">
              <LoadingSpinner size="lg" />
            </div>
          ) : topProducts && topProducts.length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
              {topProducts.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <ShoppingBag className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p>No products yet. Be the first to list one!</p>
            </div>
          )}
        </div>
      </section>

      {/* Promo banners */}
      <section className="py-12 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-gradient-to-r from-orange-400 to-pink-500 rounded-2xl p-8 text-white">
            <p className="text-sm font-semibold uppercase tracking-wider opacity-80 mb-2">Limited Time</p>
            <h3 className="text-2xl font-bold mb-2">Summer Sale</h3>
            <p className="opacity-90 mb-4">Up to 50% off on selected items. Use code SUMMER50.</p>
            <Link to="/products" className="inline-flex items-center gap-1 bg-white text-orange-600 font-semibold px-4 py-2 rounded-lg text-sm hover:bg-orange-50">
              Shop Sale <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="bg-gradient-to-r from-teal-500 to-cyan-600 rounded-2xl p-8 text-white">
            <p className="text-sm font-semibold uppercase tracking-wider opacity-80 mb-2">New Arrivals</p>
            <h3 className="text-2xl font-bold mb-2">Fresh Collection</h3>
            <p className="opacity-90 mb-4">Discover the latest products just added to our catalog.</p>
            <Link to="/products?sortBy=createdAt&sortDir=desc" className="inline-flex items-center gap-1 bg-white text-teal-600 font-semibold px-4 py-2 rounded-lg text-sm hover:bg-teal-50">
              View New <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
