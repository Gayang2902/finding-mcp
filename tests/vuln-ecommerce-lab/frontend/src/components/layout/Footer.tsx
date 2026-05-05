import { Link } from 'react-router-dom'
import { Twitter, Facebook, Instagram, Youtube, ShoppingBag } from 'lucide-react'

export default function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="bg-gray-900 text-gray-300">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Column 1: Brand */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <ShoppingBag className="h-6 w-6 text-indigo-400" />
              <span className="text-xl font-bold text-white">VulnShop</span>
            </div>
            <p className="text-sm leading-relaxed text-gray-400">
              Your one-stop destination for quality products at unbeatable prices. Shop smart, shop safe.
            </p>
          </div>

          {/* Column 2: Quick Links */}
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-white mb-4">Quick Links</h3>
            <ul className="space-y-2 text-sm">
              <li><Link to="/products" className="hover:text-indigo-400 transition-colors">Shop</Link></li>
              <li><Link to="/about" className="hover:text-indigo-400 transition-colors">About Us</Link></li>
              <li><Link to="/contact" className="hover:text-indigo-400 transition-colors">Contact</Link></li>
              <li><Link to="/blog" className="hover:text-indigo-400 transition-colors">Blog</Link></li>
            </ul>
          </div>

          {/* Column 3: Customer Service */}
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-white mb-4">Customer Service</h3>
            <ul className="space-y-2 text-sm">
              <li><Link to="/faq" className="hover:text-indigo-400 transition-colors">FAQ</Link></li>
              <li><Link to="/shipping" className="hover:text-indigo-400 transition-colors">Shipping Policy</Link></li>
              <li><Link to="/returns" className="hover:text-indigo-400 transition-colors">Returns & Exchanges</Link></li>
              <li><Link to="/orders" className="hover:text-indigo-400 transition-colors">Track Order</Link></li>
            </ul>
          </div>

          {/* Column 4: Connect */}
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-white mb-4">Connect</h3>
            <div className="flex gap-3">
              <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gray-800 p-2 hover:bg-indigo-600 transition-colors" aria-label="Twitter">
                <Twitter className="h-4 w-4" />
              </a>
              <a href="https://facebook.com" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gray-800 p-2 hover:bg-indigo-600 transition-colors" aria-label="Facebook">
                <Facebook className="h-4 w-4" />
              </a>
              <a href="https://instagram.com" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gray-800 p-2 hover:bg-indigo-600 transition-colors" aria-label="Instagram">
                <Instagram className="h-4 w-4" />
              </a>
              <a href="https://youtube.com" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gray-800 p-2 hover:bg-indigo-600 transition-colors" aria-label="YouTube">
                <Youtube className="h-4 w-4" />
              </a>
            </div>
            <p className="mt-4 text-sm text-gray-400">
              Subscribe to our newsletter for deals and updates.
            </p>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-10 border-t border-gray-800 pt-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-gray-500">
          <p>&copy; {currentYear} VulnShop. All rights reserved.</p>
          <div className="flex gap-4">
            <Link to="/privacy" className="hover:text-indigo-400 transition-colors">Privacy Policy</Link>
            <Link to="/terms" className="hover:text-indigo-400 transition-colors">Terms of Service</Link>
            <Link to="/cookies" className="hover:text-indigo-400 transition-colors">Cookie Policy</Link>
          </div>
        </div>
      </div>
    </footer>
  )
}
