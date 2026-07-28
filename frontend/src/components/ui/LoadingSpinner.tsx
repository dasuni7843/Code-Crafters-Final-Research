interface LoadingSpinnerProps {
  label?: string
  className?: string
}

export function LoadingSpinner({ label = 'Loading', className = '' }: LoadingSpinnerProps) {
  return (
    <div className={`flex flex-col items-center justify-center gap-3 py-10 ${className}`}>
      <div className="h-9 w-9 animate-spin rounded-full border-[3px] border-ocean/25 border-t-ocean dark:border-ocean-light/25 dark:border-t-ocean-light" />
      <p className="text-sm text-muted">{label}</p>
    </div>
  )
}
