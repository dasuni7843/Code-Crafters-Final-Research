import { useState } from 'react'
import { ChevronDown, Info } from 'lucide-react'
import type { ModelComparisonResponse } from '../../types'
import { formatNumber } from '../../lib/constants'

function order(values: number[]): string {
  return `(${values.join(',')})`
}

export function ModelComparison({ comparison }: { comparison: ModelComparisonResponse | null }) {
  const [open, setOpen] = useState(false)
  if (!comparison) return null

  const arimaName = `ARIMA ${order(comparison.arima_order)}`
  const sarimaName = `SARIMA ${order(comparison.sarima_order)}${order(comparison.sarima_seasonal_order)}`

  const rows = [
    {
      metric: 'MAPE',
      arima: `${comparison.arima_mape.toFixed(2)} percent`,
      sarima: `${comparison.sarima_mape.toFixed(2)} percent`,
    },
    { metric: 'MAE', arima: formatNumber(comparison.arima_mae), sarima: formatNumber(comparison.sarima_mae) },
    { metric: 'RMSE', arima: formatNumber(comparison.arima_rmse), sarima: formatNumber(comparison.sarima_rmse) },
  ]

  return (
    <div className="card p-5">
      <button onClick={() => setOpen((o) => !o)} className="flex w-full items-center justify-between text-left">
        <span className="flex items-center gap-2 font-semibold text-body">
          <Info className="h-4 w-4 text-ocean" /> How this forecast was produced
        </span>
        <ChevronDown className={`h-5 w-5 text-muted transition ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="mt-4">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[420px] text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-muted">
                  <th className="pb-2">Metric</th>
                  <th className="pb-2 text-right">{arimaName}</th>
                  <th className="pb-2 text-right text-jungle-dark dark:text-jungle-light">{sarimaName}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.metric} className="border-t border-app">
                    <td className="py-2 font-medium text-body">{r.metric}</td>
                    <td className="py-2 text-right font-mono text-muted">{r.arima}</td>
                    <td className="py-2 text-right font-mono font-bold text-jungle-dark dark:text-jungle-light">
                      {r.sarima}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-4 rounded-xl border border-dashed border-app bg-app px-4 py-3 text-xs leading-relaxed text-muted">
            {comparison.selected_model} was selected because it captures Sri Lanka's strong annual
            seasonality. Both models were trained on {comparison.train_months} months of real SLTDA data
            from {comparison.train_period.replace('-', ' to ')}, with{' '}
            {comparison.excluded_years[0]} to {comparison.excluded_years[comparison.excluded_years.length - 1]}{' '}
            excluded due to the Easter Sunday attacks, the COVID-19 border closure, and the economic crisis.
          </p>
        </div>
      )}
    </div>
  )
}
