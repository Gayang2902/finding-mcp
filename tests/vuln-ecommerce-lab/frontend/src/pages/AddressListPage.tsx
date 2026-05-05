import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { MapPin, Plus, Trash2, Edit2, Star } from 'lucide-react'
import { addressService } from '../services/addressService'
import { Address, AddressRequest } from '../types'
import Modal from '../components/common/Modal'
import LoadingSpinner from '../components/common/LoadingSpinner'
import toast from 'react-hot-toast'

export default function AddressListPage() {
  const queryClient = useQueryClient()
  const [modalOpen, setModalOpen] = useState(false)
  const [editAddress, setEditAddress] = useState<Address | null>(null)

  const { data: addresses, isLoading } = useQuery('addresses', addressService.getAddresses)

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<AddressRequest>()

  const addMutation = useMutation(addressService.addAddress, {
    onSuccess: () => {
      queryClient.invalidateQueries('addresses')
      toast.success('Address added')
      setModalOpen(false)
      reset()
    },
  })

  const updateMutation = useMutation(
    ({ id, data }: { id: number; data: AddressRequest }) => addressService.updateAddress(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('addresses')
        toast.success('Address updated')
        setModalOpen(false)
        setEditAddress(null)
        reset()
      },
    }
  )

  const deleteMutation = useMutation(addressService.deleteAddress, {
    onSuccess: () => {
      queryClient.invalidateQueries('addresses')
      toast.success('Address deleted')
    },
  })

  const setDefaultMutation = useMutation(addressService.setDefault, {
    onSuccess: () => {
      queryClient.invalidateQueries('addresses')
      toast.success('Default address updated')
    },
  })

  const openAdd = () => {
    setEditAddress(null)
    reset({})
    setModalOpen(true)
  }

  const openEdit = (addr: Address) => {
    setEditAddress(addr)
    reset({
      recipientName: addr.recipientName,
      street: addr.street,
      city: addr.city,
      state: addr.state,
      postalCode: addr.postalCode,
      country: addr.country,
      phone: addr.phone ?? '',
      label: addr.label ?? '',
    })
    setModalOpen(true)
  }

  const onSubmit = (data: AddressRequest) => {
    if (editAddress) {
      updateMutation.mutate({ id: editAddress.id, data })
    } else {
      addMutation.mutate(data)
    }
  }

  const FIELD_CLASS = (hasError: boolean) =>
    `w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 ${hasError ? 'border-red-400' : 'border-gray-300'}`

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">My Addresses</h1>
        <button
          onClick={openAdd}
          className="flex items-center gap-2 bg-indigo-600 text-white font-medium px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors text-sm"
        >
          <Plus className="w-4 h-4" /> Add Address
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner size="lg" />
        </div>
      ) : addresses?.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
          <MapPin className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-gray-900 mb-1">No addresses yet</h3>
          <p className="text-sm text-gray-500 mb-4">Add a shipping address to place orders.</p>
          <button onClick={openAdd} className="text-indigo-600 text-sm font-medium">
            + Add Address
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {addresses?.map((addr: Address) => (
            <div
              key={addr.id}
              className={`bg-white rounded-xl border-2 p-5 relative ${addr.isDefault ? 'border-indigo-400' : 'border-gray-200'}`}
            >
              {addr.isDefault && (
                <span className="absolute top-3 right-3 flex items-center gap-1 text-xs text-indigo-600 font-medium bg-indigo-50 px-2 py-0.5 rounded-full">
                  <Star className="w-3 h-3" /> Default
                </span>
              )}
              {addr.label && (
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">{addr.label}</p>
              )}
              <p className="font-semibold text-gray-900">{addr.recipientName}</p>
              <p className="text-sm text-gray-600 mt-0.5">{addr.street}</p>
              <p className="text-sm text-gray-600">{addr.city}, {addr.state} {addr.postalCode}</p>
              <p className="text-sm text-gray-600">{addr.country}</p>
              {addr.phone && <p className="text-sm text-gray-500 mt-0.5">{addr.phone}</p>}

              <div className="flex items-center gap-2 mt-4">
                <button
                  onClick={() => openEdit(addr)}
                  className="flex items-center gap-1 text-xs text-gray-600 hover:text-indigo-600 border border-gray-200 rounded-lg px-2.5 py-1.5 hover:border-indigo-200"
                >
                  <Edit2 className="w-3.5 h-3.5" /> Edit
                </button>
                {!addr.isDefault && (
                  <button
                    onClick={() => setDefaultMutation.mutate(addr.id)}
                    className="text-xs text-gray-600 hover:text-indigo-600 border border-gray-200 rounded-lg px-2.5 py-1.5 hover:border-indigo-200"
                  >
                    Set Default
                  </button>
                )}
                <button
                  onClick={() => {
                    if (confirm('Delete this address?')) deleteMutation.mutate(addr.id)
                  }}
                  className="flex items-center gap-1 text-xs text-red-400 hover:text-red-600 ml-auto"
                >
                  <Trash2 className="w-3.5 h-3.5" /> Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add/Edit Modal */}
      <Modal
        open={modalOpen}
        onClose={() => { setModalOpen(false); setEditAddress(null); reset() }}
        title={editAddress ? 'Edit Address' : 'Add New Address'}
        size="lg"
      >
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Label (optional)</label>
              <input type="text" placeholder="Home, Work…" className={FIELD_CLASS(false)} {...register('label')} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Recipient Name *</label>
              <input type="text" className={FIELD_CLASS(!!errors.recipientName)} {...register('recipientName', { required: 'Required' })} />
              {errors.recipientName && <p className="text-xs text-red-500 mt-1">{errors.recipientName.message}</p>}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Street Address *</label>
            <input type="text" className={FIELD_CLASS(!!errors.street)} {...register('street', { required: 'Required' })} />
            {errors.street && <p className="text-xs text-red-500 mt-1">{errors.street.message}</p>}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">City *</label>
              <input type="text" className={FIELD_CLASS(!!errors.city)} {...register('city', { required: 'Required' })} />
              {errors.city && <p className="text-xs text-red-500 mt-1">{errors.city.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">State *</label>
              <input type="text" className={FIELD_CLASS(!!errors.state)} {...register('state', { required: 'Required' })} />
              {errors.state && <p className="text-xs text-red-500 mt-1">{errors.state.message}</p>}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Postal Code *</label>
              <input type="text" className={FIELD_CLASS(!!errors.postalCode)} {...register('postalCode', { required: 'Required' })} />
              {errors.postalCode && <p className="text-xs text-red-500 mt-1">{errors.postalCode.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Country *</label>
              <input type="text" className={FIELD_CLASS(!!errors.country)} {...register('country', { required: 'Required' })} />
              {errors.country && <p className="text-xs text-red-500 mt-1">{errors.country.message}</p>}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
            <input type="tel" className={FIELD_CLASS(false)} {...register('phone')} />
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input type="checkbox" className="accent-indigo-600" {...register('isDefault')} />
            Set as default address
          </label>
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={() => { setModalOpen(false); reset() }}
              className="flex-1 border border-gray-200 text-gray-700 font-medium py-2.5 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 bg-indigo-600 text-white font-medium py-2.5 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              {isSubmitting ? 'Saving…' : editAddress ? 'Update Address' : 'Add Address'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
