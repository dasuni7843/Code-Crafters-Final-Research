interface ScoreGaugeProps {
  value: number // 0..1
  label?: string
  size?: number
  color?: string
}

export function ScoreGauge({ value, label = 'TSS', size = 132, color = '#27AE60' }: ScoreGaugeProps) {
  const clamped = Math.max(0, Math.min(1, value))
  const stroke = 12
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference * (1 - clamped)

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={stroke}
          className="text-black/10 dark:text-white/10"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.8s ease' }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="font-mono text-2xl font-bold text-body">{Math.round(clamped * 100)}%</span>
        <span className="text-xs text-muted">{label}</span>
      </div>
    </div>
  )
}
