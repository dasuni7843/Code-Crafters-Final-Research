import { useState } from 'react'
import { AlertTriangle, Layers, MapPin, TrendingUp } from 'lucide-react'
import { PageHeader } from '../components/ui/PageHeader'
import { MetricCard } from '../components/ui/MetricCard'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { PillGroup } from '../components/ui/FormControls'
import { CrowdRiskTable } from '../components/module3/CrowdRiskTable'
import { useApiOnMount } from '../hooks/useApi'
import { getModule3Predictions, getModule3Summary } from '../services/api'

type Scope = 'core' | 'all'

export function Module3Page() {
  const [scope, setScope] = useState<Scope>('core')
  const summary = useApiOnMount(getModule3Summary)
  const predictions = useApiOnMount(() => getModule3Predictions(false))
  const visible = (predictions.data ?? []).filter((p) => scope === 'all' || p.is_core_destination)

  return (
    <div>
      <PageHeader
        title="Crowd interest & risk"
        subtitle="Module 3 fuses Google Trends search interest and Wikipedia page views into a Destination Interest Index (DII), then forecasts next month's DII with a RandomForest / LightGBM ensemble and buckets the predicted change into Low, Medium or High crowd risk."
      >
        <span className="rounded-full bg-ocean/10 px-3 py-1 text-xs font-semibold text-ocean dark:text-ocean-light">
          Module 3 standalone
        </span>
      </PageHeader>

      <p className="mb-6 rounded-xl border border-dashed border-app bg-app px-4 py-3 text-sm text-muted">
        Module 3 tracks close to 300 individually named attractions and landmarks across Sri Lanka — a
        finer grain than the app's 20 core destinations used by Modules 1, 2 and 4. Places marked{' '}
        <span className="inline-flex items-center gap-1 font-medium text-body">
          <MapPin className="h-3.5 w-3.5" /> Core
        </span>{' '}
        also appear in those modules; everywhere else on the site, crowd context is still shown from
        Module 3's mock output until enough tracked places overlap the core list to fully replace it.
      </p>

      {summary.loading && <LoadingSpinner label="Loading crowd risk summary" />}
      {summary.error && <ErrorMessage message={summary.error} />}
      {summary.data && (
        <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <MetricCard label="Places tracked" value={String(summary.data.total_tracked)} icon={<Layers className="h-5 w-5" />} accent="ocean" />
          <MetricCard label="Core destinations" value={String(summary.data.core_destination_count)} icon={<MapPin className="h-5 w-5" />} accent="jungle" />
          <MetricCard label="High risk now" value={String(summary.data.high_count)} icon={<AlertTriangle className="h-5 w-5" />} accent="crimson" />
          <MetricCard label="Ensemble MAPE" value={`${summary.data.ensemble_mape_pct}%`} icon={<TrendingUp className="h-5 w-5" />} accent="spice" />
        </div>
      )}

      <div className="mb-4 flex items-center justify-between gap-4">
        <PillGroup
          value={scope}
          onChange={setScope}
          options={[
            { value: 'core', label: 'Core destinations' },
            { value: 'all', label: 'All tracked places' },
          ]}
        />
      </div>

      {predictions.loading && <LoadingSpinner label="Loading crowd risk predictions" />}
      {predictions.error && <ErrorMessage message={predictions.error} />}
      {predictions.data && visible.length > 0 && <CrowdRiskTable predictions={visible} />}
      {predictions.data && visible.length === 0 && (
        <div className="card flex flex-col items-center gap-3 p-12 text-center">
          <Layers className="h-10 w-10 text-muted" />
          <p className="max-w-sm text-sm text-muted">
            No tracked places overlap the app's core destinations yet. Switch to "All tracked places" to
            see the full set of ~300 attractions Module 3 monitors.
          </p>
        </div>
      )}
    </div>
  )
}
