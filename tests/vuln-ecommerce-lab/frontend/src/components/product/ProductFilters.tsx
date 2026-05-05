import { useState } from 'react'
import { ChevronDown, ChevronUp, SlidersHorizontal, X } from 'lucide-react'
import { clsx } from 'clsx'
import { Category } from '../../types'
import Button from '../common/Button'
import StarRating from '../common/StarRating'

export interface FilterState {
  categoryIds: number[]
  minPrice: string
  maxPrice: string
  sortBy: string
  minRating: number
  inStockOnly: boolean
}

interface ProductFiltersProps {
  categories: Category[]
  filters: FilterState
  onChange: (filters: FilterState) => void
  onClear: () => void
}

const sortOptions = [
  { value: '', label: 'Relevance' },
  { value: 'price_asc', label: 'Price: Low to High' },
  { value: 'price_desc', label: 'Price: High to Low' },
  { value: 'rating_desc', label: 'Highest Rated' },
  { value: 'newest', label: 'Newest' },
]

export default function ProductFilters({ categories, filters, onChange, onClear }: ProductFiltersProps) {
  const [categoriesExpanded, setCategoriesExpanded] = useState(true)
  const [mobileOpen, setMobileOpen] = useState(false)

  function toggleCategory(id: number) {
    const next = filters.categoryIds.includes(id)
      ? filters.categoryIds.filter((c) => c !== id)
      : [...filters.categoryIds, id]
    onChange({ ...filters, categoryIds: next })
  }

  const hasActiveFilters =
    filters.categoryIds.length > 0 ||
    filters.minPrice !== '' ||
    filters.maxPrice !== '' ||
    filters.minRating > 0 ||
    filters.inStockOnly

  const filterPanel = (
    <div className="space-y-6">
      {/* Sort */}
      <div>
        <label className="block text-sm font-semibold text-gray-800 mb-2">Sort By</label>
        <select
          value={filters.sortBy}
          onChange={(e) => onChange({ ...filters, sortBy: e.target.value })}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          {sortOptions.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      {/* Categories */}
      <div>
        <button
          onClick={() => setCategoriesExpanded((v) => !v)}
          className="flex w-full items-center justify-between text-sm font-semibold text-gray-800 mb-2"
        >
          Categories
          {categoriesExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
        {categoriesExpanded && (
          <div className="space-y-1.5 max-h-48 overflow-y-auto">
            {categories.map((cat) => (
              <label key={cat.id} className="flex items-center gap-2 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={filters.categoryIds.includes(cat.id)}
                  onChange={() => toggleCategory(cat.id)}
                  className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-sm text-gray-700 group-hover:text-indigo-600 transition-colors">
                  {cat.name}
                </span>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Price range */}
      <div>
        <p className="text-sm font-semibold text-gray-800 mb-2">Price Range</p>
        <div className="flex items-center gap-2">
          <input
            type="number"
            placeholder="Min"
            value={filters.minPrice}
            onChange={(e) => onChange({ ...filters, minPrice: e.target.value })}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            min={0}
          />
          <span className="text-gray-400 flex-shrink-0">–</span>
          <input
            type="number"
            placeholder="Max"
            value={filters.maxPrice}
            onChange={(e) => onChange({ ...filters, maxPrice: e.target.value })}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            min={0}
          />
        </div>
      </div>

      {/* Min rating */}
      <div>
        <p className="text-sm font-semibold text-gray-800 mb-2">Minimum Rating</p>
        <StarRating
          rating={filters.minRating}
          interactive
          onChange={(r) => onChange({ ...filters, minRating: r === filters.minRating ? 0 : r })}
          size="md"
        />
      </div>

      {/* In stock only */}
      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={filters.inStockOnly}
          onChange={(e) => onChange({ ...filters, inStockOnly: e.target.checked })}
          className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
        />
        <span className="text-sm text-gray-700">In stock only</span>
      </label>

      {/* Clear */}
      {hasActiveFilters && (
        <Button variant="ghost" size="sm" onClick={onClear} fullWidth>
          <X className="h-4 w-4" /> Clear all filters
        </Button>
      )}
    </div>
  )

  return (
    <>
      {/* Mobile trigger */}
      <div className="lg:hidden">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setMobileOpen(true)}
          iconLeft={<SlidersHorizontal className="h-4 w-4" />}
        >
          Filters {hasActiveFilters && `(${filters.categoryIds.length + (filters.minRating > 0 ? 1 : 0) + (filters.inStockOnly ? 1 : 0)})`}
        </Button>

        {mobileOpen && (
          <div className="fixed inset-0 z-50 flex">
            <div className="absolute inset-0 bg-black/40" onClick={() => setMobileOpen(false)} />
            <div className="relative ml-auto w-72 bg-white h-full overflow-y-auto p-6 shadow-xl">
              <div className="flex items-center justify-between mb-6">
                <h2 className="font-semibold text-gray-900">Filters</h2>
                <button onClick={() => setMobileOpen(false)} className="text-gray-400 hover:text-gray-600">
                  <X className="h-5 w-5" />
                </button>
              </div>
              {filterPanel}
            </div>
          </div>
        )}
      </div>

      {/* Desktop sidebar */}
      <aside className="hidden lg:block w-56 flex-shrink-0">
        <div className="sticky top-20">
          <h2 className="font-semibold text-gray-900 mb-4">Filters</h2>
          {filterPanel}
        </div>
      </aside>
    </>
  )
}
