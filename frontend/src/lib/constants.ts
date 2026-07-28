export const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]

export const MONTH_SHORT = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
]

// Seasonal planning always runs for the current year. Suitability is driven by
// climate patterns that repeat annually, so there is nothing for the user to
// choose here and no year selector is shown.
export const PLANNING_YEAR = new Date().getFullYear()

// Module 1 forecasts 2026 through 2030. Every module that feeds the integrated
// pipeline offers the same range so the modules stay consistent.
export const FORECAST_YEARS = [2026, 2027, 2028, 2029, 2030]
export const DEFAULT_FORECAST_YEAR = 2026

export const imageKeywords: Record<string, string> = {
  Sigiriya: 'sigiriya,rock,fortress',
  Ella: 'ella,srilanka,mountains',
  'Galle Fort': 'galle,fort,colonial',
  Kandy: 'kandy,temple,srilanka',
  'Nuwara Eliya': 'tea,plantation,srilanka',
  Mirissa: 'mirissa,beach,whale',
  Unawatuna: 'unawatuna,beach,tropical',
  Bentota: 'bentota,beach,resort',
  'Arugam Bay': 'surfing,beach,srilanka',
  Trincomalee: 'trincomalee,beach,bay',
  Anuradhapura: 'anuradhapura,ancient,ruins',
  Polonnaruwa: 'polonnaruwa,ruins,heritage',
  Dambulla: 'dambulla,cave,temple',
  Yala: 'yala,safari,leopard',
  Pinnawala: 'elephant,orphanage,srilanka',
  'Adams Peak': 'adamspeak,pilgrimage,sunrise',
  'Horton Plains': 'horton,plains,worldend',
  Jaffna: 'jaffna,northern,srilanka',
  Colombo: 'colombo,city,skyline',
  Negombo: 'negombo,beach,fishing',
}

// A stable colour pair per destination, used for the gradient placeholder.
export const destinationGradient: Record<string, [string, string]> = {
  Sigiriya: ['#B7600E', '#27AE60'],
  Ella: ['#1A7A43', '#2E86C1'],
  'Galle Fort': ['#1B4F72', '#E67E22'],
  Kandy: ['#922B21', '#E67E22'],
  'Nuwara Eliya': ['#27AE60', '#0D1B2A'],
  Mirissa: ['#2E86C1', '#2ECC71'],
  Unawatuna: ['#2E86C1', '#F39C12'],
  Bentota: ['#1B4F72', '#2ECC71'],
  'Arugam Bay': ['#2E86C1', '#B7600E'],
  Trincomalee: ['#1B4F72', '#2E86C1'],
  Anuradhapura: ['#B7600E', '#922B21'],
  Polonnaruwa: ['#B7600E', '#1A7A43'],
  Dambulla: ['#922B21', '#E67E22'],
  Yala: ['#B7600E', '#1A7A43'],
  Pinnawala: ['#1A7A43', '#27AE60'],
  'Adams Peak': ['#1B4F72', '#922B21'],
  'Horton Plains': ['#1A7A43', '#2E86C1'],
  Jaffna: ['#E67E22', '#1B4F72'],
  Colombo: ['#0D1B2A', '#2E86C1'],
  Negombo: ['#2E86C1', '#27AE60'],
}

export function suitabilityLabel(label: string): string {
  switch (label) {
    case 'BEST':
      return 'Best time to visit'
    case 'GOOD':
      return 'Good time to visit'
    case 'AVOID':
      return 'Avoid this period'
    default:
      return label
  }
}

export function crowdLabel(level: string): string {
  switch (level) {
    case 'LOW':
      return 'Low crowd'
    case 'MEDIUM':
      return 'Moderate crowd'
    case 'HIGH':
      return 'High crowd'
    default:
      return level
  }
}

/** Weight each component carries in the suitability score, for display. */
export const SCORE_COMPONENT_WEIGHTS: Record<string, number> = {
  weather_component: 0.45,
  season_component: 0.2,
  event_component: 0.15,
  holiday_component: 0.1,
  accessibility_component: 0.1,
}

export const SCORE_COMPONENT_LABELS: Record<string, string> = {
  weather_component: 'Weather',
  season_component: 'Season fit',
  event_component: 'Events',
  holiday_component: 'Holidays',
  accessibility_component: 'Accessibility',
}

export function formatLkr(value: number): string {
  return `LKR ${value.toLocaleString('en-US')}`
}

/** Whole number with thousands separators, e.g. 136885 to "136,885". */
export function formatNumber(value: number): string {
  return Math.round(value).toLocaleString('en-US')
}

/** Compact LKR for tight spaces such as chart axes, e.g. "LKR 490M". */
export function formatLkrCompact(value: number): string {
  if (value >= 1_000_000_000) return `LKR ${(value / 1_000_000_000).toFixed(1)}B`
  if (value >= 1_000_000) return `LKR ${Math.round(value / 1_000_000)}M`
  if (value >= 1_000) return `LKR ${Math.round(value / 1_000)}K`
  return `LKR ${Math.round(value)}`
}

/** Compact visitor count for chart axes, e.g. 136885 to "137K". */
export function formatCountCompact(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `${Math.round(value / 1_000)}K`
  return String(Math.round(value))
}

export function toPercent(value: number, digits = 0): string {
  return `${(value * 100).toFixed(digits)}%`
}
