import { useQuery, useMutation, useQueryClient } from 'react-query'
import { cartService } from '@/services/cartService'
import toast from 'react-hot-toast'

export function useCart() {
  const queryClient = useQueryClient()

  const cartQuery = useQuery('cart', cartService.getCart, {
    retry: false,
  })

  const addItem = useMutation(
    ({ productId, quantity }: { productId: number; quantity: number }) =>
      cartService.addItem({ productId, quantity }),
    {
      onSuccess: (cart) => {
        queryClient.setQueryData('cart', cart)
        toast.success('Added to cart')
      },
    }
  )

  const updateItem = useMutation(
    ({ itemId, quantity }: { itemId: number; quantity: number }) =>
      cartService.updateItem(itemId, quantity),
    {
      onSuccess: (cart) => {
        queryClient.setQueryData('cart', cart)
      },
    }
  )

  const removeItem = useMutation(
    (itemId: number) => cartService.removeItem(itemId),
    {
      onSuccess: (cart) => {
        queryClient.setQueryData('cart', cart)
        toast.success('Item removed')
      },
    }
  )

  const clearCart = useMutation(cartService.clearCart, {
    onSuccess: () => {
      queryClient.invalidateQueries('cart')
    },
  })

  return {
    cart: cartQuery.data,
    isLoading: cartQuery.isLoading,
    addItem: addItem.mutate,
    updateItem: updateItem.mutate,
    removeItem: removeItem.mutate,
    clearCart: clearCart.mutate,
    isAddingItem: addItem.isLoading,
  }
}
