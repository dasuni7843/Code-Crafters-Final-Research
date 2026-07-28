import {
  AlertTriangle,
  Backpack,
  CalendarCheck,
  CloudRain,
  CloudSun,
  Droplets,
  Gauge,
  Info,
  Compass,
  PartyPopper,
  Sun,
  Thermometer,
  Umbrella,
  Users,
  Waves,
} from 'lucide-react'
import type { SeasonalPlanResponse } from '../../types'
import { Badge, toneForCrowd, toneForSuitability } from '../ui/Badge'
import { DestinationImage } from '../ui/DestinationImage'
import { ScoreGauge } from '../ui/ScoreGauge'
import {
  SCORE_COMPONENT_LABELS,
  SCORE_COMPONENT_WEIGHTS,
  crowdLabel,
  suitabilityLabel,
} from '../../lib/constants'

const gaugeColor = (label: string) =>
  label === 'BEST' ? '#27AE60' : label === 'GOOD' ? '#2E86C1' : '#C0392B'

const componentColor: Record<string, string> = {
  weather_component: '#2E86C1',
  season_component: '#27AE60',
  event_component: '#E67E22',
  holiday_component: '#8E44AD',
  accessibility_component: '#16A085',
}

const verdictColor = (verdict: string) => {
  switch (verdict) {
    case 'Excellent':
      return 'text-jungle'
    case 'Good':
      return 'text-ocean'
    case 'Fair':
      return 'text-spice'
    default:
      return 'text-crimson'
  }
}

const rainRiskTone = (risk: string) => {
  if (risk === 'Low') return 'low'
  if (risk === 'Moderate') return 'medium'
  return 'high'
}

function StatCard({
  icon,
  label,
  value,
  accent,
}: {
  icon: React.ReactNode
  label: string
  value: string
  accent?: string
}) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-app bg-app px-3 py-2.5">
      <div className={accent ?? 'text-ocean dark:text-ocean-light'}>{icon}</div>
      <div className="min-w-0">
        <div className="font-mono text-sm font-semibold text-body">{value}</div>
        <div className="truncate text-xs text-muted">{label}</div>
      </div>
    </div>
  )
}

function PlanningCard({
  icon,
  title,
  items,
}: {
  icon: React.ReactNode
  title: string
  items: string[]
}) {
  return (
    <div className="card p-5">
      <div className="mb-3 flex items-center gap-2">
        <span className="text-ocean dark:text-ocean-light">{icon}</span>
        <h3 className="font-semibold text-body">{title}</h3>
      </div>
      {items.length > 0 ? (
        <ul className="space-y-2">
          {items.map((item) => (
            <li key={item} className="flex gap-2 text-sm text-muted">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-ocean" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted">Nothing specific to flag for this month.</p>
      )}
    </div>
  )
}

/** Section 2 — how the suitability score is composed. */
function ScoreBreakdownPanel({ plan }: { plan: SeasonalPlanResponse }) {
  const entries = Object.entries(plan.score_breakdown) as [string, number][]
  const total = entries.reduce((sum, [, v]) => sum + v, 0)

  return (
    <div className="card p-5">
      <h3 className="font-display text-lg font-semibold text-body">How this score is calculated</h3>
      <p className="mt-1 text-sm text-muted">
        Each factor contributes a weighted share of the overall suitability score.
      </p>

      <div className="mt-4 flex h-3 w-full overflow-hidden rounded-full bg-black/5 dark:bg-white/10">
        {entries.map(([key, value]) => (
          <div
            key={key}
            style={{
              width: total > 0 ? `${(value / total) * 100}%` : '0%',
              backgroundColor: componentColor[key],
            }}
            title={`${SCORE_COMPONENT_LABELS[key]}: ${Math.round(value * 100)} points`}
          />
        ))}
      </div>

      <dl className="mt-4 space-y-3">
        {entries.map(([key, value]) => (
          <div key={key} className="flex items-center gap-3">
            <dt className="w-28 shrink-0 text-sm text-muted">{SCORE_COMPONENT_LABELS[key]}</dt>
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-black/5 dark:bg-white/10">
              <div
                className="h-full rounded-full"
                style={{
                  width: total > 0 ? `${(value / total) * 100}%` : '0%',
                  backgroundColor: componentColor[key],
                }}
              />
            </div>
            <dd className="w-32 shrink-0 text-right font-mono text-xs text-muted">
              {(value * 100).toFixed(1)} pts
              <span className="ml-1.5 opacity-70">
                ({Math.round(SCORE_COMPONENT_WEIGHTS[key] * 100)}% weight)
              </span>
            </dd>
          </div>
        ))}
      </dl>

      <p className="mt-4 border-t border-app pt-3 text-xs text-muted">
        Components total {(total * 100).toFixed(1)} points against a predicted score of{' '}
        {(plan.travel_suitability_score * 100).toFixed(1)} percent. Small differences reflect the
        regression model's margin of error.
      </p>
    </div>
  )
}

export function SeasonalResults({ plan }: { plan: SeasonalPlanResponse }) {
  const isBeach = plan.dest_type.toLowerCase().includes('beach')

  return (
    <div className="flex flex-col gap-5">
      {/* Section 1 — headline verdict */}
      <div className="card overflow-hidden">
        <DestinationImage destination={plan.destination} width={800} height={280} rounded="rounded-none" />
        <div className="flex flex-wrap items-center justify-between gap-4 p-5">
          <div className="min-w-0 flex-1">
            <h2 className="font-display text-2xl font-bold text-body">{plan.destination}</h2>
            <p className="text-sm text-muted">
              {plan.month_name} {plan.year} · {plan.season}
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Badge tone={toneForSuitability(plan.suitability_label)}>
                {suitabilityLabel(plan.suitability_label)}
              </Badge>
              {plan.is_peak_national && <Badge tone="info">Peak national season</Badge>}
              {plan.is_best_period && <Badge tone="best">Best period for this destination</Badge>}
            </div>
            {plan.recommendation_summary && (
              <p className="mt-3 max-w-prose text-sm leading-relaxed text-body">
                {plan.recommendation_summary}
              </p>
            )}
            {plan.season_reason && (
              <div className="mt-3 max-w-prose rounded-lg border border-app bg-app px-3 py-2">
                <p className="text-xs font-semibold text-body">
                  {plan.suitability_label === 'AVOID'
                    ? 'Why to avoid this period'
                    : 'What holds this month back'}
                </p>
                <ul className="mt-1 space-y-0.5">
                  {plan.season_reason.split('; ').filter(Boolean).map((reason) => (
                    <li key={reason} className="flex gap-1.5 text-xs text-muted">
                      <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-muted" />
                      <span className="first-letter:uppercase">{reason}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          <ScoreGauge
            value={plan.travel_suitability_score}
            label="Suitability"
            color={gaugeColor(plan.suitability_label)}
          />
        </div>
      </div>

      {/* Section 2 — score breakdown */}
      <ScoreBreakdownPanel plan={plan} />

      {/* Section 3 — weather detail */}
      <div className="card p-5">
        <h3 className="mb-3 font-display text-lg font-semibold text-body">Weather outlook</h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          <StatCard
            icon={<CloudSun className="h-5 w-5" />}
            label="Weather verdict"
            value={plan.weather_verdict}
            accent={verdictColor(plan.weather_verdict)}
          />
          <StatCard icon={<Thermometer className="h-5 w-5" />} label="Average temperature" value={`${plan.avg_temp_c}°C`} />
          <StatCard icon={<Umbrella className="h-5 w-5" />} label="Rain risk" value={plan.rain_risk} />
          <StatCard icon={<CloudRain className="h-5 w-5" />} label="Rainy days" value={`${plan.rainy_days} days`} />
          <StatCard icon={<Droplets className="h-5 w-5" />} label="Humidity" value={`${plan.avg_humidity_pct}%`} />
          <StatCard icon={<Sun className="h-5 w-5" />} label="Sunshine per day" value={`${plan.sunshine_hours} hours`} />
          <StatCard icon={<CloudRain className="h-5 w-5" />} label="Total rainfall" value={`${plan.total_rainfall_mm} mm`} />
          <StatCard icon={<Gauge className="h-5 w-5" />} label="Comfort index" value={`${plan.comfort_index} out of 100`} />
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <Badge tone={rainRiskTone(plan.rain_risk)}>{plan.rain_risk} rain risk</Badge>
          <div className="flex min-w-[180px] flex-1 items-center gap-2">
            <span className="text-xs text-muted">Comfort</span>
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-black/5 dark:bg-white/10">
              <div
                className="h-full rounded-full bg-jungle"
                style={{ width: `${Math.max(0, Math.min(100, plan.comfort_index))}%` }}
              />
            </div>
            <span className="font-mono text-xs text-muted">{plan.comfort_index}</span>
          </div>
        </div>
      </div>

      {/* Section 4 — seasonal and event context */}
      <div className="card p-5">
        <h3 className="mb-3 font-display text-lg font-semibold text-body">Seasonal and event context</h3>

        {plan.festival_name && (
          <div className="mb-4 flex items-center gap-3 rounded-xl border border-spice/30 bg-spice/10 px-4 py-3">
            <PartyPopper className="h-5 w-5 shrink-0 text-spice" />
            <p className="text-sm font-medium text-body">
              {plan.festival_name} happening this month
            </p>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard icon={<Compass className="h-5 w-5" />} label="Season" value={plan.season} />
          <StatCard
            icon={<CalendarCheck className="h-5 w-5" />}
            label="Peak national season"
            value={plan.is_peak_national ? 'Yes' : 'No'}
          />
          <StatCard
            icon={<PartyPopper className="h-5 w-5" />}
            label="Tourism event score"
            value={`${plan.tourism_event_score}`}
          />
          <StatCard
            icon={<CalendarCheck className="h-5 w-5" />}
            label="Public holidays"
            value={plan.holiday_count === 1 ? '1 holiday' : `${plan.holiday_count} holidays`}
          />
        </div>

        <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-2 border-t border-app pt-4 text-sm sm:grid-cols-3">
          <div className="flex justify-between gap-2">
            <dt className="text-muted">Destination type</dt>
            <dd className="font-medium capitalize text-body">{plan.dest_type}</dd>
          </div>
          <div className="flex justify-between gap-2">
            <dt className="text-muted">Climate zone</dt>
            <dd className="font-medium capitalize text-body">{plan.climate_zone}</dd>
          </div>
          <div className="flex justify-between gap-2">
            <dt className="text-muted">Typical stay</dt>
            <dd className="font-medium text-body">
              {plan.avg_stay_days === 1 ? '1 day' : `${plan.avg_stay_days} days`}
            </dd>
          </div>
        </dl>
      </div>

      {/* Section 5 — practical planning */}
      <div className="grid gap-5 md:grid-cols-3">
        <PlanningCard icon={<Compass className="h-5 w-5" />} title="What to do" items={plan.best_activities} />
        <PlanningCard icon={<Backpack className="h-5 w-5" />} title="What to pack" items={plan.packing_advice} />
        <PlanningCard icon={<Info className="h-5 w-5" />} title="Good to know" items={plan.things_to_note} />
      </div>

      {/* Section 6 — sea condition, beach destinations only */}
      {isBeach && plan.sea_condition && (
        <div className="card flex items-center gap-3 p-5">
          <Waves className="h-6 w-6 shrink-0 text-ocean dark:text-ocean-light" />
          <div>
            <h3 className="font-semibold text-body">Sea condition</h3>
            <p className="text-sm text-muted">{plan.sea_condition}</p>
          </div>
        </div>
      )}

      {/* Off-season advisory, sourced from Module 3 */}
      {plan.is_off_season && (
        <div className="flex items-start gap-3 rounded-xl border border-spice/40 bg-spice/10 p-5">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-spice" />
          <div>
            <h3 className="font-semibold text-body">Off-season advisory</h3>
            <p className="mt-1 text-sm text-muted">
              This destination is off-season this month and is not recommended for travel.
            </p>
          </div>
        </div>
      )}

      {/* Section 7 — crowd context, sourced from Module 3 */}
      <div className="rounded-xl border border-dashed border-app bg-app p-5">
        <div className="flex flex-wrap items-center gap-3">
          <Users className="h-5 w-5 shrink-0 text-muted" />
          <span className="text-sm font-semibold text-muted">Crowd level</span>
          <Badge tone={toneForCrowd(plan.crowd_context_level)}>
            {crowdLabel(plan.crowd_context_level)}
          </Badge>
          <Badge tone="neutral" className="ml-auto">Module 3</Badge>
        </div>
        {plan.crowd_event_note && (
          <p className="mt-2 text-sm font-medium text-body">{plan.crowd_event_note}</p>
        )}
        <p className="mt-2 text-xs text-muted">
          {plan.crowd_context_note}. Crowd is not part of the seasonal suitability score.
        </p>
      </div>
    </div>
  )
}
