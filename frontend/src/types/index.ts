// TypeScript interfaces matching the backend schemas exactly.

export interface DestinationInfo {
  destination: string
  dest_type: string
  district: string
  climate_zone: string
  elevation_m: number
}

/** Weighted contributions that make up the travel suitability score. */
export interface SeasonalScoreBreakdown {
  weather_component: number
  season_component: number
  event_component: number
  holiday_component: number
  accessibility_component: number
}

export interface SeasonalPlanResponse {
  destination: string
  year: number
  month: number
  month_name: string

  // Core output
  suitability_label: 'BEST' | 'GOOD' | 'AVOID'
  travel_suitability_score: number
  recommendation_summary: string
  season_reason: string

  // Score breakdown
  score_breakdown: SeasonalScoreBreakdown

  // Weather detail
  weather_suitability_score: number
  weather_verdict: string
  avg_temp_c: number
  total_rainfall_mm: number
  rain_risk: string
  rainy_days: number
  avg_humidity_pct: number
  sunshine_hours: number
  comfort_index: number

  // Seasonal context
  season: string
  is_peak_national: boolean
  is_best_period: boolean
  festival_name: string
  tourism_event_score: number
  holiday_count: number

  // Practical planning
  best_activities: string[]
  packing_advice: string[]
  things_to_note: string[]
  sea_condition: string

  // Destination meta
  dest_type: string
  climate_zone: string
  avg_stay_days: number

  // Crowd context, produced by Module 3 and shown as external information only
  crowd_context_level: 'LOW' | 'MEDIUM' | 'HIGH'
  crowd_context_note: string
  crowd_event_note: string
  is_off_season: boolean
}

export interface RecommendationRequest {
  preferred_type: string
  crowd_tolerance: string
  travel_month: number
  travel_year: number
  trip_budget: string
  travel_party: string
  weather_preference: string
  activity_preference: string
  top_n: number
}

export interface ScoreBreakdown {
  predicted_rating: number
  content_similarity: number
  crowd_compatibility: number
  seasonal_suitability: number
}

export interface DestinationRecommendation {
  rank: number
  destination: string
  recommendation_score: number
  predicted_rating: number
  content_similarity_score: number
  crowd_risk_level: 'LOW' | 'MEDIUM' | 'HIGH'
  crowd_score: number
  predicted_arrivals: number
  estimated_revenue_lkr: number
  avg_tss: number
  avg_wss: number
  weather_label: string
  season_suitability: 'BEST' | 'GOOD' | 'AVOID'
  season_reason: string
  why_recommended: string
  activities: string[]
  avg_stay_days: number
  best_months: string[]
  dest_type: string
  district: string
  is_off_season: boolean
  crowd_event_note: string
  score_breakdown: ScoreBreakdown
}

export interface SimilarDestination {
  destination: string
  similarity_score: number
  dest_type: string
  district: string
}

export interface DestinationProfile {
  destination: string
  dest_type: string
  district: string
  climate_zone: string
  beach_score: number
  culture_score: number
  nature_score: number
  adventure_score: number
  accessibility_score: number
  avg_stay_days: number
  best_months: string[]
  activities: string[]
  avg_cost_level: string
  family_friendly: boolean
}

export interface Module1Output {
  destination: string
  predicted_arrivals: number
  predicted_foreign_visitors: number
  predicted_local_visitors: number
  estimated_revenue_lkr: number
}

// ── Module 1 — Demand & Revenue Forecast ──
export interface DemandForecastResponse {
  destination: string
  year: number
  month: number
  month_name: string

  // Demand
  predicted_tourist_arrivals: number
  predicted_foreign_visitors: number
  predicted_local_visitors: number
  confidence_lower: number
  confidence_upper: number

  // Revenue
  estimated_revenue_lkr: number
  estimated_foreign_revenue_lkr: number
  estimated_local_revenue_lkr: number

  // Context
  national_arrivals: number
  model_used: string
  mape_pct: number
  data_source: string
  forecast_horizon_years: number
  national_lower: number
  national_upper: number
}

export interface ModelComparisonResponse {
  arima_order: number[]
  arima_mape: number
  arima_mae: number
  arima_rmse: number
  sarima_order: number[]
  sarima_seasonal_order: number[]
  sarima_mape: number
  sarima_mae: number
  sarima_rmse: number
  selected_model: string
  excluded_years: number[]
  train_period: string
  train_months: number
}

export interface HistoricalRecord {
  year: number
  destination: string
  foreign_visitors: number
  local_visitors: number
  total_visitors: number
  foreign_income_lkr: number
  local_income_lkr: number
  total_revenue_lkr: number
}

export interface Module2Output {
  destination: string
  travel_suitability_score: number
  suitability_label: 'BEST' | 'GOOD' | 'AVOID'
  season: string
  weather_verdict: string
  recommendation_summary: string
  season_reason: string
}

export interface Module3Output {
  destination: string
  crowd_risk_level: 'LOW' | 'MEDIUM' | 'HIGH'
  crowd_score: number
  recommendation_action: string
}

// ── Module 3 — Crowd Risk (real, trained on Google Trends + Wikipedia signal) ──
export interface CrowdRiskPrediction {
  destination: string
  is_core_destination: boolean
  last_known_month: string
  predicted_month: string
  latest_interest_index: number
  predicted_interest_index: number
  predicted_change_pct: number
  crowd_risk_level: 'Low' | 'Medium' | 'High'
  crowd_score_0_100: number
  recommendation_action: string
  model_used: string
}

export interface CrowdRiskSummary {
  total_tracked: number
  core_destination_count: number
  low_count: number
  medium_count: number
  high_count: number
  naive_mape_pct: number
  ensemble_mape_pct: number
}

export interface IntegratedResponse {
  travel_month: number
  month_name: string
  module1: Module1Output[]
  module2: Module2Output[]
  module3: Module3Output[]
  module4: DestinationRecommendation[]
}

export interface ResultImage {
  filename: string
  title: string
  description: string
  url: string
}

export interface HealthResponse {
  status: string
  models_loaded: boolean
}
