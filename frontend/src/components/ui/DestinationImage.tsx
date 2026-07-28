import { useEffect, useState } from 'react'
import { MapPin } from 'lucide-react'
import { destinationGradient } from '../../lib/constants'
import { getDestinationImageUrl } from '../../lib/destinationImages'

interface DestinationImageProps {
  destination: string
  className?: string
  height?: number
  width?: number
  rounded?: string
}

// Loads a real, location-accurate photo from Wikipedia and falls back to a
// stable, on-brand gradient placeholder if the lookup or image fails.
export function DestinationImage({
  destination,
  className = '',
  height = 250,
  width = 400,
  rounded = 'rounded-t-2xl',
}: DestinationImageProps) {
  const [src, setSrc] = useState<string | null>(null)
  const [loaded, setLoaded] = useState(false)
  const [failed, setFailed] = useState(false)

  const [from, to] = destinationGradient[destination] ?? ['#1B4F72', '#27AE60']

  useEffect(() => {
    let active = true
    setSrc(null)
    setLoaded(false)
    setFailed(false)
    getDestinationImageUrl(destination, width)
      .then((url) => {
        if (!active) return
        if (url) setSrc(url)
        else setFailed(true)
      })
      .catch(() => {
        if (active) setFailed(true)
      })
    return () => {
      active = false
    }
  }, [destination, width])

  return (
    <div
      className={`relative overflow-hidden ${rounded} ${className}`}
      style={{ aspectRatio: `${width} / ${height}` }}
    >
      {/* Gradient placeholder — always present underneath */}
      <div
        className="absolute inset-0 flex flex-col items-center justify-center gap-2"
        style={{ background: `linear-gradient(135deg, ${from}, ${to})` }}
      >
        <MapPin className="h-7 w-7 text-white/80" />
        <span className="font-display text-lg font-semibold text-white drop-shadow">{destination}</span>
      </div>

      {/* Skeleton shimmer while the image loads */}
      {!loaded && !failed && (
        <div className="absolute inset-0 animate-pulse bg-black/10 dark:bg-white/5" />
      )}

      {src && !failed && (
        <img
          src={src}
          alt={destination}
          loading="lazy"
          onLoad={() => setLoaded(true)}
          onError={() => setFailed(true)}
          className={`absolute inset-0 h-full w-full object-cover transition-opacity duration-500 ${
            loaded ? 'opacity-100' : 'opacity-0'
          }`}
        />
      )}
    </div>
  )
}
