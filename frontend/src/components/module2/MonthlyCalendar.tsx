import { Star } from 'lucide-react'
import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { SeasonalPlanResponse } from '../../types'
import { Badge, toneForSuitability } from '../ui/Badge'
import { DestinationImage } from '../ui/DestinationImage'
import { MONTH_SHORT, suitabilityLabel } from '../../lib/constants'

const labelColor: Record<string, string> = {
  BEST: '#27AE60',
  GOOD: '#2E86C1',
  AVOID: '#C0392B',
}

interface MonthlyCalendarProps {
  months: SeasonalPlanResponse[]
  selectedMonth?: number
  onSelectMonth?: (month: number) => void
}

function ChipRow({
  title,
  months,
  tone,
  emptyText,
  onSelectMonth,
}: {
  title: string
  months: SeasonalPlanResponse[]
  tone: 'best' | 'avoid'
  emptyText: string
  onSelectMonth?: (month: number) => void
}) {
  return (
    <div>
      <p className="mb-2 text-sm font-medium text-body">{title}</p>
      {months.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {months.map((m) =>
            onSelectMonth ? (
              <button
                key={m.month}
                type="button"
                onClick={() => onSelectMonth(m.month)}
                className="rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-ocean"
              >
                <Badge tone={tone}>{m.month_name}</Badge>
              </button>
            ) : (
              <Badge key={m.month} tone={tone}>{m.month_name}</Badge>
            ),
          )}
        </div>
      ) : (
        <p className="text-sm text-muted">{emptyText}</p>
      )}
    </div>
  )
}

export function MonthlyCalendar({ months, selectedMonth, onSelectMonth }: MonthlyCalendarProps) {
  const destination = months[0]?.destination ?? ''
  const chartData = months.map((m) => ({
    month: MONTH_SHORT[m.month - 1],
    tss: Math.round(m.travel_suitability_score * 100),
    label: m.suitability_label,
  }))

  const bestMonths = months.filter((m) => m.suitability_label === 'BEST')
  const avoidMonths = months.filter((m) => m.suitability_label === 'AVOID')

  return (
    <div className="flex flex-col gap-5">
      <div className="card overflow-hidden">
        <DestinationImage destination={destination} width={800} height={220} rounded="rounded-none" />
        <div className="p-5">
          <h2 className="font-display text-2xl font-bold text-body">{destination}</h2>
          <p className="text-sm text-muted">Year at a glance · suitability by month</p>
        </div>
      </div>

      <div className="card p-5">
        <h3 className="mb-1 font-display text-lg font-semibold text-body">Month by month</h3>
        <p className="mb-4 text-sm text-muted">Select any month to see its full seasonal plan.</p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {months.map((m) => {
            const isSelected = m.month === selectedMonth
            return (
              <button
                key={m.month}
                type="button"
                onClick={() => onSelectMonth?.(m.month)}
                aria-pressed={isSelected}
                className={`relative rounded-xl border p-3 text-left transition hover:border-ocean focus:outline-none focus-visible:ring-2 focus-visible:ring-ocean ${
                  isSelected ? 'border-ocean ring-2 ring-ocean' : 'border-app'
                }`}
                style={{ borderLeft: `4px solid ${labelColor[m.suitability_label]}` }}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-body">{m.month_name}</span>
                  {m.is_best_period && <Star className="h-4 w-4 fill-spice text-spice" />}
                </div>
                <div className="mt-1 font-mono text-lg font-bold text-body">
                  {Math.round(m.travel_suitability_score * 100)}%
                </div>
                <div className="mt-2">
                  <Badge tone={toneForSuitability(m.suitability_label)}>
                    {suitabilityLabel(m.suitability_label)}
                  </Badge>
                </div>
              </button>
            )
          })}
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-muted">
          <span className="flex items-center gap-1.5">
            <Star className="h-3.5 w-3.5 fill-spice text-spice" /> Best period for this destination
          </span>
        </div>
      </div>

      <div className="card p-5">
        <h3 className="mb-4 font-display text-lg font-semibold text-body">Planning summary</h3>
        <div className="grid gap-5 sm:grid-cols-2">
          <ChipRow
            title="Best months to visit"
            months={bestMonths}
            tone="best"
            emptyText="No month scores as a best period for this destination."
            onSelectMonth={onSelectMonth}
          />
          <ChipRow
            title="Months to avoid"
            months={avoidMonths}
            tone="avoid"
            emptyText="No month is flagged as one to avoid."
            onSelectMonth={onSelectMonth}
          />
        </div>
      </div>

      <div className="card p-5">
        <h3 className="mb-4 font-display text-lg font-semibold text-body">Suitability score by month</h3>
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -18, bottom: 0 }}>
              <XAxis dataKey="month" tick={{ fontSize: 12, fill: 'var(--color-muted)' }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 12, fill: 'var(--color-muted)' }} axisLine={false} tickLine={false} />
              <Tooltip
                cursor={{ fill: 'rgba(0,0,0,0.04)' }}
                contentStyle={{
                  background: 'var(--color-card)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 12,
                  color: 'var(--color-text)',
                }}
                formatter={(v: number) => [`${v}%`, 'Suitability']}
              />
              <Bar dataKey="tss" radius={[6, 6, 0, 0]}>
                {chartData.map((d, i) => (
                  <Cell key={i} fill={labelColor[d.label]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
