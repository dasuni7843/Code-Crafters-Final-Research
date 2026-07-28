import type { ReactNode } from 'react'

interface MetricCardProps {
  label: string
  value: string
  icon?: ReactNode
  hint?: string
  accent?: 'ocean' | 'jungle' | 'spice' | 'crimson'
}

const accentBg: Record<NonNullable<MetricCardProps['accent']>, string> = {
  ocean: 'bg-ocean/10 text-ocean dark:text-ocean-light',
  jungle: 'bg-jungle/10 text-jungle-dark dark:text-jungle-light',
  spice: 'bg-spice/10 text-spice-dark dark:text-spice-light',
  crimson: 'bg-crimson/10 text-crimson dark:text-crimson-light',
}

export function MetricCard({ label, value, icon, hint, accent = 'ocean' }: MetricCardProps) {
  return (
    <div className="card flex items-center gap-4 p-5 shadow-sm">
      {icon && (
        <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${accentBg[accent]}`}>
          {icon}
        </div>
      )}
      <div className="min-w-0">
        <div className="font-mono text-2xl font-bold text-body">{value}</div>
        <div className="truncate text-sm text-muted">{label}</div>
        {hint && <div className="mt-0.5 truncate text-xs text-muted">{hint}</div>}
      </div>
    </div>
  )
}
