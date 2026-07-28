import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, CalendarDays, Compass, Layers, MapPin, Target, TrendingUp, Zap } from 'lucide-react'
import type { RecommendationRequest } from '../types'
import { PipelineFlow } from '../components/integrated/PipelineFlow'
import { MetricCard } from '../components/ui/MetricCard'
import { DestinationImage } from '../components/ui/DestinationImage'
import { Field, PillGroup, PrimaryButton, Select } from '../components/ui/FormControls'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { Badge, toneForCrowd } from '../components/ui/Badge'
import { useAsyncAction } from '../hooks/useApi'
import { getRecommendations } from '../services/api'
import { crowdLabel, DEFAULT_FORECAST_YEAR, MONTH_NAMES, toPercent } from '../lib/constants'

const userTypes = [
  { value: 'beach', label: 'Beach lover' },
  { value: 'cultural', label: 'Culture explorer' },
  { value: 'nature', label: 'Nature seeker' },
  { value: 'adventure', label: 'Adventurer' },
]

export function HomePage() {
  const recs = useAsyncAction(getRecommendations)
  const [preferredType, setPreferredType] = useState('beach')
  const [month, setMonth] = useState(12)

  const quickTest = () => {
    const req: RecommendationRequest = {
      preferred_type: preferredType,
      crowd_tolerance: 'low',
      travel_month: month,
      travel_year: DEFAULT_FORECAST_YEAR,
      trip_budget: 'mid',
      travel_party: 'couple',
      weather_preference: 'any',
      activity_preference: preferredType === 'cultural' ? 'heritage' : preferredType,
      top_n: 3,
    }
    recs.execute(req)
  }

  const results = recs.data ?? []

  return (
    <div className="flex flex-col gap-8">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-3xl">
        <div className="absolute inset-0">
          <DestinationImage destination="Sigiriya" width={1200} height={420} rounded="rounded-3xl" />
          <div className="absolute inset-0 bg-gradient-to-r from-ocean-dark/90 via-ocean-dark/70 to-transparent" />
        </div>
        <div className="relative px-6 py-14 sm:px-10 sm:py-20">
          <span className="inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold text-white backdrop-blur">
            <Zap className="h-3.5 w-3.5" /> Code Crafters · University of Moratuwa
          </span>
          <h1 className="mt-4 max-w-2xl font-display text-4xl font-bold leading-tight text-white sm:text-5xl">
            Ceylon Tourism AI
          </h1>
          <p className="mt-3 max-w-xl text-base text-white/85 sm:text-lg">
            AI powered travel intelligence for Sri Lanka. Plan the best season to travel and get
            personalized destination recommendations, end to end.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link to="/module4">
              <PrimaryButton className="bg-jungle hover:bg-jungle-light">
                <Target className="h-4 w-4" /> Get recommendations
              </PrimaryButton>
            </Link>
            <Link to="/integrated">
              <span className="inline-flex items-center gap-2 rounded-xl border border-white/40 bg-white/10 px-5 py-3 text-sm font-semibold text-white backdrop-blur transition hover:bg-white/20">
                Explore the full system <ArrowRight className="h-4 w-4" />
              </span>
            </Link>
          </div>
        </div>
      </section>

      {/* Pipeline */}
      <section className="card p-6">
        <h2 className="mb-1 font-display text-xl font-semibold text-body">How the system works</h2>
        <p className="mb-5 text-sm text-muted">
          Four modules run in sequence. This codebase implements demand forecasting, seasonal planning
          and recommendations; only crowd risk is provided by another team module.
        </p>
        <PipelineFlow />
      </section>

      {/* Quick stats */}
      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard label="Destinations" value="20" icon={<MapPin className="h-6 w-6" />} accent="ocean" />
        <MetricCard label="AI modules" value="4" icon={<Layers className="h-6 w-6" />} accent="jungle" />
        <MetricCard label="Months covered" value="12" icon={<CalendarDays className="h-6 w-6" />} accent="spice" />
        <MetricCard label="Forecast years" value="5" hint="2026 to 2030" icon={<TrendingUp className="h-6 w-6" />} accent="crimson" />
      </section>

      {/* Quick test */}
      <section className="card p-6">
        <div className="mb-4 flex items-center gap-2">
          <Compass className="h-5 w-5 text-ocean" />
          <h2 className="font-display text-xl font-semibold text-body">Quick test</h2>
        </div>
        <div className="grid gap-5 md:grid-cols-[1fr_1fr_auto] md:items-end">
          <Field label="Travel style">
            <PillGroup value={preferredType} onChange={setPreferredType} options={userTypes} />
          </Field>
          <Field label="Travel month">
            <Select
              value={month}
              onChange={setMonth}
              options={MONTH_NAMES.map((m, i) => ({ value: i + 1, label: m }))}
              ariaLabel="Travel month"
            />
          </Field>
          <PrimaryButton onClick={quickTest} disabled={recs.loading} className="w-full md:w-auto">
            {recs.loading ? 'Working' : 'Show top 3'}
          </PrimaryButton>
        </div>

        <div className="mt-6">
          {recs.loading && <LoadingSpinner label="Finding great matches" />}
          {recs.error && <ErrorMessage message={recs.error} onRetry={quickTest} />}
          {!recs.loading && results.length > 0 && (
            <div className="grid gap-4 sm:grid-cols-3">
              {results.map((r) => (
                <div key={r.destination} className="card overflow-hidden">
                  <div className="relative">
                    <DestinationImage destination={r.destination} width={400} height={200} />
                    <span className="absolute left-2 top-2 flex h-7 w-7 items-center justify-center rounded-full bg-ocean font-mono text-xs font-bold text-white">
                      {r.rank}
                    </span>
                  </div>
                  <div className="p-3">
                    <h3 className="font-display text-lg font-semibold text-body">{r.destination}</h3>
                    <div className="mt-1 flex items-center justify-between">
                      <span className="font-mono text-sm font-semibold text-jungle-dark dark:text-jungle-light">
                        {toPercent(r.recommendation_score)} match
                      </span>
                      <Badge tone={toneForCrowd(r.crowd_risk_level)}>{crowdLabel(r.crowd_risk_level)}</Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
