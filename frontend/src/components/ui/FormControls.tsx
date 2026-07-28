import { useEffect, useRef, useState, type ReactNode } from 'react'
import { Check, ChevronDown } from 'lucide-react'

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-sm font-medium text-body">{label}</label>
      {children}
    </div>
  )
}

interface Option<T extends string | number> {
  value: T
  label: string
}

// Custom listbox dropdown: rounded trigger, chevron with its own spacing,
// and a scrollable, capped-height, rounded popup with styled options.
export function Select<T extends string | number>({
  value,
  onChange,
  options,
  ariaLabel,
}: {
  value: T
  onChange: (v: T) => void
  options: Option<T>[]
  ariaLabel?: string
}) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)
  const listRef = useRef<HTMLUListElement>(null)

  const selected = options.find((o) => o.value === value)

  useEffect(() => {
    if (!open) return
    const onClick = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onClick)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  useEffect(() => {
    if (open && listRef.current) {
      const active = listRef.current.querySelector('[data-selected="true"]')
      active?.scrollIntoView({ block: 'nearest' })
    }
  }, [open])

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        aria-label={ariaLabel}
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        className={`flex w-full items-center justify-between gap-2 rounded-xl border bg-surface px-3.5 py-2.5 text-left text-sm text-body outline-none transition ${
          open ? 'border-ocean ring-2 ring-ocean/20' : 'border-app hover:border-ocean/50'
        }`}
      >
        <span className="truncate">{selected?.label ?? 'Select'}</span>
        <ChevronDown
          className={`ml-2 h-4 w-4 shrink-0 text-muted transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {open && (
        <ul
          ref={listRef}
          role="listbox"
          className="absolute z-50 mt-2 max-h-60 w-full overflow-y-auto rounded-xl border border-app bg-card p-1.5 shadow-xl"
        >
          {options.map((o) => {
            const active = o.value === value
            return (
              <li key={String(o.value)} role="option" aria-selected={active} data-selected={active}>
                <button
                  type="button"
                  onClick={() => {
                    onChange(o.value)
                    setOpen(false)
                  }}
                  className={`flex w-full items-center justify-between gap-2 rounded-lg px-3 py-2 text-left text-sm transition ${
                    active
                      ? 'bg-ocean/10 font-semibold text-ocean dark:text-ocean-light'
                      : 'text-body hover:bg-black/5 dark:hover:bg-white/5'
                  }`}
                >
                  <span className="truncate">{o.label}</span>
                  {active && <Check className="h-4 w-4 shrink-0" />}
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}

export function PillGroup<T extends string | number>({
  value,
  onChange,
  options,
}: {
  value: T
  onChange: (v: T) => void
  options: Option<T>[]
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((o) => {
        const active = o.value === value
        return (
          <button
            key={String(o.value)}
            type="button"
            onClick={() => onChange(o.value)}
            className={`rounded-full border px-3.5 py-1.5 text-sm font-medium transition ${
              active
                ? 'border-ocean bg-ocean text-white shadow-sm'
                : 'border-app bg-surface text-muted hover:border-ocean/50 hover:text-body'
            }`}
          >
            {o.label}
          </button>
        )
      })}
    </div>
  )
}

export function PrimaryButton({
  children,
  onClick,
  disabled,
  className = '',
  type = 'button',
}: {
  children: ReactNode
  onClick?: () => void
  disabled?: boolean
  className?: string
  type?: 'button' | 'submit'
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`inline-flex items-center justify-center gap-2 rounded-xl bg-ocean px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-ocean-light disabled:cursor-not-allowed disabled:opacity-60 ${className}`}
    >
      {children}
    </button>
  )
}
