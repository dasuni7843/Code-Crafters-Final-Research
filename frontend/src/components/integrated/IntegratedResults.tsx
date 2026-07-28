import { BarChart3, Leaf, Target, Users } from 'lucide-react'
import type { IntegratedResponse } from '../../types'
import { Badge, toneForCrowd, toneForSuitability } from '../ui/Badge'
import { crowdLabel, formatLkr, suitabilityLabel, toPercent } from '../../lib/constants'

function StepHeader({
  index,
  icon,
  module,
  title,
  source,
}: {
  index: number
  icon: React.ReactNode
  module: string
  title: string
  source?: string
}) {
  return (
    <div className="flex items-center gap-3">
      <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-ocean text-white">{icon}</span>
      <div>
        <div className="text-xs font-semibold uppercase tracking-wide text-muted">
          Step {index} · {module}
        </div>
        <div className="font-display text-lg font-semibold text-body">{title}</div>
        {source && <div className="text-xs text-muted">{source}</div>}
      </div>
    </div>
  )
}

export function IntegratedPipelineSteps({ data }: { data: IntegratedResponse }) {
  const finalDests = new Set(data.module4.map((r) => r.destination))

  return (
    <div className="flex flex-col gap-4">
      {/* Step 1 — Module 1 */}
      <div className="card border-l-4 border-l-spice p-5">
        <StepHeader index={1} icon={<BarChart3 className="h-5 w-5" />} module="Module 1" title="Demand forecast" source="This system · SARIMA demand forecast with linear regression revenue" />
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[520px] text-sm">
            <thead>
              <tr className="text-left text-xs uppercase text-muted">
                <th className="pb-2">Destination</th>
                <th className="pb-2 text-right">Predicted arrivals</th>
                <th className="pb-2 text-right">Foreign</th>
                <th className="pb-2 text-right">Local</th>
                <th className="pb-2 text-right">Estimated revenue</th>
              </tr>
            </thead>
            <tbody>
              {data.module1.slice(0, 6).map((m) => (
                <tr key={m.destination} className={`border-t border-app ${finalDests.has(m.destination) ? 'font-semibold text-body' : 'text-muted'}`}>
                  <td className="py-1.5">{m.destination}</td>
                  <td className="py-1.5 text-right font-mono">{m.predicted_arrivals.toLocaleString('en-US')}</td>
                  <td className="py-1.5 text-right font-mono">{m.predicted_foreign_visitors.toLocaleString('en-US')}</td>
                  <td className="py-1.5 text-right font-mono">{m.predicted_local_visitors.toLocaleString('en-US')}</td>
                  <td className="py-1.5 text-right font-mono">{formatLkr(m.estimated_revenue_lkr)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Step 2 — Module 2 */}
      <div className="card border-l-4 border-l-jungle p-5">
        <StepHeader index={2} icon={<Leaf className="h-5 w-5" />} module="Module 2" title="Seasonal planning" source="This system · RandomForest + XGBoost" />
        <div className="mt-4 grid gap-2 sm:grid-cols-2">
          {data.module2.slice(0, 8).map((m) => (
            <div key={m.destination} className="rounded-lg border border-app px-3 py-2">
              <div className="flex items-center justify-between gap-2">
                <span className={`text-sm ${finalDests.has(m.destination) ? 'font-semibold text-body' : 'text-muted'}`}>{m.destination}</span>
                <div className="flex shrink-0 items-center gap-2">
                  <span className="font-mono text-sm text-body">{toPercent(m.travel_suitability_score)}</span>
                  <Badge tone={toneForSuitability(m.suitability_label)}>{suitabilityLabel(m.suitability_label)}</Badge>
                </div>
              </div>
              <div className="mt-1 flex flex-wrap items-center gap-x-2 text-xs text-muted">
                <span>{m.season}</span>
                <span aria-hidden>·</span>
                <span>{m.weather_verdict} weather</span>
              </div>
              {m.recommendation_summary && (
                <p className="mt-1 text-xs leading-relaxed text-muted">{m.recommendation_summary}</p>
              )}
              {m.season_reason && (
                <p className="mt-1 text-xs leading-relaxed text-muted">
                  <span className="font-semibold text-body">
                    {m.suitability_label === 'AVOID' ? 'Why to avoid' : 'What holds it back'}:
                  </span>{' '}
                  <span className="first-letter:uppercase">{m.season_reason}</span>
                </p>
              )}
            </div>
          ))}
        </div>
        <p className="mt-3 text-xs text-muted">
          Seasonal suitability is scored from weather, seasonality, tourism events, public holidays
          and accessibility. Crowd risk is produced separately by Module 3.
        </p>
      </div>

      {/* Step 3 — Module 3 */}
      <div className="card border-l-4 border-l-crimson p-5">
        <StepHeader index={3} icon={<Users className="h-5 w-5" />} module="Module 3" title="Crowd risk" source="Data source: Ensemble model output (mock)" />
        <div className="mt-4 grid gap-2 sm:grid-cols-2">
          {data.module3
            .filter((m) => finalDests.has(m.destination))
            .map((m) => (
              <div key={m.destination} className="flex items-center justify-between rounded-lg border border-app px-3 py-2">
                <span className="text-sm font-semibold text-body">{m.destination}</span>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs text-muted">{m.crowd_score.toFixed(0)} out of 100</span>
                  <Badge tone={toneForCrowd(m.crowd_risk_level)}>{crowdLabel(m.crowd_risk_level)}</Badge>
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* Step 4 — Module 4 heading (cards rendered by page) */}
      <div className="card border-l-4 border-l-ocean p-5">
        <StepHeader index={4} icon={<Target className="h-5 w-5" />} module="Module 4" title="Personalized recommendations" source="This system · final ranking below" />
        <p className="mt-3 text-sm text-muted">
          The final ranking combines the demand forecast, seasonal suitability, crowd risk and content
          similarity. Each card below shows how the four factors contributed to its score.
        </p>
      </div>
    </div>
  )
}
