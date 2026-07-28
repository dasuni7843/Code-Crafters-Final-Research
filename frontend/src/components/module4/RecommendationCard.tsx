import { AlertTriangle, Clock, MapPin, PartyPopper, Sparkles, Star, Users } from 'lucide-react'
import type { DestinationRecommendation } from '../../types'
import { Badge, toneForCrowd, toneForSuitability, toneForWeather } from '../ui/Badge'
import { DestinationImage } from '../ui/DestinationImage'
import { crowdLabel, suitabilityLabel, toPercent } from '../../lib/constants'

interface RecommendationCardProps {
  rec: DestinationRecommendation
  onSeeSimilar: (destination: string) => void
  showBreakdown?: boolean
}

const breakdownParts = [
  { key: 'predicted_rating', label: 'Rating', color: '#1B4F72' },
  { key: 'content_similarity', label: 'Similarity', color: '#27AE60' },
  { key: 'crowd_compatibility', label: 'Crowd fit', color: '#E67E22' },
  { key: 'seasonal_suitability', label: 'Season', color: '#2E86C1' },
] as const

export function RecommendationCard({ rec, onSeeSimilar, showBreakdown = false }: RecommendationCardProps) {
  const total = rec.recommendation_score

  return (
    <div className="card group flex flex-col overflow-hidden transition hover:-translate-y-0.5 hover:shadow-lg">
      <div className="relative">
        <DestinationImage destination={rec.destination} width={480} height={260} />
        <span className="absolute left-3 top-3 flex h-9 w-9 items-center justify-center rounded-full bg-ocean font-mono text-sm font-bold text-white shadow">
          {rec.rank}
        </span>
        <span className="absolute right-3 top-3 flex items-center gap-1 rounded-full bg-black/55 px-2.5 py-1 text-xs font-semibold text-white">
          <Star className="h-3.5 w-3.5 fill-spice-light text-spice-light" />
          {rec.predicted_rating.toFixed(1)}
        </span>
      </div>

      <div className="flex flex-1 flex-col gap-3 p-4">
        <div>
          <h3 className="font-display text-xl font-bold text-body">{rec.destination}</h3>
          <p className="flex items-center gap-1 text-xs capitalize text-muted">
            <MapPin className="h-3.5 w-3.5" /> {rec.dest_type} · {rec.district}
          </p>
        </div>

        <div>
          <div className="mb-1 flex items-center justify-between text-xs">
            <span className="text-muted">Match score</span>
            <span className="font-mono font-semibold text-body">{toPercent(total)}</span>
          </div>
          <div className="h-2.5 w-full overflow-hidden rounded-full bg-black/10 dark:bg-white/10">
            <div
              className="h-full rounded-full bg-gradient-to-r from-ocean to-jungle"
              style={{ width: `${Math.min(100, total * 100)}%` }}
            />
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Badge tone={toneForCrowd(rec.crowd_risk_level)} icon={<Users className="h-3.5 w-3.5" />}>
            {crowdLabel(rec.crowd_risk_level)}
          </Badge>
          <Badge tone={toneForSuitability(rec.season_suitability)}>
            {suitabilityLabel(rec.season_suitability)}
          </Badge>
          {rec.is_off_season && (
            <Badge tone="medium" icon={<AlertTriangle className="h-3.5 w-3.5" />}>
              Off-season
            </Badge>
          )}
          <Badge tone={toneForWeather(rec.weather_label)}>{rec.weather_label} weather</Badge>
          {rec.crowd_event_note && (
            <Badge tone="medium" icon={<PartyPopper className="h-3.5 w-3.5" />}>
              {rec.crowd_event_note}
            </Badge>
          )}
        </div>

        {/* Why the seasonal label is what it is, so a badge is never unexplained */}
        {(rec.season_reason || rec.is_off_season) && (
          <div
            className={`rounded-lg border px-3 py-2 ${
              rec.is_off_season ? 'border-spice/40 bg-spice/10' : 'border-app bg-app'
            }`}
          >
            <p className="text-xs font-semibold text-body">
              {rec.season_suitability === 'AVOID' ? 'Why to avoid this period' : 'What holds it back'}
            </p>
            <ul className="mt-1 space-y-0.5">
              {rec.is_off_season && (
                <li className="flex gap-1.5 text-xs text-muted">
                  <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-spice" />
                  <span className="font-medium text-body">
                    Off-season, travel not recommended this month
                  </span>
                </li>
              )}
              {rec.season_reason.split('; ').filter(Boolean).map((reason) => (
                <li key={reason} className="flex gap-1.5 text-xs text-muted">
                  <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-muted" />
                  <span className="first-letter:uppercase">{reason}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <p className="text-sm italic leading-relaxed text-muted">{rec.why_recommended}</p>

        {rec.activities.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {rec.activities.map((a) => (
              <span key={a} className="rounded-full bg-jungle/10 px-2.5 py-0.5 text-xs font-medium text-jungle-dark dark:text-jungle-light">
                {a}
              </span>
            ))}
          </div>
        )}

        {showBreakdown && (
          <div className="rounded-xl border border-app bg-app p-3">
            <p className="mb-2 text-xs font-semibold text-body">Score breakdown</p>
            <div className="flex h-3 w-full overflow-hidden rounded-full">
              {breakdownParts.map((p) => {
                const val = rec.score_breakdown[p.key]
                const width = total > 0 ? (val / total) * 100 : 0
                return <div key={p.key} style={{ width: `${width}%`, backgroundColor: p.color }} title={`${p.label}: ${toPercent(val, 1)}`} />
              })}
            </div>
            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-muted">
              {breakdownParts.map((p) => (
                <span key={p.key} className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full" style={{ backgroundColor: p.color }} />
                  {p.label} {toPercent(rec.score_breakdown[p.key], 1)}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="mt-auto flex items-center justify-between gap-3 pt-1 text-xs text-muted">
          <span className="flex items-center gap-1">
            <Clock className="h-3.5 w-3.5" /> {rec.avg_stay_days} day stay
          </span>
          <button
            onClick={() => onSeeSimilar(rec.destination)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-app px-3 py-1.5 font-semibold text-ocean transition hover:bg-ocean/10 dark:text-ocean-light"
          >
            <Sparkles className="h-3.5 w-3.5" /> See similar
          </button>
        </div>
      </div>
    </div>
  )
}
