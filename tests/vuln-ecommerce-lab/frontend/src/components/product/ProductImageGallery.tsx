import { useState } from 'react'
import { ImageOff, ChevronLeft, ChevronRight } from 'lucide-react'
import { clsx } from 'clsx'

interface ProductImageGalleryProps {
  images?: string[]
  mainImage?: string
  productName: string
}

export default function ProductImageGallery({ images = [], mainImage, productName }: ProductImageGalleryProps) {
  const allImages = mainImage
    ? [mainImage, ...images.filter((img) => img !== mainImage)]
    : images

  const [selectedIndex, setSelectedIndex] = useState(0)
  const [zoomed, setZoomed] = useState(false)
  const [mousePos, setMousePos] = useState({ x: 50, y: 50 })

  const selectedImage = allImages[selectedIndex]

  function handleMouseMove(e: React.MouseEvent<HTMLDivElement>) {
    const rect = e.currentTarget.getBoundingClientRect()
    const x = ((e.clientX - rect.left) / rect.width) * 100
    const y = ((e.clientY - rect.top) / rect.height) * 100
    setMousePos({ x, y })
  }

  function prev() {
    setSelectedIndex((i) => (i - 1 + allImages.length) % allImages.length)
  }

  function next() {
    setSelectedIndex((i) => (i + 1) % allImages.length)
  }

  if (allImages.length === 0) {
    return (
      <div className="flex h-80 w-full items-center justify-center rounded-2xl bg-gray-100 text-gray-300">
        <div className="flex flex-col items-center gap-2">
          <ImageOff className="h-12 w-12" />
          <span className="text-sm">No image available</span>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Main image */}
      <div
        className={clsx(
          'relative aspect-square w-full overflow-hidden rounded-2xl bg-gray-50 cursor-zoom-in',
          zoomed && 'cursor-zoom-out'
        )}
        onMouseEnter={() => setZoomed(true)}
        onMouseLeave={() => setZoomed(false)}
        onMouseMove={handleMouseMove}
      >
        <img
          src={selectedImage}
          alt={`${productName} - image ${selectedIndex + 1}`}
          className={clsx(
            'h-full w-full object-contain transition-transform duration-300',
            zoomed ? 'scale-150' : 'scale-100'
          )}
          style={zoomed ? { transformOrigin: `${mousePos.x}% ${mousePos.y}%` } : undefined}
        />

        {/* Prev/Next arrows */}
        {allImages.length > 1 && (
          <>
            <button
              onClick={prev}
              className="absolute left-2 top-1/2 -translate-y-1/2 rounded-full bg-white/80 p-1.5 shadow hover:bg-white transition-colors"
              aria-label="Previous image"
            >
              <ChevronLeft className="h-4 w-4 text-gray-700" />
            </button>
            <button
              onClick={next}
              className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full bg-white/80 p-1.5 shadow hover:bg-white transition-colors"
              aria-label="Next image"
            >
              <ChevronRight className="h-4 w-4 text-gray-700" />
            </button>
          </>
        )}
      </div>

      {/* Thumbnails */}
      {allImages.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-1">
          {allImages.map((img, i) => (
            <button
              key={i}
              onClick={() => setSelectedIndex(i)}
              className={clsx(
                'flex-shrink-0 h-16 w-16 rounded-lg overflow-hidden border-2 transition-colors',
                i === selectedIndex ? 'border-indigo-500' : 'border-transparent hover:border-gray-300'
              )}
            >
              <img src={img} alt={`Thumbnail ${i + 1}`} className="h-full w-full object-cover" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
