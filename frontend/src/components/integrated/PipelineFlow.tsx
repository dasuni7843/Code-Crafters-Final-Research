import { ArrowRight, BarChart3, Leaf, Target, Users } from 'lucide-react'
import type { ComponentType } from 'react'

interface Stage {
  id: string
  module: string
  title: string
  icon: ComponentType<{ className?: string }>
  external: boolean
}

const stages: Stage[] = [
  { id: 'm1', module: 'Module 1', title: 'Demand forecast', icon: BarChart3, external: false },
  { id: 'm2', module: 'Module 2', title: 'Seasonal planning', icon: Leaf, external: false },
  { id: 'm3', module: 'Module 3', title: 'Crowd risk', icon: Users, external: true },
  { id: 'm4', module: 'Module 4', title: 'Recommendations', icon: Target, external: false },
]

export function PipelineFlow() {
  return (
    <div>
      <div className="flex flex-col items-stretch gap-3 md:flex-row md:items-center">
        {stages.map((s, i) => {
          const Icon = s.icon
          return (
            <div key={s.id} className="flex flex-1 items-center gap-3 md:flex-col md:gap-3">
              <div
                className={`flex w-full flex-1 flex-col items-center gap-2 rounded-2xl p-4 text-center transition ${
                  s.external
                    ? 'border-2 border-dashed border-app bg-app'
                    : 'border-2 border-ocean bg-ocean/5 shadow-sm'
                }`}
              >
                <span
                  className={`flex h-11 w-11 items-center justify-center rounded-xl ${
                    s.external ? 'bg-black/5 text-muted dark:bg-white/10' : 'bg-ocean text-white'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                </span>
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wide text-muted">{s.module}</div>
                  <div className="font-semibold text-body">{s.title}</div>
                </div>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                    s.external
                      ? 'bg-black/5 text-muted dark:bg-white/10'
                      : 'bg-jungle/15 text-jungle-dark dark:text-jungle-light'
                  }`}
                >
                  {s.external ? 'External input' : 'This system'}
                </span>
              </div>
              {i < stages.length - 1 && (
                <ArrowRight className="h-5 w-5 shrink-0 rotate-90 text-muted md:rotate-0" />
              )}
            </div>
          )
        })}
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-muted">
        <span className="flex items-center gap-2">
          <span className="h-3 w-5 rounded border-2 border-ocean bg-ocean/5" /> Implemented in this system
        </span>
        <span className="flex items-center gap-2">
          <span className="h-3 w-5 rounded border-2 border-dashed border-app bg-app" /> Provided by other team modules
        </span>
      </div>
    </div>
  )
}
