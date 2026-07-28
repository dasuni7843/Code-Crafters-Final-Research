import { useState } from 'react'
import { Layers, Workflow } from 'lucide-react'
import type { RecommendationRequest } from '../types'
import { PageHeader } from '../components/ui/PageHeader'
import { RecommendationForm } from '../components/module4/RecommendationForm'
import { RecommendationsGrid } from '../components/module4/RecommendationsGrid'
import { PipelineFlow } from '../components/integrated/PipelineFlow'
import { IntegratedPipelineSteps } from '../components/integrated/IntegratedResults'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { useAsyncAction } from '../hooks/useApi'
import { getIntegratedRecommendations } from '../services/api'

export function IntegratedPage() {
  const pipeline = useAsyncAction(getIntegratedRecommendations)
  const [showSteps, setShowSteps] = useState(true)
  const [submitted, setSubmitted] = useState(false)

  const submit = (req: RecommendationRequest) => {
    setSubmitted(true)
    pipeline.execute(req)
  }

  const data = pipeline.data

  const toggle = (
    <label className="flex items-center justify-between gap-3 rounded-xl border border-app bg-app px-4 py-3">
      <span className="flex items-center gap-2 text-sm font-medium text-body">
        <Layers className="h-4 w-4 text-ocean" /> Show pipeline steps
      </span>
      <button
        type="button"
        onClick={() => setShowSteps((s) => !s)}
        className={`flex h-6 w-11 shrink-0 items-center rounded-full p-0.5 transition-colors ${
          showSteps ? 'justify-end bg-ocean' : 'justify-start bg-black/20 dark:bg-white/20'
        }`}
        aria-pressed={showSteps}
      >
        <span className="h-5 w-5 rounded-full bg-white shadow transition-transform" />
      </button>
    </label>
  )

  return (
    <div>
      <PageHeader
        title="Full system"
        subtitle="See all four modules work together. The same preferences drive a single pipeline where each module contributes to the final ranking."
      >
        <span className="rounded-full bg-spice/10 px-3 py-1 text-xs font-semibold text-spice-dark dark:text-spice-light">
          Integrated view
        </span>
      </PageHeader>

      <div className="mb-6 card p-5">
        <div className="mb-4 flex items-center gap-2">
          <Workflow className="h-5 w-5 text-ocean" />
          <h2 className="font-display text-lg font-semibold text-body">Recommendation pipeline</h2>
        </div>
        <PipelineFlow />
      </div>

      <RecommendationForm onSubmit={submit} loading={pipeline.loading} submitLabel="Run the full pipeline" extra={toggle} />

      <div className="mt-6 flex flex-col gap-6">
        {pipeline.loading && <LoadingSpinner label="Running all four modules" />}
        {pipeline.error && <ErrorMessage message={pipeline.error} />}

        {!pipeline.loading && data && (
          <>
            {showSteps && <IntegratedPipelineSteps data={data} />}

            <div>
              <h2 className="mb-4 font-display text-xl font-semibold text-body">
                Final recommendations for {data.month_name}
              </h2>
              {data.module4.length > 0 ? (
                <RecommendationsGrid recommendations={data.module4} showBreakdown />
              ) : (
                <div className="card p-8 text-center text-sm text-muted">
                  No destinations matched your preferences. Try adjusting your crowd tolerance or preferred
                  experience type.
                </div>
              )}
            </div>
          </>
        )}

        {!submitted && (
          <div className="card flex flex-col items-center gap-3 p-12 text-center">
            <Workflow className="h-10 w-10 text-muted" />
            <p className="max-w-sm text-sm text-muted">
              Set your preferences and run the pipeline to see how Module 1, Module 2, Module 3 and Module 4
              combine into a final ranking.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
