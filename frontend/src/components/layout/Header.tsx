import { Link } from 'react-router-dom'
import { Menu, Moon, Sun, Palmtree } from 'lucide-react'
import { useTheme } from '../../context/ThemeContext'

interface HeaderProps {
  onMenuClick: () => void
}

export function Header({ onMenuClick }: HeaderProps) {
  const { theme, toggleTheme } = useTheme()

  return (
    <header className="fixed inset-x-0 top-0 z-40 h-16 border-b border-app bg-surface/80 backdrop-blur-md">
      <div className="flex h-full items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-3">
          <button
            onClick={onMenuClick}
            className="rounded-lg p-2 text-muted transition hover:bg-black/5 dark:hover:bg-white/10 lg:hidden"
            aria-label="Open navigation"
          >
            <Menu className="h-5 w-5" />
          </button>
          <Link to="/" className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-ocean text-white">
              <Palmtree className="h-5 w-5" />
            </span>
            <span className="leading-tight">
              <span className="block font-display text-lg font-bold text-body">Ceylon Tourism AI</span>
              <span className="block text-xs text-muted">Sri Lanka travel intelligence</span>
            </span>
          </Link>
        </div>

        <button
          onClick={toggleTheme}
          className="relative flex h-9 w-16 items-center rounded-full border border-app bg-app px-1 transition"
          aria-label="Toggle theme"
        >
          <span
            className={`flex h-7 w-7 items-center justify-center rounded-full bg-surface shadow transition-transform duration-300 ${
              theme === 'dark' ? 'translate-x-7' : 'translate-x-0'
            }`}
          >
            {theme === 'dark' ? (
              <Moon className="h-4 w-4 text-ocean-light" />
            ) : (
              <Sun className="h-4 w-4 text-spice" />
            )}
          </span>
        </button>
      </div>
    </header>
  )
}
