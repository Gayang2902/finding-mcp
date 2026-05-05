import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { Search, Users, Trash2, ToggleLeft, ToggleRight } from 'lucide-react'
import { adminService } from '../../services/adminService'
import { Role } from '../../types'
import { formatDate } from '../../utils/formatters'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import Pagination from '../../components/common/Pagination'
import toast from 'react-hot-toast'

const ROLE_COLORS: Record<Role, string> = {
  [Role.USER]: 'bg-gray-100 text-gray-700',
  [Role.SELLER]: 'bg-blue-100 text-blue-700',
  [Role.ADMIN]: 'bg-red-100 text-red-700',
}

export default function AdminUsersPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery(
    ['admin-users', search, page],
    () => adminService.getUsers({ q: search || undefined, page: page - 1, size: 20 }),
    { keepPreviousData: true }
  )

  const roleUpdate = useMutation(
    ({ id, role }: { id: number; role: Role }) => adminService.updateUserRole(id, role),
    {
      onSuccess: () => { queryClient.invalidateQueries('admin-users'); toast.success('Role updated') },
    }
  )

  const toggle = useMutation(adminService.toggleUserStatus, {
    onSuccess: () => { queryClient.invalidateQueries('admin-users'); toast.success('Status updated') },
  })

  const deleteUser = useMutation(adminService.deleteUser, {
    onSuccess: () => { queryClient.invalidateQueries('admin-users'); toast.success('User deleted') },
  })

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Users</h1>
        <span className="text-sm text-gray-500">{data?.totalElements ?? 0} total users</span>
      </div>

      {/* Search */}
      <div className="relative mb-6 max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          placeholder="Search by name or email…"
          className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner size="lg" />
        </div>
      ) : (
        <>
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    <th className="px-4 py-3 text-left">User</th>
                    <th className="px-4 py-3 text-left">Role</th>
                    <th className="px-4 py-3 text-left">Joined</th>
                    <th className="px-4 py-3 text-left">Status</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data?.content.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="text-center py-12 text-gray-400">
                        <Users className="w-10 h-10 mx-auto mb-2 opacity-40" />
                        <p>No users found</p>
                      </td>
                    </tr>
                  ) : (
                    data?.content.map((user) => (
                      <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3">
                          <p className="text-sm font-medium text-gray-900">{user.firstName} {user.lastName}</p>
                          <p className="text-xs text-gray-500">{user.email}</p>
                        </td>
                        <td className="px-4 py-3">
                          <select
                            value={user.role}
                            onChange={(e) => roleUpdate.mutate({ id: user.id, role: e.target.value as Role })}
                            className={`text-xs font-medium px-2 py-1 rounded-full border-0 cursor-pointer focus:outline-none focus:ring-2 focus:ring-indigo-500 ${ROLE_COLORS[user.role]}`}
                          >
                            {Object.values(Role).map((r) => (
                              <option key={r} value={r}>{r}</option>
                            ))}
                          </select>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500">{formatDate(user.createdAt)}</td>
                        <td className="px-4 py-3">
                          <button
                            onClick={() => toggle.mutate(user.id)}
                            className={`flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded-full ${
                              user.isActive ? 'text-green-700 bg-green-50' : 'text-red-700 bg-red-50'
                            }`}
                          >
                            {user.isActive ? (
                              <><ToggleRight className="w-4 h-4" /> Active</>
                            ) : (
                              <><ToggleLeft className="w-4 h-4" /> Suspended</>
                            )}
                          </button>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => {
                              if (confirm(`Delete user ${user.email}?`)) deleteUser.mutate(user.id)
                            }}
                            className="p-1.5 text-gray-400 hover:text-red-500 transition-colors"
                            title="Delete user"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
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
    </div>
  )
}
