import { useCallback, useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight, X } from 'lucide-react'
import type { ResultImage } from '../types'
import { PageHeader } from '../components/ui/PageHeader'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { useApiOnMount } from '../hooks/useApi'
import { BASE_URL, getModule1Results, getModule2Results, getModule3Results, getModule4Results } from '../services/api'

type Tab = 'module1' | 'module2' | 'module3' | 'module4'

const metrics: Record<Tab, { label: string; value: string }[]> = {
  module1: [
    { label: 'SARIMA MAPE', value: '6.78%' },
    { label: 'SARIMA MAE', value: '13,784' },
    { label: 'SARIMA RMSE', value: '18,597' },
    { label: 'Revenue R² foreign and local', value: '0.63 and 0.76' },
  ],
  module2: [
    { label: 'Accuracy', value: '96.88%' },
    { label: 'CV accuracy', value: '97.21%' },
    { label: 'XGBoost R²', value: '0.9984' },
    { label: 'XGBoost RMSE', value: '0.0061' },
  ],
  module3: [
    { label: 'Seasonal naive MAPE', value: '78.61%' },
    { label: 'Random Forest MAPE', value: '56.45%' },
    { label: 'Pooled LightGBM MAPE', value: '55.85%' },
    { label: 'Inverse-MAPE ensemble MAPE', value: '53.98%' },
  ],
  module4: [
    { label: 'RMSE', value: '0.1385' },
    { label: 'Exact match', value: '97.57%' },
    { label: 'Mean NDCG@10', value: '0.9885' },
    { label: 'Destinations', value: '20' },
  ],
}

export function TrainingResultsPage() {
  const [tab, setTab] = useState<Tab>('module1')
  const m1 = useApiOnMount(getModule1Results)
  const m2 = useApiOnMount(getModule2Results)
  const m3 = useApiOnMount(getModule3Results)
  const m4 = useApiOnMount(getModule4Results)
  const [lightbox, setLightbox] = useState<number | null>(null)

  const active = tab === 'module1' ? m1 : tab === 'module2' ? m2 : tab === 'module3' ? m3 : m4
  const images = active.data ?? []

  const close = useCallback(() => setLightbox(null), [])
  const prev = useCallback(() => setLightbox((i) => (i === null ? i : (i - 1 + images.length) % images.length)), [images.length])
  const next = useCallback(() => setLightbox((i) => (i === null ? i : (i + 1) % images.length)), [images.length])

  useEffect(() => {
    if (lightbox === null) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') close()
      if (e.key === 'ArrowLeft') prev()
      if (e.key === 'ArrowRight') next()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [lightbox, close, prev, next])

  const imgUrl = (img: ResultImage) => `${BASE_URL}${img.url}`

  return (
    <div>
      <PageHeader
        title="Model results"
        subtitle="Explore the training charts for all four modules. Click any chart to open it full size and step through with the arrow keys."
      />

      <div className="mb-6 inline-flex flex-wrap rounded-xl border border-app bg-surface p-1">
        {(['module1', 'module2', 'module3', 'module4'] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => { setTab(t); setLightbox(null) }}
            className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
              tab === t ? 'bg-ocean text-white shadow-sm' : 'text-muted hover:text-body'
            }`}
          >
            {t === 'module1'
              ? 'Module 1 · Demand forecast'
              : t === 'module2'
                ? 'Module 2 · Seasonal planning'
                : t === 'module3'
                  ? 'Module 3 · Crowd risk'
                  : 'Module 4 · Recommendations'}
          </button>
        ))}
      </div>

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {metrics[tab].map((m) => (
          <div key={m.label} className="card p-4 text-center">
            <div className="font-mono text-xl font-bold text-body">{m.value}</div>
            <div className="text-xs text-muted">{m.label}</div>
          </div>
        ))}
      </div>

      {tab === 'module1' && (
        <p className="mb-6 rounded-xl border border-dashed border-app bg-app px-4 py-3 text-sm text-muted">
          Module 1 forecasts demand with SARIMA and estimates revenue with linear regression, trained on
          real SLTDA arrival data from 2010 to 2018. The 2019 to 2022 years are excluded due to the Easter
          Sunday attacks, the COVID-19 border closure and the economic crisis.
        </p>
      )}

      {tab === 'module2' && (
        <p className="mb-6 rounded-xl border border-dashed border-app bg-app px-4 py-3 text-sm text-muted">
          Module 2 scoring uses weather, seasonality, events, holidays, and accessibility. Crowd risk
          is handled separately by Module 3.
        </p>
      )}

      {tab === 'module3' && (
        <p className="mb-6 rounded-xl border border-dashed border-app bg-app px-4 py-3 text-sm text-muted">
          Module 3 forecasts a Destination Interest Index from fused Google Trends and Wikipedia
          signal with a walk-forward evaluated RandomForest / LightGBM ensemble, then buckets the
          predicted change into Low, Medium or High crowd risk using empirical terciles.
        </p>
      )}

      {active.loading && <LoadingSpinner label="Loading charts" />}
      {active.error && <ErrorMessage message={active.error} />}

      {images.length > 0 && (
        <div className="grid gap-5 md:grid-cols-2">
          {images.map((img, i) => (
            <button
              key={img.filename}
              onClick={() => setLightbox(i)}
              className="card overflow-hidden text-left transition hover:-translate-y-0.5 hover:shadow-lg"
            >
              <div className="bg-white">
                <img
                  src={imgUrl(img)}
                  alt={img.title}
                  loading="lazy"
                  className="h-56 w-full object-contain"
                />
              </div>
              <div className="p-4">
                <h3 className="font-display text-base font-semibold text-body">{img.title}</h3>
                <p className="mt-1 text-sm text-muted">{img.description}</p>
              </div>
            </button>
          ))}
        </div>
      )}

      {lightbox !== null && images[lightbox] && (
        <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/80 p-4" onClick={close}>
          <button
            onClick={(e) => { e.stopPropagation(); prev() }}
            className="absolute left-4 flex h-11 w-11 items-center justify-center rounded-full bg-white/10 text-white transition hover:bg-white/20"
            aria-label="Previous"
          >
            <ChevronLeft className="h-6 w-6" />
          </button>

          <div className="flex max-h-[90vh] max-w-[90vw] flex-col items-center gap-4" onClick={(e) => e.stopPropagation()}>
            <img
              src={imgUrl(images[lightbox])}
              alt={images[lightbox].title}
              className="max-h-[76vh] max-w-[90vw] rounded-lg bg-white object-contain"
            />
            <div className="text-center text-white">
              <h3 className="font-display text-lg font-semibold">{images[lightbox].title}</h3>
              <p className="text-sm text-white/70">{images[lightbox].description}</p>
              <p className="mt-1 text-xs text-white/50">{lightbox + 1} of {images.length}</p>
            </div>
          </div>

          <button
            onClick={(e) => { e.stopPropagation(); next() }}
            className="absolute right-4 flex h-11 w-11 items-center justify-center rounded-full bg-white/10 text-white transition hover:bg-white/20"
            aria-label="Next"
          >
            <ChevronRight className="h-6 w-6" />
          </button>
          <button
            onClick={close}
            className="absolute right-4 top-4 flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-white transition hover:bg-white/20"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      )}
    </div>
  )
}
