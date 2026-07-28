import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { ArrowDownRight, ArrowUpRight, TrendingUp, Wallet } from 'lucide-react'
import type { DemandForecastResponse } from '../../types'
import {
  formatCountCompact,
  formatLkr,
  formatLkrCompact,
  formatNumber,
  MONTH_SHORT,
} from '../../lib/constants'

const OCEAN = '#2E86C1'
const SPICE = '#E67E22'

interface TooltipRow {
  label: string
  value: string
}

// Shared tooltip styled to the card surface so it reads in light and dark alike.
function ChartTooltip({ title, rows }: { title: string; rows: TooltipRow[] }) {
  return (
    <div className="rounded-xl border border-app bg-card px-3 py-2 shadow-lg">
      <div className="mb-1 text-xs font-semibold text-body">{title}</div>
      {rows.map((r) => (
        <div key={r.label} className="flex items-center justify-between gap-4 text-xs">
          <span className="text-muted">{r.label}</span>
          <span className="font-mono text-body">{r.value}</span>
        </div>
      ))}
    </div>
  )
}

export function YearlyForecast({ months }: { months: DemandForecastResponse[] }) {
  const data = months.map((m) => ({
    month: MONTH_SHORT[m.month - 1],
    monthFull: m.month_name,
    arrivals: m.predicted_tourist_arrivals,
    band: [m.confidence_lower, m.confidence_upper] as [number, number],
    revenue: m.estimated_revenue_lkr,
  }))

  const totalArrivals = months.reduce((s, m) => s + m.predicted_tourist_arrivals, 0)
  const totalRevenue = months.reduce((s, m) => s + m.estimated_revenue_lkr, 0)
  const peak = months.reduce((a, b) =>
    b.predicted_tourist_arrivals > a.predicted_tourist_arrivals ? b : a,
  )
  const lowest = months.reduce((a, b) =>
    b.predicted_tourist_arrivals < a.predicted_tourist_arrivals ? b : a,
  )
  const year = months[0]?.year

  const axisTick = { fontSize: 12, fill: 'var(--color-muted)' }

  return (
    <div className="flex flex-col gap-6">
      {/* Summary strip */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div className="card p-4">
          <div className="flex items-center gap-2 text-xs text-muted">
            <TrendingUp className="h-4 w-4 text-ocean" /> Annual arrivals
          </div>
          <div className="mt-1 font-mono text-xl font-bold text-body">{formatNumber(totalArrivals)}</div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-2 text-xs text-muted">
            <Wallet className="h-4 w-4 text-spice" /> Annual revenue
          </div>
          <div className="mt-1 font-mono text-xl font-bold text-body">{formatLkrCompact(totalRevenue)}</div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-2 text-xs text-muted">
            <ArrowUpRight className="h-4 w-4 text-jungle-dark dark:text-jungle-light" /> Peak month
          </div>
          <div className="mt-1 font-display text-xl font-semibold text-body">{peak.month_name}</div>
          <div className="text-xs text-muted">{formatNumber(peak.predicted_tourist_arrivals)} visitors</div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-2 text-xs text-muted">
            <ArrowDownRight className="h-4 w-4 text-crimson dark:text-crimson-light" /> Lowest month
          </div>
          <div className="mt-1 font-display text-xl font-semibold text-body">{lowest.month_name}</div>
          <div className="text-xs text-muted">{formatNumber(lowest.predicted_tourist_arrivals)} visitors</div>
        </div>
      </div>

      {/* Arrivals line with confidence band */}
      <div className="card p-5">
        <h3 className="mb-1 font-display text-lg font-semibold text-body">Predicted arrivals across {year}</h3>
        <p className="mb-4 text-xs text-muted">
          Monthly visitors with the shaded forecast confidence range around each point.
        </p>
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
              <XAxis dataKey="month" tick={axisTick} tickLine={false} axisLine={{ stroke: 'var(--color-border)' }} />
              <YAxis
                tick={axisTick}
                tickLine={false}
                axisLine={false}
                width={44}
                tickFormatter={formatCountCompact}
              />
              <Tooltip
                cursor={{ stroke: 'var(--color-border)' }}
                content={({ active, payload }) => {
                  if (!active || !payload || !payload.length) return null
                  const p = payload[0].payload as (typeof data)[number]
                  return (
                    <ChartTooltip
                      title={p.monthFull}
                      rows={[
                        { label: 'Arrivals', value: formatNumber(p.arrivals) },
                        { label: 'Range', value: `${formatNumber(p.band[0])} to ${formatNumber(p.band[1])}` },
                      ]}
                    />
                  )
                }}
              />
              <Area
                dataKey="band"
                stroke="none"
                fill={OCEAN}
                fillOpacity={0.14}
                isAnimationActive={false}
                activeDot={false}
              />
              <Line
                dataKey="arrivals"
                stroke={OCEAN}
                strokeWidth={2}
                dot={{ r: 3, fill: OCEAN, strokeWidth: 0 }}
                activeDot={{ r: 5 }}
                isAnimationActive={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Revenue bars */}
      <div className="card p-5">
        <h3 className="mb-1 font-display text-lg font-semibold text-body">Estimated revenue by month</h3>
        <p className="mb-4 text-xs text-muted">Monthly tourism revenue in Sri Lankan rupees.</p>
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
              <XAxis dataKey="month" tick={axisTick} tickLine={false} axisLine={{ stroke: 'var(--color-border)' }} />
              <YAxis
                tick={axisTick}
                tickLine={false}
                axisLine={false}
                width={56}
                tickFormatter={formatLkrCompact}
              />
              <Tooltip
                cursor={{ fill: 'var(--color-border)', fillOpacity: 0.25 }}
                content={({ active, payload }) => {
                  if (!active || !payload || !payload.length) return null
                  const p = payload[0].payload as (typeof data)[number]
                  return (
                    <ChartTooltip
                      title={p.monthFull}
                      rows={[{ label: 'Revenue', value: formatLkr(p.revenue) }]}
                    />
                  )
                }}
              />
              <Bar dataKey="revenue" fill={SPICE} radius={[4, 4, 0, 0]} maxBarSize={38} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
