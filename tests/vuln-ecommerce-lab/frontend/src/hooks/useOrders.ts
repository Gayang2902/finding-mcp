import { useQuery } from 'react-query'
import { orderService } from '@/services/orderService'
import { OrderStatus } from '@/types'

export function useMyOrders(status?: OrderStatus) {
  return useQuery(['orders', 'my', status], () => orderService.getMyOrders({ status }))
}

export function useOrder(id: number) {
  return useQuery(['order', id], () => orderService.getOrderById(id), {
    enabled: !!id,
  })
}

export function useAllOrders(status?: OrderStatus) {
  return useQuery(['orders', 'all', status], () => orderService.getAllOrders({ status }))
}
