import { Link } from 'react-router-dom'
import { ChevronRight, Home } from 'lucide-react'
import { clsx } from 'clsx'

interface BreadcrumbItem {
  label: string
  to?: string
}

interface BreadcrumbProps {
  items: BreadcrumbItem[]
  showHome?: boolean
  className?: string
}

export default function Breadcrumb({ items, showHome = true, className }: BreadcrumbProps) {
  return (
    <nav className={clsx('flex items-center gap-1 text-sm', className)} aria-label="Breadcrumb">
      {showHome && (
        <>
          <Link to="/" className="text-gray-400 hover:text-indigo-600 transition-colors" aria-label="Home">
            <Home className="h-4 w-4" />
          </Link>
          {items.length > 0 && <ChevronRight className="h-3.5 w-3.5 text-gray-300 flex-shrink-0" />}
        </>
      )}
      {items.map((item, i) => (
        <span key={i} className="flex items-center gap-1">
          {i > 0 && <ChevronRight className="h-3.5 w-3.5 text-gray-300 flex-shrink-0" />}
          {item.to ? (
            <Link to={item.to} className="text-gray-500 hover:text-indigo-600 transition-colors">
              {item.label}
            </Link>
          ) : (
            <span className="text-gray-900 font-medium" aria-current="page">
              {item.label}
            </span>
          )}
        </span>
      ))}
    </nav>
  )
}
