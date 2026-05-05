import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { useForm } from 'react-hook-form'
import { Plus, Trash2, Edit2, Search, Package } from 'lucide-react'
import { productService } from '../../services/productService'
import { Product } from '../../types'
import { formatCurrency, formatDate } from '../../utils/formatters'
import Modal from '../../components/common/Modal'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import Pagination from '../../components/common/Pagination'
import toast from 'react-hot-toast'

interface ProductForm {
  name: string
  description: string
  price: number
  compareAtPrice?: number
  stock: number
  sku: string
  categoryId: number
  imageUrl?: string
}

export default function AdminProductsPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [modalOpen, setModalOpen] = useState(false)
  const [editProduct, setEditProduct] = useState<Product | null>(null)

  const { data, isLoading } = useQuery(
    ['admin-products', search, page],
    () => productService.getProducts({ q: search || undefined, page: page - 1, size: 20 }),
    { keepPreviousData: true }
  )

  const { data: categories } = useQuery('categories', productService.getCategories)

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<ProductForm>()

  const createMutation = useMutation(productService.createProduct, {
    onSuccess: () => {
      queryClient.invalidateQueries('admin-products')
      toast.success('Product created')
      setModalOpen(false)
      reset()
    },
  })

  const updateMutation = useMutation(
    ({ id, data }: { id: number; data: Partial<Product> }) => productService.updateProduct(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('admin-products')
        toast.success('Product updated')
        setModalOpen(false)
        setEditProduct(null)
        reset()
      },
    }
  )

  const deleteMutation = useMutation(productService.deleteProduct, {
    onSuccess: () => {
      queryClient.invalidateQueries('admin-products')
      toast.success('Product deleted')
    },
  })

  const openCreate = () => {
    setEditProduct(null)
    reset({})
    setModalOpen(true)
  }

  const openEdit = (product: Product) => {
    setEditProduct(product)
    reset({
      name: product.name,
      description: product.description,
      price: product.price,
      compareAtPrice: product.compareAtPrice,
      stock: product.stock,
      sku: product.sku,
      categoryId: product.categoryId,
      imageUrl: product.imageUrl ?? '',
    })
    setModalOpen(true)
  }

  const onSubmit = (data: ProductForm) => {
    if (editProduct) {
      updateMutation.mutate({ id: editProduct.id, data })
    } else {
      createMutation.mutate(data)
    }
  }

  const FIELD = (err: boolean) =>
    `w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 ${err ? 'border-red-400' : 'border-gray-300'}`

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Products</h1>
        <button
          onClick={openCreate}
          className="flex items-center gap-2 bg-indigo-600 text-white font-medium px-4 py-2 rounded-lg hover:bg-indigo-700 text-sm"
        >
          <Plus className="w-4 h-4" /> Add Product
        </button>
      </div>

      <div className="relative mb-6 max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          placeholder="Search products…"
          className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16"><LoadingSpinner size="lg" /></div>
      ) : (
        <>
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    <th className="px-4 py-3 text-left">Product</th>
                    <th className="px-4 py-3 text-left">Category</th>
                    <th className="px-4 py-3 text-left">Price</th>
                    <th className="px-4 py-3 text-left">Stock</th>
                    <th className="px-4 py-3 text-left">Seller</th>
                    <th className="px-4 py-3 text-left">Created</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data?.content.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-12 text-gray-400">
                        <Package className="w-10 h-10 mx-auto mb-2 opacity-40" />
                        <p>No products found</p>
                      </td>
                    </tr>
                  ) : (
                    data?.content.map((product) => (
                      <tr key={product.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-gray-100 rounded-lg flex-shrink-0 overflow-hidden">
                              {product.imageUrl
                                ? <img src={product.imageUrl} alt="" className="w-full h-full object-cover" />
                                : <Package className="w-5 h-5 text-gray-300 m-auto mt-2.5" />
                              }
                            </div>
                            <div>
                              <p className="text-sm font-medium text-gray-900 max-w-[200px] truncate">{product.name}</p>
                              <p className="text-xs text-gray-400">{product.sku}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">{product.category?.name ?? '—'}</td>
                        <td className="px-4 py-3">
                          <p className="text-sm font-semibold">{formatCurrency(product.price)}</p>
                          {product.compareAtPrice && (
                            <p className="text-xs text-gray-400 line-through">{formatCurrency(product.compareAtPrice)}</p>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`text-sm font-medium ${product.stock === 0 ? 'text-red-600' : product.stock < 10 ? 'text-yellow-600' : 'text-green-600'}`}>
                            {product.stock}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500">
                          {product.seller ? `${product.seller.firstName} ${product.seller.lastName}` : '—'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-400">{formatDate(product.createdAt)}</td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <button onClick={() => openEdit(product)} className="p-1.5 text-gray-400 hover:text-indigo-600 transition-colors">
                              <Edit2 className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => { if (confirm('Delete this product?')) deleteMutation.mutate(product.id) }}
                              className="p-1.5 text-gray-400 hover:text-red-500 transition-colors"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
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

      <Modal
        open={modalOpen}
        onClose={() => { setModalOpen(false); setEditProduct(null); reset() }}
        title={editProduct ? 'Edit Product' : 'Add Product'}
        size="lg"
      >
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
            <input type="text" className={FIELD(!!errors.name)} {...register('name', { required: 'Required' })} />
            {errors.name && <p className="text-xs text-red-500 mt-1">{errors.name.message}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description *</label>
            <textarea rows={3} className={FIELD(!!errors.description)} {...register('description', { required: 'Required' })} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Price *</label>
              <input type="number" step="0.01" min="0" className={FIELD(!!errors.price)} {...register('price', { required: 'Required', min: 0 })} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Compare-at Price</label>
              <input type="number" step="0.01" min="0" className={FIELD(false)} {...register('compareAtPrice')} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Stock *</label>
              <input type="number" min="0" className={FIELD(!!errors.stock)} {...register('stock', { required: 'Required', min: 0 })} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">SKU *</label>
              <input type="text" className={FIELD(!!errors.sku)} {...register('sku', { required: 'Required' })} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
              <select className={FIELD(false)} {...register('categoryId', { valueAsNumber: true })}>
                <option value="">Select…</option>
                {categories?.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Image URL</label>
              <input type="url" className={FIELD(false)} {...register('imageUrl')} />
            </div>
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={() => { setModalOpen(false); reset() }} className="flex-1 border border-gray-200 text-gray-700 font-medium py-2.5 rounded-lg hover:bg-gray-50">Cancel</button>
            <button type="submit" disabled={isSubmitting} className="flex-1 bg-indigo-600 text-white font-medium py-2.5 rounded-lg hover:bg-indigo-700 disabled:opacity-50">
              {isSubmitting ? 'Saving…' : editProduct ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
