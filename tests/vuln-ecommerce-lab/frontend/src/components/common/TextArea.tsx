import { forwardRef } from 'react'
import { clsx } from 'clsx'

interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
  rows?: number
  showCharCount?: boolean
  maxLength?: number
  resize?: 'none' | 'both' | 'horizontal' | 'vertical'
}

const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(function TextArea(
  { label, error, rows = 4, showCharCount = false, maxLength, resize = 'vertical', className, id, value, ...props },
  ref
) {
  const areaId = id ?? label?.toLowerCase().replace(/\s+/g, '-')
  const charCount = typeof value === 'string' ? value.length : 0

  const resizeClass = {
    none: 'resize-none',
    both: 'resize',
    horizontal: 'resize-x',
    vertical: 'resize-y',
  }[resize]

  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label htmlFor={areaId} className="text-sm font-medium text-gray-700">
          {label}
        </label>
      )}
      <textarea
        ref={ref}
        id={areaId}
        rows={rows}
        maxLength={maxLength}
        value={value}
        className={clsx(
          'w-full rounded-lg border px-3 py-2 text-sm text-gray-900 placeholder-gray-400',
          'focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
          'disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed',
          resizeClass,
          error ? 'border-red-400 focus:ring-red-400' : 'border-gray-300',
          className
        )}
        {...props}
      />
      <div className="flex justify-between">
        {error ? (
          <p className="text-xs text-red-500">{error}</p>
        ) : (
          <span />
        )}
        {showCharCount && maxLength && (
          <p className="text-xs text-gray-400">
            {charCount}/{maxLength}
          </p>
        )}
      </div>
    </div>
  )
})

export default TextArea
