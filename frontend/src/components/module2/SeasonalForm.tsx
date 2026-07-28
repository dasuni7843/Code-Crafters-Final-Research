import { CalendarRange, Search } from 'lucide-react'
import { Field, PillGroup, PrimaryButton, Select } from '../ui/FormControls'
import { FORECAST_YEARS, MONTH_NAMES } from '../../lib/constants'

export type ViewMode = 'single' | 'year'

interface SeasonalFormProps {
  destinations: string[]
  destination: string
  onDestination: (v: string) => void
  year: number
  onYear: (v: number) => void
  month: number
  onMonth: (v: number) => void
  viewMode: ViewMode
  onViewMode: (v: ViewMode) => void
  onSubmit: () => void
  loading: boolean
}

export function SeasonalForm({
  destinations,
  destination,
  onDestination,
  year,
  onYear,
  month,
  onMonth,
  viewMode,
  onViewMode,
  onSubmit,
  loading,
}: SeasonalFormProps) {
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        onSubmit()
      }}
      className="card flex flex-col gap-5 p-5"
    >
      <Field label="Destination">
        <Select
          value={destination}
          onChange={onDestination}
          options={destinations.map((d) => ({ value: d, label: d }))}
          ariaLabel="Destination"
        />
      </Field>

      <Field label="Year">
        <PillGroup
          value={year}
          onChange={onYear}
          options={FORECAST_YEARS.map((y) => ({ value: y, label: String(y) }))}
        />
      </Field>

      <Field label="View mode">
        <PillGroup
          value={viewMode}
          onChange={onViewMode}
          options={[
            { value: 'single', label: 'Single month' },
            { value: 'year', label: 'Full year calendar' },
          ]}
        />
      </Field>

      {viewMode === 'single' && (
        <Field label="Month">
          <Select
            value={month}
            onChange={onMonth}
            options={MONTH_NAMES.map((m, i) => ({ value: i + 1, label: m }))}
            ariaLabel="Month"
          />
        </Field>
      )}

      <PrimaryButton type="submit" disabled={loading} className="w-full">
        {viewMode === 'single' ? <Search className="h-4 w-4" /> : <CalendarRange className="h-4 w-4" />}
        {loading ? 'Working' : viewMode === 'single' ? 'Get seasonal plan' : 'Get year overview'}
      </PrimaryButton>
    </form>
  )
}
