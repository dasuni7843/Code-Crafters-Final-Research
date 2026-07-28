import { useEffect } from 'react'
import { X } from 'lucide-react'
import type { SimilarDestination } from '../../types'
import { DestinationImage } from '../ui/DestinationImage'
import { LoadingSpinner } from '../ui/LoadingSpinner'
import { ErrorMessage } from '../ui/ErrorMessage'
import { toPercent } from '../../lib/constants'

interface SimilarDestinationsProps {
  origin: string
  items: SimilarDestination[] | null
  loading: boolean
  error: string | null
  onClose: () => void
}

export function SimilarDestinations({ origin, items, loading, error, onClose }: SimilarDestinationsProps) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="card w-full max-w-lg overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-app px-5 py-4">
          <div>
            <h3 className="font-display text-lg font-semibold text-body">Similar to {origin}</h3>
            <p className="text-xs text-muted">Ranked by content similarity</p>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-muted hover:bg-black/5 dark:hover:bg-white/10">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="max-h-[70vh] overflow-y-auto p-5">
          {loading && <LoadingSpinner label="Finding similar destinations" />}
          {error && <ErrorMessage message={error} />}
          {items && items.length === 0 && (
            <p className="py-6 text-center text-sm text-muted">No similar destinations found.</p>
          )}
          {items && items.length > 0 && (
            <div className="flex flex-col gap-3">
              {items.map((s) => (
                <div key={s.destination} className="flex items-center gap-4 rounded-xl border border-app p-3">
                  <div className="w-24 shrink-0">
                    <DestinationImage destination={s.destination} width={200} height={140} rounded="rounded-lg" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-body">{s.destination}</p>
                    <p className="text-xs capitalize text-muted">
                      {s.dest_type} · {s.district}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="font-mono text-lg font-bold text-jungle-dark dark:text-jungle-light">
                      {toPercent(s.similarity_score)}
                    </div>
                    <div className="text-xs text-muted">match</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
