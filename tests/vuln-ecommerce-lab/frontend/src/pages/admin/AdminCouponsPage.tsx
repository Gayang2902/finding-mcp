import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { useForm } from 'react-hook-form'
import { Tag, Plus, Edit2, ToggleLeft, ToggleRight } from 'lucide-react'
import { couponService } from '../../services/couponService'
import { DiscountType, Coupon } from '../../types'
import { formatCurrency, formatDate } from '../../utils/formatters'
import Modal from '../../components/common/Modal'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import toast from 'react-hot-toast'

interface CouponForm {
  code: string
  description: string
  discountType: DiscountType
  discountValue: number
  minOrderAmount?: number
  maxDiscountAmount?: number
  usageLimit?: number
  expiresAt?: string
  isActive: boolean
}

export default function AdminCouponsPage() {
  const queryClient = useQueryClient()
  const [modalOpen, setModalOpen] = useState(false)
  const [editCoupon, setEditCoupon] = useState<Coupon | null>(null)

  const { data: coupons, isLoading } = useQuery('admin-coupons', couponService.getActiveCoupons)

  const { register, handleSubmit, reset, watch, formState: { errors, isSubmitting } } = useForm<CouponForm>()
  const discountType = watch('discountType', DiscountType.PERCENTAGE)

  const createMutation = useMutation(couponService.createCoupon, {
    onSuccess: () => {
      queryClient.invalidateQueries('admin-coupons')
      toast.success('Coupon created')
      setModalOpen(false)
      reset()
    },
  })

  const updateMutation = useMutation(
    ({ id, data }: { id: number; data: Partial<Coupon> }) => couponService.updateCoupon(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('admin-coupons')
        toast.success('Coupon updated')
        setModalOpen(false)
        setEditCoupon(null)
        reset()
      },
    }
  )

  const openCreate = () => {
    setEditCoupon(null)
    reset({ discountType: DiscountType.PERCENTAGE, isActive: true })
    setModalOpen(true)
  }

  const openEdit = (coupon: Coupon) => {
    setEditCoupon(coupon)
    reset({
      code: coupon.code,
      description: coupon.description ?? '',
      discountType: coupon.discountType,
      discountValue: coupon.discountValue,
      minOrderAmount: coupon.minOrderAmount,
      maxDiscountAmount: coupon.maxDiscountAmount,
      usageLimit: coupon.usageLimit,
      expiresAt: coupon.expiresAt ? coupon.expiresAt.slice(0, 10) : '',
      isActive: coupon.isActive,
    })
    setModalOpen(true)
  }

  const toggleActive = (coupon: Coupon) => {
    updateMutation.mutate({ id: coupon.id, data: { isActive: !coupon.isActive } })
  }

  const onSubmit = (data: CouponForm) => {
    if (editCoupon) {
      updateMutation.mutate({ id: editCoupon.id, data })
    } else {
      createMutation.mutate(data)
    }
  }

  const FIELD = (err: boolean) =>
    `w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 ${err ? 'border-red-400' : 'border-gray-300'}`

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Coupons</h1>
        <button
          onClick={openCreate}
          className="flex items-center gap-2 bg-indigo-600 text-white font-medium px-4 py-2 rounded-lg hover:bg-indigo-700 text-sm"
        >
          <Plus className="w-4 h-4" /> New Coupon
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16"><LoadingSpinner size="lg" /></div>
      ) : !coupons?.length ? (
        <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
          <Tag className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No coupons yet</p>
          <button onClick={openCreate} className="mt-3 text-indigo-600 text-sm font-medium">Create one</button>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  <th className="px-4 py-3 text-left">Code</th>
                  <th className="px-4 py-3 text-left">Discount</th>
                  <th className="px-4 py-3 text-left">Min Order</th>
                  <th className="px-4 py-3 text-left">Usage</th>
                  <th className="px-4 py-3 text-left">Expires</th>
                  <th className="px-4 py-3 text-left">Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {coupons.map((coupon) => (
                  <tr key={coupon.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3">
                      <p className="text-sm font-bold font-mono text-indigo-600">{coupon.code}</p>
                      {coupon.description && <p className="text-xs text-gray-400">{coupon.description}</p>}
                    </td>
                    <td className="px-4 py-3 text-sm font-medium">
                      {coupon.discountType === DiscountType.PERCENTAGE
                        ? `${coupon.discountValue}%`
                        : formatCurrency(coupon.discountValue)
                      }
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {coupon.minOrderAmount ? formatCurrency(coupon.minOrderAmount) : '—'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {coupon.usageCount}{coupon.usageLimit ? ` / ${coupon.usageLimit}` : ''}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {coupon.expiresAt ? formatDate(coupon.expiresAt) : 'Never'}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => toggleActive(coupon)}
                        className={`flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full ${
                          coupon.isActive ? 'text-green-700 bg-green-50' : 'text-gray-500 bg-gray-100'
                        }`}
                      >
                        {coupon.isActive
                          ? <><ToggleRight className="w-4 h-4" /> Active</>
                          : <><ToggleLeft className="w-4 h-4" /> Inactive</>
                        }
                      </button>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => openEdit(coupon)}
                        className="p-1.5 text-gray-400 hover:text-indigo-600 transition-colors"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <Modal
        open={modalOpen}
        onClose={() => { setModalOpen(false); setEditCoupon(null); reset() }}
        title={editCoupon ? 'Edit Coupon' : 'New Coupon'}
        size="lg"
      >
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Code *</label>
              <input
                type="text"
                placeholder="SUMMER50"
                className={FIELD(!!errors.code)}
                style={{ textTransform: 'uppercase' }}
                {...register('code', { required: 'Required' })}
              />
              {errors.code && <p className="text-xs text-red-500 mt-1">{errors.code.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <input type="text" className={FIELD(false)} {...register('description')} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Discount Type *</label>
              <select className={FIELD(false)} {...register('discountType', { required: true })}>
                <option value={DiscountType.PERCENTAGE}>Percentage (%)</option>
                <option value={DiscountType.FIXED}>Fixed Amount ($)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Discount Value * {discountType === DiscountType.PERCENTAGE ? '(%)' : '($)'}
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                className={FIELD(!!errors.discountValue)}
                {...register('discountValue', { required: 'Required', min: 0 })}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Min Order Amount</label>
              <input type="number" step="0.01" min="0" className={FIELD(false)} {...register('minOrderAmount')} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Max Discount ($)</label>
              <input type="number" step="0.01" min="0" className={FIELD(false)} {...register('maxDiscountAmount')} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Usage Limit</label>
              <input type="number" min="1" className={FIELD(false)} {...register('usageLimit')} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Expiry Date</label>
              <input type="date" className={FIELD(false)} {...register('expiresAt')} />
            </div>
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input type="checkbox" className="accent-indigo-600" {...register('isActive')} />
            Active
          </label>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={() => { setModalOpen(false); reset() }} className="flex-1 border border-gray-200 text-gray-700 font-medium py-2.5 rounded-lg hover:bg-gray-50">Cancel</button>
            <button type="submit" disabled={isSubmitting} className="flex-1 bg-indigo-600 text-white font-medium py-2.5 rounded-lg hover:bg-indigo-700 disabled:opacity-50">
              {isSubmitting ? 'Saving…' : editCoupon ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
