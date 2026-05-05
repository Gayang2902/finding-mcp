import { useState } from 'react'
import StarRating from '../common/StarRating'
import Input from '../common/Input'
import TextArea from '../common/TextArea'
import Button from '../common/Button'
import Alert from '../common/Alert'

interface ReviewFormProps {
  productId: number
  onSubmit: (data: { rating: number; title: string; body: string }) => Promise<void>
}

interface FormErrors {
  rating?: string
  title?: string
  body?: string
}

export default function ReviewForm({ productId: _productId, onSubmit }: ReviewFormProps) {
  const [rating, setRating] = useState(0)
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [errors, setErrors] = useState<FormErrors>({})
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)

  function validate(): boolean {
    const newErrors: FormErrors = {}
    if (rating === 0) newErrors.rating = 'Please select a rating'
    if (!title.trim()) newErrors.title = 'Title is required'
    else if (title.trim().length < 3) newErrors.title = 'Title must be at least 3 characters'
    if (!body.trim()) newErrors.body = 'Review is required'
    else if (body.trim().length < 10) newErrors.body = 'Review must be at least 10 characters'
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!validate()) return
    setSubmitting(true)
    try {
      await onSubmit({ rating, title: title.trim(), body: body.trim() })
      setSuccess(true)
      setRating(0)
      setTitle('')
      setBody('')
      setErrors({})
    } catch {
      setErrors({ body: 'Failed to submit review. Please try again.' })
    } finally {
      setSubmitting(false)
    }
  }

  if (success) {
    return (
      <Alert
        type="success"
        title="Review submitted!"
        message="Thank you for your review. It will be visible after moderation."
        dismissible
      />
    )
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm space-y-4">
      <h3 className="text-base font-semibold text-gray-900">Write a Review</h3>

      {/* Star rating */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1.5">Your Rating</label>
        <StarRating
          rating={rating}
          interactive
          onChange={setRating}
          size="lg"
        />
        {errors.rating && <p className="text-xs text-red-500 mt-1">{errors.rating}</p>}
      </div>

      <Input
        label="Review Title"
        placeholder="Summarize your experience"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        error={errors.title}
        maxLength={100}
      />

      <TextArea
        label="Your Review"
        placeholder="Share details of your experience with this product..."
        value={body}
        onChange={(e) => setBody(e.target.value)}
        error={errors.body}
        rows={5}
        showCharCount
        maxLength={2000}
      />

      <Button type="submit" loading={submitting} fullWidth>
        Submit Review
      </Button>
    </form>
  )
}
