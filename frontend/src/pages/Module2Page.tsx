import { useState } from 'react'
import { CalendarDays } from 'lucide-react'
import { PageHeader } from '../components/ui/PageHeader'
import { SeasonalForm, type ViewMode } from '../components/module2/SeasonalForm'
import { SeasonalResults } from '../components/module2/SeasonalResults'
import { MonthlyCalendar } from '../components/module2/MonthlyCalendar'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { useApiOnMount, useAsyncAction } from '../hooks/useApi'
import { getModule2Destinations, getMonthlyPlan, getSeasonalPlan } from '../services/api'
import { DEFAULT_FORECAST_YEAR } from '../lib/constants'

export function Module2Page() {
  const dests = useApiOnMount(getModule2Destinations)
  const destNames = (dests.data ?? []).map((d) => d.destination)

  const [destination, setDestination] = useState('Mirissa')
  const [year, setYear] = useState(DEFAULT_FORECAST_YEAR)
  const [month, setMonth] = useState(1)
  const [viewMode, setViewMode] = useState<ViewMode>('single')
  // Month drilled into from the full year calendar
  const [detailMonth, setDetailMonth] = useState<number | null>(null)

  const single = useAsyncAction(getSeasonalPlan)
  const yearly = useAsyncAction(getMonthlyPlan)

  const submit = () => {
    setDetailMonth(null)
    if (viewMode === 'single') single.execute(destination, year, month)
    else yearly.execute(destination, year)
  }

  const loading = single.loading || yearly.loading
  const error = viewMode === 'single' ? single.error : yearly.error

  const detailPlan =
    detailMonth !== null ? yearly.data?.find((m) => m.month === detailMonth) : undefined

  return (
    <div>
      <PageHeader
        title="Seasonal travel planning"
        subtitle="Test Module 2 on its own. Pick a destination and month to see the suitability verdict, how the score is composed, the weather outlook and practical planning advice."
      >
        <span className="rounded-full bg-jungle/10 px-3 py-1 text-xs font-semibold text-jungle-dark dark:text-jungle-light">
          Module 2 standalone
        </span>
      </PageHeader>

      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <div>
          {dests.loading && <LoadingSpinner label="Loading destinations" />}
          {dests.error && <ErrorMessage message={dests.error} />}
          {destNames.length > 0 && (
            <SeasonalForm
              destinations={destNames}
              destination={destination}
              onDestination={setDestination}
              year={year}
              onYear={setYear}
              month={month}
              onMonth={setMonth}
              viewMode={viewMode}
              onViewMode={setViewMode}
              onSubmit={submit}
              loading={loading}
            />
          )}
        </div>

        <div className="flex flex-col gap-5">
          {loading && <LoadingSpinner label="Running the seasonal model" />}
          {error && <ErrorMessage message={error} onRetry={submit} />}

          {!loading && !error && viewMode === 'single' && single.data && (
            <SeasonalResults plan={single.data} />
          )}

          {!loading && !error && viewMode === 'year' && yearly.data && (
            <>
              <MonthlyCalendar
                months={yearly.data}
                selectedMonth={detailMonth ?? undefined}
                onSelectMonth={setDetailMonth}
              />
              {detailPlan && <SeasonalResults plan={detailPlan} />}
            </>
          )}

          {!loading && !error && !single.data && !yearly.data && (
            <div className="card flex flex-col items-center gap-3 p-12 text-center">
              <CalendarDays className="h-10 w-10 text-muted" />
              <p className="max-w-sm text-sm text-muted">
                Choose a destination and month, then run the seasonal plan to see results here.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
