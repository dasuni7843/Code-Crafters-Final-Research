import { useState } from 'react'
import { TrendingUp } from 'lucide-react'
import { PageHeader } from '../components/ui/PageHeader'
import { DemandForm, type DemandViewMode } from '../components/module1/DemandForm'
import { ForecastResult } from '../components/module1/ForecastResult'
import { YearlyForecast } from '../components/module1/YearlyForecast'
import { ModelComparison } from '../components/module1/ModelComparison'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { useApiOnMount, useAsyncAction } from '../hooks/useApi'
import {
  getModule1Comparison,
  getModule1Forecast,
  getModule1Yearly,
  getModule2Destinations,
} from '../services/api'
import { DEFAULT_FORECAST_YEAR } from '../lib/constants'

export function Module1Page() {
  const dests = useApiOnMount(getModule2Destinations)
  const comparison = useApiOnMount(getModule1Comparison)
  const destNames = (dests.data ?? []).map((d) => d.destination)

  const [destination, setDestination] = useState('Sigiriya')
  const [year, setYear] = useState(DEFAULT_FORECAST_YEAR)
  const [month, setMonth] = useState(12)
  const [viewMode, setViewMode] = useState<DemandViewMode>('single')

  const single = useAsyncAction(getModule1Forecast)
  const yearly = useAsyncAction(getModule1Yearly)

  const submit = () => {
    if (viewMode === 'single') single.execute(destination, year, month)
    else yearly.execute(destination, year)
  }

  const loading = single.loading || yearly.loading
  const error = viewMode === 'single' ? single.error : yearly.error

  return (
    <div>
      <PageHeader
        title="Demand forecast"
        subtitle="Module 1 forecasts destination level tourist demand and revenue for 2026 through 2030, using a SARIMA model trained on real SLTDA arrival data and a linear regression for revenue."
      >
        <span className="rounded-full bg-ocean/10 px-3 py-1 text-xs font-semibold text-ocean dark:text-ocean-light">
          Module 1 standalone
        </span>
      </PageHeader>

      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <div className="flex flex-col gap-6">
          {dests.loading && <LoadingSpinner label="Loading destinations" />}
          {dests.error && <ErrorMessage message={dests.error} />}
          {destNames.length > 0 && (
            <DemandForm
              destinations={destNames}
              destination={destination}
              onDestination={setDestination}
              year={year}
              onYear={setYear}
              viewMode={viewMode}
              onViewMode={setViewMode}
              month={month}
              onMonth={setMonth}
              onSubmit={submit}
              loading={loading}
            />
          )}
        </div>

        <div className="flex flex-col gap-5">
          {loading && <LoadingSpinner label="Running the demand forecast" />}
          {error && <ErrorMessage message={error} onRetry={submit} />}

          {!loading && !error && viewMode === 'single' && single.data && (
            <ForecastResult plan={single.data} />
          )}

          {!loading && !error && viewMode === 'year' && yearly.data && (
            <YearlyForecast months={yearly.data} />
          )}

          {!loading && !error && !single.data && !yearly.data && (
            <div className="card flex flex-col items-center gap-3 p-12 text-center">
              <TrendingUp className="h-10 w-10 text-muted" />
              <p className="max-w-sm text-sm text-muted">
                Choose a destination, forecast year and month, then run the demand forecast to see
                predicted arrivals, the foreign and local split, revenue and model detail here.
              </p>
            </div>
          )}
        </div>
      </div>

      <div className="mt-6">
        <ModelComparison comparison={comparison.data} />
      </div>
    </div>
  )
}
