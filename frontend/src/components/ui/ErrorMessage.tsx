import { AlertTriangle, RefreshCw } from 'lucide-react'

interface ErrorMessageProps {
  message: string
  onRetry?: () => void
  className?: string
}

export function ErrorMessage({ message, onRetry, className = '' }: ErrorMessageProps) {
  return (
    <div
      className={`flex flex-col items-center gap-3 rounded-xl border border-crimson/30 bg-crimson/10 px-6 py-8 text-center ${className}`}
    >
      <AlertTriangle className="h-8 w-8 text-crimson" />
      <p className="max-w-md text-sm font-medium text-crimson dark:text-crimson-light">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-1 inline-flex items-center gap-2 rounded-lg border border-crimson/40 px-4 py-2 text-sm font-semibold text-crimson transition hover:bg-crimson/10 dark:text-crimson-light"
        >
          <RefreshCw className="h-4 w-4" />
          Try again
        </button>
      )}
    </div>
  )
}
