import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import Sidebar from './Sidebar'
import RequireAuth from './RequireAuth'
import { Role } from '../../types'

interface BreadcrumbItem {
  label: string
  to?: string
}

interface AdminLayoutProps {
  children: React.ReactNode
  breadcrumbs?: BreadcrumbItem[]
}

export default function AdminLayout({ children, breadcrumbs = [] }: AdminLayoutProps) {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()

  // Auto-generate breadcrumbs from path if none provided
  const crumbs: BreadcrumbItem[] = breadcrumbs.length > 0
    ? breadcrumbs
    : location.pathname
        .split('/')
        .filter(Boolean)
        .map((segment, i, arr) => ({
          label: segment.charAt(0).toUpperCase() + segment.slice(1),
          to: i < arr.length - 1 ? '/' + arr.slice(0, i + 1).join('/') : undefined,
        }))

  return (
    <RequireAuth requiredRole={Role.ADMIN}>
      <div className="flex min-h-screen bg-gray-100">
        <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((v) => !v)} />

        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Breadcrumb bar */}
          <header className="bg-white border-b border-gray-200 px-6 py-3">
            <nav className="flex items-center gap-1 text-sm text-gray-500">
              {crumbs.map((crumb, i) => (
                <span key={i} className="flex items-center gap-1">
                  {i > 0 && <ChevronRight className="h-3.5 w-3.5 text-gray-400" />}
                  {crumb.to ? (
                    <Link to={crumb.to} className="hover:text-indigo-600 transition-colors">
                      {crumb.label}
                    </Link>
                  ) : (
                    <span className="text-gray-800 font-medium">{crumb.label}</span>
                  )}
                </span>
              ))}
            </nav>
          </header>

          {/* Main content */}
          <main className="flex-1 overflow-auto p-6">
            {children}
          </main>
        </div>
      </div>
    </RequireAuth>
  )
}
