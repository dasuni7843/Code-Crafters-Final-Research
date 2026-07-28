import { Building2, Info, Plane, TrendingUp, Users } from 'lucide-react'
import type { DemandForecastResponse } from '../../types'
import { DestinationImage } from '../ui/DestinationImage'
import { Badge } from '../ui/Badge'
import { formatLkr, formatNumber } from '../../lib/constants'

// Visitor split shown as a single horizontal bar. Foreign in ocean, local in
// jungle — the two brand hues, read as one figure split in two.
function SplitBar({ foreign, local }: { foreign: number; local: number }) {
  const total = Math.max(foreign + local, 1)
  const foreignPct = (foreign / total) * 100
  const localPct = 100 - foreignPct
  return (
    <div className="flex h-3 w-full overflow-hidden rounded-full bg-app">
      <div style={{ width: `${foreignPct}%`, backgroundColor: '#2E86C1' }} />
      <div style={{ width: `${localPct}%`, backgroundColor: '#27AE60', marginLeft: 2 }} />
    </div>
  )
}

export function ForecastResult({ plan }: { plan: DemandForecastResponse }) {
  const total = plan.predicted_foreign_visitors + plan.predicted_local_visitors
  const foreignShare = total > 0 ? Math.round((plan.predicted_foreign_visitors / total) * 100) : 0
  const localShare = 100 - foreignShare
  const revenuePerVisitor =
    plan.predicted_tourist_arrivals > 0
      ? Math.round(plan.estimated_revenue_lkr / plan.predicted_tourist_arrivals)
      : 0
  const isActual = plan.data_source === 'actual'
  const longHorizon = plan.forecast_horizon_years >= 3

  return (
    <div className="flex flex-col gap-5">
      {/* Section 1 — Headline */}
      <div className="card overflow-hidden">
        <div className="relative">
          <DestinationImage destination={plan.destination} width={800} height={260} rounded="rounded-t-2xl" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
          <div className="absolute bottom-0 left-0 right-0 flex items-end justify-between gap-4 p-5">
            <div>
              <div className="text-sm font-medium text-white/80">
                {plan.destination} · {plan.month_name} {plan.year}
              </div>
              <div className="mt-1 font-mono text-4xl font-bold leading-none text-white drop-shadow sm:text-5xl">
                {formatNumber(plan.predicted_tourist_arrivals)}
              </div>
              <div className="mt-1 text-sm text-white/85">predicted visitors</div>
              <div className="mt-1 text-xs text-white/75">
                Range: {formatNumber(plan.confidence_lower)} to {formatNumber(plan.confidence_upper)}
              </div>
            </div>
            <Badge tone={isActual ? 'best' : 'info'} className="shrink-0 bg-white/90 dark:bg-white/90">
              {isActual ? 'Actual' : 'Forecast'}
            </Badge>
          </div>
        </div>
        {longHorizon && (
          <p className="flex items-start gap-2 px-5 py-3 text-xs text-muted">
            <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-spice" />
            Forecasts beyond three years carry wider uncertainty and are intended for long range
            planning rather than precise projection.
          </p>
        )}
      </div>

      {/* Section 2 — Visitor breakdown */}
      <div>
        <h3 className="mb-3 font-display text-lg font-semibold text-body">Visitor breakdown</h3>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="card p-5">
            <div className="flex items-center gap-2 text-sm text-muted">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-ocean/10 text-ocean dark:text-ocean-light">
                <Plane className="h-4 w-4" />
              </span>
              Foreign visitors
            </div>
            <div className="mt-2 font-mono text-2xl font-bold text-body">
              {formatNumber(plan.predicted_foreign_visitors)}
            </div>
            <div className="text-xs text-muted">{foreignShare} percent of total</div>
          </div>
          <div className="card p-5">
            <div className="flex items-center gap-2 text-sm text-muted">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-jungle/10 text-jungle-dark dark:text-jungle-light">
                <Users className="h-4 w-4" />
              </span>
              Local visitors
            </div>
            <div className="mt-2 font-mono text-2xl font-bold text-body">
              {formatNumber(plan.predicted_local_visitors)}
            </div>
            <div className="text-xs text-muted">{localShare} percent of total</div>
          </div>
        </div>
        <div className="mt-3">
          <SplitBar foreign={plan.predicted_foreign_visitors} local={plan.predicted_local_visitors} />
          <div className="mt-2 flex items-center gap-4 text-xs text-muted">
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: '#2E86C1' }} /> Foreign
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: '#27AE60' }} /> Local
            </span>
          </div>
        </div>
      </div>

      {/* Section 3 — Revenue */}
      <div>
        <h3 className="mb-3 font-display text-lg font-semibold text-body">Estimated revenue</h3>
        <div className="card p-5">
          <div className="font-mono text-3xl font-bold text-body">{formatLkr(plan.estimated_revenue_lkr)}</div>
          <div className="mt-4 grid gap-4 sm:grid-cols-3">
            <div className="rounded-xl border border-app p-4">
              <div className="text-xs text-muted">Foreign revenue</div>
              <div className="mt-1 font-mono text-lg font-semibold text-body">
                {formatLkr(plan.estimated_foreign_revenue_lkr)}
              </div>
            </div>
            <div className="rounded-xl border border-app p-4">
              <div className="text-xs text-muted">Local revenue</div>
              <div className="mt-1 font-mono text-lg font-semibold text-body">
                {formatLkr(plan.estimated_local_revenue_lkr)}
              </div>
            </div>
            <div className="rounded-xl border border-app p-4">
              <div className="text-xs text-muted">Revenue per visitor</div>
              <div className="mt-1 font-mono text-lg font-semibold text-body">{formatLkr(revenuePerVisitor)}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Section 4 — Model information */}
      <div>
        <h3 className="mb-3 font-display text-lg font-semibold text-body">Model information</h3>
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="card flex items-center gap-3 p-4">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-ocean/10 text-ocean dark:text-ocean-light">
              <TrendingUp className="h-5 w-5" />
            </span>
            <div>
              <div className="font-mono text-lg font-bold text-body">{plan.model_used}</div>
              <div className="text-xs text-muted">Selected model</div>
            </div>
          </div>
          <div className="card flex items-center gap-3 p-4">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-jungle/10 text-jungle-dark dark:text-jungle-light">
              <Info className="h-5 w-5" />
            </span>
            <div>
              <div className="font-mono text-lg font-bold text-body">{plan.mape_pct.toFixed(2)} percent</div>
              <div className="text-xs text-muted">Forecast error (MAPE)</div>
            </div>
          </div>
          <div className="card flex items-center gap-3 p-4">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-spice/10 text-spice-dark dark:text-spice-light">
              <Building2 className="h-5 w-5" />
            </span>
            <div>
              <div className="font-mono text-lg font-bold text-body">{formatNumber(plan.national_arrivals)}</div>
              <div className="text-xs text-muted">National arrivals this month</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
