import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Search, Filter, SlidersHorizontal, X } from 'lucide-react'
import { useProducts, useCategories } from '../hooks/useProducts'
import { useDebounce } from '../hooks/useDebounce'
import { ProductCard } from '../components/product/ProductCard'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Pagination from '../components/common/Pagination'
import EmptyState from '../components/common/EmptyState'
import { ProductSearchParams } from '../types'

const SORT_OPTIONS = [
  { value: 'createdAt-desc', label: 'Newest' },
  { value: 'price-asc', label: 'Price: Low to High' },
  { value: 'price-desc', label: 'Price: High to Low' },
  { value: 'averageRating-desc', label: 'Top Rated' },
  { value: 'name-asc', label: 'Name A–Z' },
]

export default function ProductListPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const [search, setSearch] = useState(searchParams.get('q') ?? '')
  const [sortKey, setSortKey] = useState('createdAt-desc')
  const [categoryId, setCategoryId] = useState<number | undefined>(
    searchParams.get('categoryId') ? Number(searchParams.get('categoryId')) : undefined
  )
  const [minPrice, setMinPrice] = useState('')
  const [maxPrice, setMaxPrice] = useState('')
  const [page, setPage] = useState(1)

  const debouncedSearch = useDebounce(search, 400)
  const { data: categories } = useCategories()

  const [sortBy, sortDir] = sortKey.split('-') as [string, 'asc' | 'desc']

  const params: ProductSearchParams = {
    q: debouncedSearch || undefined,
    categoryId,
    minPrice: minPrice ? Number(minPrice) : undefined,
    maxPrice: maxPrice ? Number(maxPrice) : undefined,
    sortBy,
    sortDir,
    page: page - 1,
    size: 12,
  }

  const { data, isLoading, isFetching } = useProducts(params)

  // Sync URL params
  useEffect(() => {
    const p: Record<string, string> = {}
    if (debouncedSearch) p.q = debouncedSearch
    if (categoryId) p.categoryId = String(categoryId)
    setSearchParams(p, { replace: true })
  }, [debouncedSearch, categoryId, setSearchParams])

  const clearFilters = () => {
    setSearch('')
    setCategoryId(undefined)
    setMinPrice('')
    setMaxPrice('')
    setSortKey('createdAt-desc')
    setPage(1)
  }

  const hasFilters = !!(debouncedSearch || categoryId || minPrice || maxPrice)

  const Filters = () => (
    <div className="space-y-6">
      {/* Category */}
      <div>
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Category</h3>
        <div className="space-y-1.5">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="category"
              checked={!categoryId}
              onChange={() => { setCategoryId(undefined); setPage(1) }}
              className="accent-indigo-600"
            />
            <span className="text-sm text-gray-700">All</span>
          </label>
          {categories?.map((cat) => (
            <label key={cat.id} className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="category"
                checked={categoryId === cat.id}
                onChange={() => { setCategoryId(cat.id); setPage(1) }}
                className="accent-indigo-600"
              />
              <span className="text-sm text-gray-700">{cat.name}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Price range */}
      <div>
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Price Range</h3>
        <div className="flex gap-2">
          <input
            type="number"
            placeholder="Min"
            value={minPrice}
            onChange={(e) => { setMinPrice(e.target.value); setPage(1) }}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            min="0"
          />
          <span className="self-center text-gray-400">–</span>
          <input
            type="number"
            placeholder="Max"
            value={maxPrice}
            onChange={(e) => { setMaxPrice(e.target.value); setPage(1) }}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            min="0"
          />
        </div>
      </div>

      {hasFilters && (
        <button
          onClick={clearFilters}
          className="flex items-center gap-1 text-sm text-red-500 hover:text-red-600"
        >
          <X className="w-4 h-4" /> Clear filters
        </button>
      )}
    </div>
  )

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Products</h1>
        {data && (
          <p className="text-sm text-gray-500">{data.totalElements} item{data.totalElements !== 1 ? 's' : ''} found</p>
        )}
      </div>

      {/* Search + sort bar */}
      <div className="flex gap-3 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            placeholder="Search products…"
            className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <select
          value={sortKey}
          onChange={(e) => { setSortKey(e.target.value); setPage(1) }}
          className="rounded-lg border border-gray-300 px-3 py-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <button
          onClick={() => setSidebarOpen(true)}
          className="lg:hidden flex items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-2.5 text-sm bg-white"
        >
          <SlidersHorizontal className="w-4 h-4" />
          Filters
        </button>
      </div>

      <div className="flex gap-8">
        {/* Desktop sidebar */}
        <aside className="hidden lg:block w-56 flex-shrink-0">
          <div className="bg-white rounded-xl border border-gray-200 p-5 sticky top-24">
            <div className="flex items-center gap-2 mb-5">
              <Filter className="w-4 h-4 text-gray-500" />
              <span className="text-sm font-semibold text-gray-900">Filters</span>
            </div>
            <Filters />
          </div>
        </aside>

        {/* Mobile sidebar */}
        {sidebarOpen && (
          <div className="fixed inset-0 z-40 flex lg:hidden">
            <div className="absolute inset-0 bg-black/40" onClick={() => setSidebarOpen(false)} />
            <div className="relative w-72 bg-white h-full shadow-xl p-6 overflow-y-auto">
              <div className="flex items-center justify-between mb-6">
                <h2 className="font-semibold text-gray-900">Filters</h2>
                <button onClick={() => setSidebarOpen(false)}>
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>
              <Filters />
            </div>
          </div>
        )}

        {/* Product grid */}
        <div className="flex-1 min-w-0">
          {isLoading || isFetching ? (
            <div className="flex justify-center py-20">
              <LoadingSpinner size="lg" />
            </div>
          ) : data?.content.length === 0 ? (
            <EmptyState
              icon={<Search className="w-10 h-10" />}
              title="No products found"
              description="Try adjusting your search or filters."
              actionLabel="Clear filters"
              onAction={clearFilters}
            />
          ) : (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-4">
                {data?.content.map((product) => (
                  <ProductCard key={product.id} product={product} />
                ))}
              </div>
              {data && data.totalPages > 1 && (
                <div className="mt-8">
                  <Pagination
                    page={page}
                    totalPages={data.totalPages}
                    onPageChange={setPage}
                  />
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
