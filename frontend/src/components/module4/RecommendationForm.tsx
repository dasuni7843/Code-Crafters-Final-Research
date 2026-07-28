import { useState, type ReactNode } from 'react'
import { Compass } from 'lucide-react'
import type { RecommendationRequest } from '../../types'
import { Field, PillGroup, PrimaryButton, Select } from '../ui/FormControls'
import { DEFAULT_FORECAST_YEAR, FORECAST_YEARS, MONTH_NAMES } from '../../lib/constants'

interface RecommendationFormProps {
  onSubmit: (req: RecommendationRequest) => void
  loading: boolean
  submitLabel?: string
  extra?: ReactNode
}

const defaults: RecommendationRequest = {
  preferred_type: 'beach',
  crowd_tolerance: 'low',
  travel_month: 12,
  travel_year: DEFAULT_FORECAST_YEAR,
  trip_budget: 'mid',
  travel_party: 'couple',
  weather_preference: 'any',
  activity_preference: 'beach',
  top_n: 5,
}

export function RecommendationForm({
  onSubmit,
  loading,
  submitLabel = 'Find my perfect destinations',
  extra,
}: RecommendationFormProps) {
  const [req, setReq] = useState<RecommendationRequest>(defaults)
  const set = <K extends keyof RecommendationRequest>(key: K, value: RecommendationRequest[K]) =>
    setReq((r) => ({ ...r, [key]: value }))

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        onSubmit(req)
      }}
      className="card flex flex-col gap-6 p-5 sm:p-6"
    >
      <div className="grid gap-6 md:grid-cols-2">
        <div className="flex flex-col gap-5">
          <Field label="Preferred experience">
            <PillGroup
              value={req.preferred_type}
              onChange={(v) => set('preferred_type', v)}
              options={[
                { value: 'beach', label: 'Beach' },
                { value: 'cultural', label: 'Cultural' },
                { value: 'nature', label: 'Nature' },
                { value: 'adventure', label: 'Adventure' },
              ]}
            />
          </Field>

          <Field label="Crowd comfort">
            <PillGroup
              value={req.crowd_tolerance}
              onChange={(v) => set('crowd_tolerance', v)}
              options={[
                { value: 'low', label: 'Prefer quiet' },
                { value: 'medium', label: 'Moderate' },
                { value: 'high', label: 'Lively is fine' },
              ]}
            />
          </Field>

          <Field label="Travel month">
            <Select
              value={req.travel_month}
              onChange={(v) => set('travel_month', v)}
              options={MONTH_NAMES.map((m, i) => ({ value: i + 1, label: m }))}
              ariaLabel="Travel month"
            />
          </Field>

          <Field label="Travel year">
            <PillGroup
              value={req.travel_year}
              onChange={(v) => set('travel_year', v)}
              options={FORECAST_YEARS.map((y) => ({ value: y, label: String(y) }))}
            />
          </Field>

          <Field label="Trip budget">
            <PillGroup
              value={req.trip_budget}
              onChange={(v) => set('trip_budget', v)}
              options={[
                { value: 'budget', label: 'Budget' },
                { value: 'mid', label: 'Mid range' },
                { value: 'luxury', label: 'Luxury' },
              ]}
            />
          </Field>
        </div>

        <div className="flex flex-col gap-5">
          <Field label="Travel party">
            <PillGroup
              value={req.travel_party}
              onChange={(v) => set('travel_party', v)}
              options={[
                { value: 'solo', label: 'Solo' },
                { value: 'couple', label: 'Couple' },
                { value: 'family', label: 'Family' },
                { value: 'group', label: 'Group' },
              ]}
            />
          </Field>

          <Field label="Weather preference">
            <PillGroup
              value={req.weather_preference}
              onChange={(v) => set('weather_preference', v)}
              options={[
                { value: 'hot', label: 'Tropical heat' },
                { value: 'warm', label: 'Warm' },
                { value: 'cool', label: 'Cool highland' },
                { value: 'any', label: 'Any' },
              ]}
            />
          </Field>

          <Field label="Activity interest">
            <PillGroup
              value={req.activity_preference}
              onChange={(v) => set('activity_preference', v)}
              options={[
                { value: 'heritage', label: 'Heritage' },
                { value: 'beach', label: 'Beach' },
                { value: 'nature', label: 'Nature' },
                { value: 'adventure', label: 'Adventure' },
                { value: 'wellness', label: 'Wellness' },
                { value: 'food', label: 'Food' },
                { value: 'photography', label: 'Photography' },
              ]}
            />
          </Field>

          <Field label="Results to show">
            <PillGroup
              value={req.top_n}
              onChange={(v) => set('top_n', v)}
              options={[
                { value: 3, label: '3' },
                { value: 5, label: '5' },
                { value: 10, label: '10' },
              ]}
            />
          </Field>
        </div>
      </div>

      {extra}

      <PrimaryButton type="submit" disabled={loading} className="w-full">
        <Compass className="h-4 w-4" />
        {loading ? 'Finding matches' : submitLabel}
      </PrimaryButton>
    </form>
  )
}
