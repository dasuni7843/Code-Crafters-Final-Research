import { useMemo, useState } from 'react'
import { MapPin, Search } from 'lucide-react'
import type { CrowdRiskPrediction } from '../../types'
import { Badge, toneForCrowd } from '../ui/Badge'

function formatChangePct(pct: number): string {
  if (pct > 300) return '> +300%'
  if (pct < -300) return '< -300%'
  return `${pct > 0 ? '+' : ''}${pct.toFixed(1)}%`
}

export function CrowdRiskTable({ predictions }: { predictions: CrowdRiskPrediction[] }) {
  const [query, setQuery] = useState('')

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return predictions
    return predictions.filter((p) => p.destination.toLowerCase().includes(q))
  }, [predictions, query])

  return (
    <div className="card overflow-hidden">
      <div className="border-b border-app p-4">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search tracked places..."
            className="w-full rounded-xl border border-app bg-surface py-2.5 pl-9 pr-3 text-sm text-body outline-none transition focus:border-ocean focus:ring-2 focus:ring-ocean/20"
          />
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead>
            <tr className="border-b border-app text-xs uppercase tracking-wide text-muted">
              <th className="px-4 py-3 font-semibold">Place</th>
              <th className="px-4 py-3 font-semibold">Risk</th>
              <th className="px-4 py-3 font-semibold">Latest interest</th>
              <th className="px-4 py-3 font-semibold">Predicted next month</th>
              <th className="px-4 py-3 font-semibold">Change</th>
              <th className="px-4 py-3 font-semibold">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-app">
            {filtered.map((p) => (
              <tr key={p.destination} className="transition hover:bg-black/[0.02] dark:hover:bg-white/[0.03]">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-body">{p.destination}</span>
                    {p.is_core_destination && (
                      <Badge tone="info" icon={<MapPin className="h-3 w-3" />}>
                        Core
                      </Badge>
                    )}
                  </div>
                  <div className="mt-0.5 text-xs text-muted">
                    {p.last_known_month} &rarr; {p.predicted_month}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <Badge tone={toneForCrowd(p.crowd_risk_level.toUpperCase())}>{p.crowd_risk_level}</Badge>
                </td>
                <td className="px-4 py-3 font-mono text-body">{p.latest_interest_index.toFixed(1)}</td>
                <td className="px-4 py-3 font-mono text-body">{p.predicted_interest_index.toFixed(1)}</td>
                <td className={`px-4 py-3 font-mono ${p.predicted_change_pct >= 0 ? 'text-jungle-dark dark:text-jungle-light' : 'text-crimson dark:text-crimson-light'}`}>
                  {formatChangePct(p.predicted_change_pct)}
                </td>
                <td className="px-4 py-3 capitalize text-muted">{p.recommendation_action}</td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-sm text-muted">
                  No tracked places match “{query}”.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
