import api from './api'
import { Address, AddressRequest } from '@/types'

export const addressService = {
  getAddresses: () =>
    api.get<Address[]>('/addresses').then((r) => r.data),

  addAddress: (data: AddressRequest) =>
    api.post<Address>('/addresses', data).then((r) => r.data),

  updateAddress: (id: number, data: AddressRequest) =>
    api.put<Address>(`/addresses/${id}`, data).then((r) => r.data),

  deleteAddress: (id: number) =>
    api.delete(`/addresses/${id}`).then((r) => r.data),

  setDefault: (id: number) =>
    api.post<Address>(`/addresses/${id}/default`).then((r) => r.data),
}
