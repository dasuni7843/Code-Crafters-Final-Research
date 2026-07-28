import { NavLink } from 'react-router-dom'
import { BarChart3, Home, Leaf, Link2, Target, TrendingUp, X } from 'lucide-react'

interface SidebarProps {
  open: boolean
  onClose: () => void
}

const navItems = [
  { to: '/', label: 'Overview', icon: Home, end: true },
  { to: '/module1', label: 'Demand forecast', icon: TrendingUp, end: false },
  { to: '/module2', label: 'Seasonal planning', icon: Leaf, end: false },
  { to: '/module4', label: 'Recommendations', icon: Target, end: false },
  { to: '/integrated', label: 'Full system', icon: Link2, end: false },
  { to: '/results', label: 'Model results', icon: BarChart3, end: false },
]

export function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
          onClick={onClose}
          aria-hidden
        />
      )}

      <aside
        className={`fixed left-0 top-16 z-50 h-[calc(100vh-4rem)] w-60 transform border-r border-app bg-surface transition-transform duration-300 lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between px-4 py-3 lg:hidden">
          <span className="text-sm font-semibold text-muted">Navigation</span>
          <button onClick={onClose} className="rounded-lg p-1.5 text-muted hover:bg-black/5 dark:hover:bg-white/10">
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex flex-col gap-1 px-3 py-3">
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-lg border-l-[3px] px-3 py-2.5 text-sm font-medium transition ${
                    isActive
                      ? 'border-jungle bg-ocean/10 text-ocean dark:text-ocean-light'
                      : 'border-transparent text-muted hover:bg-black/5 hover:text-body dark:hover:bg-white/5'
                  }`
                }
              >
                <Icon className="h-[18px] w-[18px]" />
                {item.label}
              </NavLink>
            )
          })}
        </nav>

        <div className="mt-auto px-4 py-4">
          <div className="rounded-xl border border-app bg-app p-3 text-xs text-muted">
            <p className="font-semibold text-body">Code Crafters</p>
            <p className="mt-1">University of Moratuwa, Faculty of IT, Level 4</p>
          </div>
        </div>
      </aside>
    </>
  )
}
