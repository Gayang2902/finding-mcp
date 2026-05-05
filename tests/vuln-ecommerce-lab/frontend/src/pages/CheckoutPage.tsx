import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { Check, MapPin, CreditCard, ShoppingBag, ChevronRight } from 'lucide-react'
import { useCart } from '../hooks/useCart'
import { useQuery } from 'react-query'
import { addressService } from '../services/addressService'
import { orderService } from '../services/orderService'
import { Address, PaymentMethod } from '../types'
import { formatCurrency } from '../utils/formatters'
import LoadingSpinner from '../components/common/LoadingSpinner'
import toast from 'react-hot-toast'

type Step = 'address' | 'payment' | 'review' | 'confirm'

interface PaymentForm {
  cardHolder: string
  cardNumber: string
  cardExpiry: string
  cardCvv: string
}

export default function CheckoutPage() {
  const navigate = useNavigate()
  const { cart } = useCart()
  const [step, setStep] = useState<Step>('address')
  const [selectedAddressId, setSelectedAddressId] = useState<number | null>(null)
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>(PaymentMethod.CREDIT_CARD)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { data: addresses, isLoading: addressesLoading } = useQuery('addresses', addressService.getAddresses)
  const { register, handleSubmit, formState: { errors } } = useForm<PaymentForm>()

  const subtotal = cart?.total ?? 0
  const shipping = subtotal >= 50 ? 0 : 5.99
  const tax = subtotal * 0.08
  const total = subtotal + shipping + tax

  const selectedAddress = addresses?.find((a: Address) => a.id === selectedAddressId)
    ?? addresses?.find((a: Address) => a.isDefault)
    ?? addresses?.[0]

  const STEPS: { key: Step; label: string; icon: React.ReactNode }[] = [
    { key: 'address', label: 'Address', icon: <MapPin className="w-4 h-4" /> },
    { key: 'payment', label: 'Payment', icon: <CreditCard className="w-4 h-4" /> },
    { key: 'review', label: 'Review', icon: <ShoppingBag className="w-4 h-4" /> },
  ]

  const stepIdx = { address: 0, payment: 1, review: 2, confirm: 3 }

  const placeOrder = async () => {
    if (!selectedAddress) {
      toast.error('Please select a shipping address')
      return
    }
    if (!cart?.items.length) {
      toast.error('Your cart is empty')
      return
    }
    setIsSubmitting(true)
    try {
      const order = await orderService.createOrder({
        items: cart.items.map((i) => ({ productId: i.productId, quantity: i.quantity })),
        shippingAddressId: selectedAddress.id,
        paymentMethod,
      })
      navigate(`/orders/${order.id}`)
      toast.success('Order placed successfully!')
    } catch {
      // handled by interceptor
    } finally {
      setIsSubmitting(false)
    }
  }

  if (step === 'confirm') {
    return (
      <div className="max-w-lg mx-auto px-4 py-20 text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <Check className="w-8 h-8 text-green-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Order Placed!</h2>
        <p className="text-gray-500 mb-6">Thank you for your purchase. You'll receive an email confirmation shortly.</p>
        <button onClick={() => navigate('/orders')} className="bg-indigo-600 text-white font-semibold px-6 py-3 rounded-xl hover:bg-indigo-700 transition-colors">
          View Orders
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Checkout</h1>

      {/* Step indicators */}
      <div className="flex items-center mb-8">
        {STEPS.map((s, i) => (
          <div key={s.key} className="flex items-center flex-1 last:flex-none">
            <div className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium ${
              stepIdx[step] >= i
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-500'
            }`}>
              {stepIdx[step] > i ? <Check className="w-4 h-4" /> : s.icon}
              <span className="hidden sm:inline">{s.label}</span>
            </div>
            {i < STEPS.length - 1 && (
              <div className={`flex-1 h-0.5 mx-2 ${stepIdx[step] > i ? 'bg-indigo-600' : 'bg-gray-200'}`} />
            )}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          {/* Step: Address */}
          {step === 'address' && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Shipping Address</h2>
              {addressesLoading ? (
                <LoadingSpinner />
              ) : addresses?.length === 0 ? (
                <div className="text-center py-8">
                  <MapPin className="w-10 h-10 text-gray-300 mx-auto mb-2" />
                  <p className="text-sm text-gray-500 mb-4">No saved addresses. Please add one first.</p>
                  <button onClick={() => navigate('/addresses')} className="text-indigo-600 text-sm font-medium">
                    Add Address
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {addresses?.map((addr: Address) => (
                    <label key={addr.id} className={`flex items-start gap-3 p-4 rounded-xl border-2 cursor-pointer transition-colors ${
                      (selectedAddressId ?? selectedAddress?.id) === addr.id
                        ? 'border-indigo-500 bg-indigo-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}>
                      <input
                        type="radio"
                        name="address"
                        value={addr.id}
                        checked={(selectedAddressId ?? selectedAddress?.id) === addr.id}
                        onChange={() => setSelectedAddressId(addr.id)}
                        className="mt-0.5 accent-indigo-600"
                      />
                      <div className="text-sm">
                        <p className="font-medium text-gray-900">{addr.recipientName}</p>
                        <p className="text-gray-500">{addr.street}</p>
                        <p className="text-gray-500">{addr.city}, {addr.state} {addr.postalCode}</p>
                        <p className="text-gray-500">{addr.country}</p>
                        {addr.isDefault && (
                          <span className="inline-block mt-1 text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full">Default</span>
                        )}
                      </div>
                    </label>
                  ))}
                </div>
              )}
              <button
                onClick={() => setStep('payment')}
                disabled={!selectedAddress}
                className="mt-6 w-full flex items-center justify-center gap-2 bg-indigo-600 text-white font-semibold py-3 rounded-xl hover:bg-indigo-700 disabled:opacity-50 transition-colors"
              >
                Continue to Payment <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Step: Payment */}
          {step === 'payment' && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Payment Method</h2>
              <div className="space-y-3 mb-5">
                {[PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD, PaymentMethod.PAYPAL].map((method) => (
                  <label key={method} className={`flex items-center gap-3 p-4 rounded-xl border-2 cursor-pointer ${
                    paymentMethod === method ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'
                  }`}>
                    <input
                      type="radio"
                      name="payment"
                      value={method}
                      checked={paymentMethod === method}
                      onChange={() => setPaymentMethod(method)}
                      className="accent-indigo-600"
                    />
                    <span className="text-sm font-medium text-gray-900">{method.replace('_', ' ')}</span>
                  </label>
                ))}
              </div>

              {(paymentMethod === PaymentMethod.CREDIT_CARD || paymentMethod === PaymentMethod.DEBIT_CARD) && (
                <form className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Card Holder Name</label>
                    <input
                      type="text"
                      placeholder="John Doe"
                      className={`w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 ${errors.cardHolder ? 'border-red-400' : 'border-gray-300'}`}
                      {...register('cardHolder', { required: 'Required' })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Card Number</label>
                    <input
                      type="text"
                      placeholder="1234 5678 9012 3456"
                      maxLength={19}
                      className={`w-full border rounded-lg px-3 py-2.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500 ${errors.cardNumber ? 'border-red-400' : 'border-gray-300'}`}
                      {...register('cardNumber', { required: 'Required', minLength: 16 })}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Expiry</label>
                      <input
                        type="text"
                        placeholder="MM/YY"
                        maxLength={5}
                        className={`w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 ${errors.cardExpiry ? 'border-red-400' : 'border-gray-300'}`}
                        {...register('cardExpiry', { required: 'Required' })}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">CVV</label>
                      <input
                        type="text"
                        placeholder="123"
                        maxLength={4}
                        className={`w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 ${errors.cardCvv ? 'border-red-400' : 'border-gray-300'}`}
                        {...register('cardCvv', { required: 'Required', minLength: 3 })}
                      />
                    </div>
                  </div>
                  <p className="text-xs text-gray-400">This is a demo app — do not enter real card details.</p>
                </form>
              )}

              <div className="flex gap-3 mt-6">
                <button onClick={() => setStep('address')} className="px-5 py-3 border border-gray-200 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-50">
                  Back
                </button>
                <button
                  onClick={() => setStep('review')}
                  className="flex-1 flex items-center justify-center gap-2 bg-indigo-600 text-white font-semibold py-3 rounded-xl hover:bg-indigo-700 transition-colors"
                >
                  Review Order <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* Step: Review */}
          {step === 'review' && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Review Your Order</h2>
              <div className="space-y-3 mb-6">
                {cart?.items.map((item) => (
                  <div key={item.id} className="flex gap-3">
                    <div className="w-12 h-12 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                      {item.product.imageUrl && (
                        <img src={item.product.imageUrl} alt={item.product.name} className="w-full h-full object-cover" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{item.product.name}</p>
                      <p className="text-xs text-gray-500">Qty: {item.quantity}</p>
                    </div>
                    <p className="text-sm font-bold">{formatCurrency(item.price * item.quantity)}</p>
                  </div>
                ))}
              </div>
              {selectedAddress && (
                <div className="text-sm bg-gray-50 rounded-lg p-3 mb-5">
                  <p className="font-medium text-gray-900 mb-1">Shipping to:</p>
                  <p className="text-gray-600">{selectedAddress.recipientName}, {selectedAddress.street}, {selectedAddress.city}</p>
                </div>
              )}
              <div className="flex gap-3">
                <button onClick={() => setStep('payment')} className="px-5 py-3 border border-gray-200 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-50">
                  Back
                </button>
                <button
                  onClick={placeOrder}
                  disabled={isSubmitting}
                  className="flex-1 flex items-center justify-center gap-2 bg-green-600 text-white font-semibold py-3 rounded-xl hover:bg-green-700 disabled:opacity-60 transition-colors"
                >
                  {isSubmitting ? 'Placing order…' : 'Place Order'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Summary sidebar */}
        <div>
          <div className="bg-white rounded-xl border border-gray-200 p-5 sticky top-24">
            <h2 className="text-sm font-semibold text-gray-900 mb-4">Order Summary</h2>
            <div className="space-y-1.5 text-sm mb-4">
              <div className="flex justify-between">
                <span className="text-gray-500">Subtotal ({cart?.itemCount} items)</span>
                <span>{formatCurrency(subtotal)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Shipping</span>
                <span className={shipping === 0 ? 'text-green-600' : ''}>{shipping === 0 ? 'FREE' : formatCurrency(shipping)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Tax</span>
                <span>{formatCurrency(tax)}</span>
              </div>
              <div className="flex justify-between font-bold border-t pt-2 mt-2">
                <span>Total</span>
                <span>{formatCurrency(total)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
