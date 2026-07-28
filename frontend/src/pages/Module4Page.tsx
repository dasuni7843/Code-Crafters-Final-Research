import { useState } from 'react'
import { ChevronDown, Info, Sparkles } from 'lucide-react'
import type { RecommendationRequest } from '../types'
import { PageHeader } from '../components/ui/PageHeader'
import { RecommendationForm } from '../components/module4/RecommendationForm'
import { RecommendationsGrid } from '../components/module4/RecommendationsGrid'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { useAsyncAction } from '../hooks/useApi'
import { getRecommendations } from '../services/api'

const factors = [
  { label: 'Content similarity', pct: '35%', desc: 'How closely a destination matches your preferred experience.' },
  { label: 'Seasonal suitability', pct: '25%', desc: 'Module 2 travel suitability score for your chosen month.' },
  { label: 'Crowd compatibility', pct: '25%', desc: 'How the Module 3 crowd risk fits your comfort level.' },
  { label: 'Accessibility', pct: '15%', desc: 'Ease of reaching and getting around the destination.' },
]

export function Module4Page() {
  const recs = useAsyncAction(getRecommendations)
  const [explain, setExplain] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  const submit = (req: RecommendationRequest) => {
    setSubmitted(true)
    recs.execute(req)
  }

  const results = recs.data ?? []

  return (
    <div>
      <PageHeader
        title="Personalized recommendations"
        subtitle="Test Module 4 on its own. Set your travel preferences and get a ranked list of destinations with the reasons behind each match."
      >
        <span className="rounded-full bg-ocean/10 px-3 py-1 text-xs font-semibold text-ocean dark:text-ocean-light">
          Module 4 standalone
        </span>
      </PageHeader>

      <RecommendationForm onSubmit={submit} loading={recs.loading} />

      <div className="mt-6">
        {recs.loading && <LoadingSpinner label="Matching destinations to your preferences" />}
        {recs.error && <ErrorMessage message={recs.error} />}

        {!recs.loading && !recs.error && submitted && results.length === 0 && (
          <div className="card p-8 text-center text-sm text-muted">
            No destinations matched your preferences. Try adjusting your crowd tolerance or preferred
            experience type.
          </div>
        )}

        {!recs.loading && results.length > 0 && (
          <>
            <div className="mb-4 flex items-center gap-2 text-sm text-muted">
              <Sparkles className="h-4 w-4 text-jungle" />
              Showing your top {results.length} destinations
            </div>
            <RecommendationsGrid recommendations={results} />

            <div className="mt-6 card p-5">
              <button
                onClick={() => setExplain((e) => !e)}
                className="flex w-full items-center justify-between text-left"
              >
                <span className="flex items-center gap-2 font-semibold text-body">
                  <Info className="h-4 w-4 text-ocean" /> How this recommendation was made
                </span>
                <ChevronDown className={`h-5 w-5 text-muted transition ${explain ? 'rotate-180' : ''}`} />
              </button>
              {explain && (
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  {factors.map((f) => (
                    <div key={f.label} className="rounded-xl border border-app p-4">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-body">{f.label}</span>
                        <span className="font-mono text-sm font-bold text-ocean dark:text-ocean-light">{f.pct}</span>
                      </div>
                      <p className="mt-1 text-xs text-muted">{f.desc}</p>
                    </div>
                  ))}
                  <p className="sm:col-span-2 rounded-xl border border-dashed border-app bg-app px-4 py-3 text-xs text-muted">
                    Predicted arrivals come from Module 1's real SARIMA demand forecast. Crowd risk levels
                    come from Module 3, a separate team module shown here using realistic mock data in its format.
                  </p>
                </div>
              )}
            </div>
          </>
        )}

        {!submitted && (
          <div className="card flex flex-col items-center gap-3 p-12 text-center">
            <Sparkles className="h-10 w-10 text-muted" />
            <p className="max-w-sm text-sm text-muted">
              Set your preferences above and find destinations tailored to how you like to travel.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
