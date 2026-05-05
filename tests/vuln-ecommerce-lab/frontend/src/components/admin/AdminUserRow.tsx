import { format } from 'date-fns'
import { Pencil, Trash2 } from 'lucide-react'
import { User, Role } from '../../types'
import Button from '../common/Button'

interface AdminUserRowProps {
  user: User
  onRoleChange?: (userId: number, role: Role) => void
  onToggleActive?: (userId: number, isActive: boolean) => void
  onEdit?: (user: User) => void
  onDelete?: (userId: number) => void
}

export default function AdminUserRow({ user, onRoleChange, onToggleActive, onEdit, onDelete }: AdminUserRowProps) {
  return (
    <tr className="hover:bg-gray-50 transition-colors">
      {/* User info */}
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 text-xs font-bold flex-shrink-0">
            {user.firstName.charAt(0)}{user.lastName.charAt(0)}
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-gray-800 truncate">
              {user.firstName} {user.lastName}
            </p>
            <p className="text-xs text-gray-400 truncate max-w-[180px]">{user.email}</p>
          </div>
        </div>
      </td>

      {/* Joined */}
      <td className="px-4 py-3">
        <span className="text-xs text-gray-500">{format(new Date(user.createdAt), 'MMM d, yyyy')}</span>
      </td>

      {/* Role */}
      <td className="px-4 py-3">
        <select
          value={user.role}
          onChange={(e) => onRoleChange?.(user.id, e.target.value as Role)}
          className="rounded-lg border border-gray-200 px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
          onClick={(e) => e.stopPropagation()}
        >
          {Object.values(Role).map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
      </td>

      {/* Active toggle */}
      <td className="px-4 py-3">
        <button
          onClick={() => onToggleActive?.(user.id, !user.isActive)}
          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
            user.isActive ? 'bg-green-500' : 'bg-gray-300'
          }`}
          aria-label={user.isActive ? 'Disable user' : 'Enable user'}
        >
          <span
            className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${
              user.isActive ? 'translate-x-4.5' : 'translate-x-0.5'
            }`}
          />
        </button>
      </td>

      {/* Actions */}
      <td className="px-4 py-3">
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="sm" onClick={() => onEdit?.(user)}>
            <Pencil className="h-3.5 w-3.5" />
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onDelete?.(user.id)} className="text-red-500 hover:bg-red-50">
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </td>
    </tr>
  )
}
