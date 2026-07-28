import type { ReactNode } from 'react'

type Tone = 'best' | 'good' | 'avoid' | 'low' | 'medium' | 'high' | 'neutral' | 'info'

const toneStyles: Record<Tone, string> = {
  best: 'bg-jungle/15 text-jungle-dark dark:text-jungle-light border-jungle/30',
  good: 'bg-ocean/15 text-ocean dark:text-ocean-light border-ocean/30',
  avoid: 'bg-crimson/15 text-crimson dark:text-crimson-light border-crimson/30',
  low: 'bg-jungle/15 text-jungle-dark dark:text-jungle-light border-jungle/30',
  medium: 'bg-spice/15 text-spice-dark dark:text-spice-light border-spice/30',
  high: 'bg-crimson/15 text-crimson dark:text-crimson-light border-crimson/30',
  neutral: 'bg-black/5 dark:bg-white/10 text-muted border-app',
  info: 'bg-ocean-light/15 text-ocean dark:text-ocean-light border-ocean/30',
}

export function toneForSuitability(label: string): Tone {
  if (label === 'BEST') return 'best'
  if (label === 'GOOD') return 'good'
  if (label === 'AVOID') return 'avoid'
  return 'neutral'
}

export function toneForWeather(verdict: string): Tone {
  if (verdict === 'Excellent') return 'best'
  if (verdict === 'Good') return 'good'
  if (verdict === 'Fair') return 'medium'
  if (verdict === 'Poor') return 'avoid'
  return 'neutral'
}

export function toneForCrowd(level: string): Tone {
  if (level === 'LOW') return 'low'
  if (level === 'MEDIUM') return 'medium'
  if (level === 'HIGH') return 'high'
  return 'neutral'
}

interface BadgeProps {
  tone?: Tone
  children: ReactNode
  className?: string
  icon?: ReactNode
}

export function Badge({ tone = 'neutral', children, className = '', icon }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold ${toneStyles[tone]} ${className}`}
    >
      {icon}
      {children}
    </span>
  )
}
