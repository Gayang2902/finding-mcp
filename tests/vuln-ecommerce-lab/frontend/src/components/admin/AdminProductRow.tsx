import { Link } from 'react-router-dom'
import { Pencil, Trash2, Package } from 'lucide-react'
import { Product } from '../../types'
import Button from '../common/Button'
import PriceDisplay from '../common/PriceDisplay'
import Badge from '../common/Badge'

interface AdminProductRowProps {
  product: Product
  onEdit?: (product: Product) => void
  onDelete?: (productId: number) => void
}

export default function AdminProductRow({ product, onEdit, onDelete }: AdminProductRowProps) {
  const stockVariant = product.stock === 0 ? 'danger' : product.stock < 10 ? 'warning' : 'success'
  const stockLabel = product.stock === 0 ? 'Out of stock' : product.stock < 10 ? `Low (${product.stock})` : `In stock (${product.stock})`

  return (
    <tr className="hover:bg-gray-50 transition-colors">
      {/* Product */}
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-lg overflow-hidden bg-gray-100 flex-shrink-0">
            {product.imageUrl ? (
              <img src={product.imageUrl} alt={product.name} className="h-full w-full object-cover" />
            ) : (
              <div className="h-full w-full flex items-center justify-center text-gray-300">
                <Package className="h-5 w-5" />
              </div>
            )}
          </div>
          <div className="min-w-0">
            <Link
              to={`/products/${product.id}`}
              className="text-sm font-medium text-gray-800 hover:text-indigo-600 transition-colors line-clamp-1"
            >
              {product.name}
            </Link>
            <p className="text-xs text-gray-400 mt-0.5">{product.sku}</p>
          </div>
        </div>
      </td>

      {/* Seller */}
      <td className="px-4 py-3">
        {product.seller ? (
          <p className="text-xs text-gray-600 truncate max-w-[140px]">
            {product.seller.firstName} {product.seller.lastName}
          </p>
        ) : (
          <span className="text-xs text-gray-400">—</span>
        )}
      </td>

      {/* Stock */}
      <td className="px-4 py-3">
        <Badge variant={stockVariant} size="sm">{stockLabel}</Badge>
      </td>

      {/* Price */}
      <td className="px-4 py-3">
        <PriceDisplay price={product.price} compareAtPrice={product.compareAtPrice} size="sm" />
      </td>

      {/* Actions */}
      <td className="px-4 py-3">
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="sm" onClick={() => onEdit?.(product)}>
            <Pencil className="h-3.5 w-3.5" />
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onDelete?.(product.id)} className="text-red-500 hover:bg-red-50">
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </td>
    </tr>
  )
}
