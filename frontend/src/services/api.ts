import axios, { AxiosError } from 'axios'
import type {
  CrowdRiskPrediction,
  CrowdRiskSummary,
  DemandForecastResponse,
  DestinationInfo,
  DestinationProfile,
  DestinationRecommendation,
  HistoricalRecord,
  IntegratedResponse,
  ModelComparisonResponse,
  RecommendationRequest,
  ResultImage,
  SeasonalPlanResponse,
  SimilarDestination,
} from '../types'

export const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 20000,
  headers: { 'Content-Type': 'application/json' },
})

interface ApiErrorBody {
  error?: boolean
  message?: string
  detail?: string
}

// Convert any Axios error into a user-friendly Error.
function toFriendlyError(err: unknown): Error {
  const axErr = err as AxiosError<ApiErrorBody>
  if (axErr.response) {
    const body = axErr.response.data
    if (body && body.message) return new Error(body.message)
    return new Error('The server could not complete your request. Please try again.')
  }
  if (axErr.request) {
    return new Error('Unable to connect to the server. Please ensure the backend is running.')
  }
  return new Error('Something went wrong. Please try again.')
}

async function run<T>(promise: Promise<{ data: T }>): Promise<T> {
  try {
    const res = await promise
    return res.data
  } catch (err) {
    throw toFriendlyError(err)
  }
}

// ── Module 1 — Demand & Revenue Forecast ──
export const getModule1Forecast = (destination: string, year: number, month: number) =>
  run<DemandForecastResponse>(
    client.get(`/api/module1/forecast/${encodeURIComponent(destination)}/${year}/${month}`),
  )

export const getModule1Yearly = (destination: string, year: number) =>
  run<DemandForecastResponse[]>(
    client.get(`/api/module1/yearly/${encodeURIComponent(destination)}/${year}`),
  )

export const getModule1Comparison = () =>
  run<ModelComparisonResponse>(client.get('/api/module1/comparison'))

export const getModule1AllDestinations = (year: number, month: number) =>
  run<DemandForecastResponse[]>(client.get(`/api/module1/all/${year}/${month}`))

export const getModule1Historical = (destination: string) =>
  run<HistoricalRecord[]>(client.get(`/api/module1/historical/${encodeURIComponent(destination)}`))

// ── Module 2 ──
export const getModule2Destinations = () =>
  run<DestinationInfo[]>(client.get('/api/module2/destinations'))

export const getSeasonalPlan = (destination: string, year: number, month: number) =>
  run<SeasonalPlanResponse>(
    client.get(`/api/module2/plan/${encodeURIComponent(destination)}/${year}/${month}`),
  )

export const getMonthlyPlan = (destination: string, year: number) =>
  run<SeasonalPlanResponse[]>(
    client.get(`/api/module2/monthly/${encodeURIComponent(destination)}/${year}`),
  )

// ── Module 3 — Crowd Risk ──
export const getModule3Predictions = (coreOnly = false) =>
  run<CrowdRiskPrediction[]>(
    client.get('/api/module3/predictions', { params: { core_only: coreOnly } }),
  )

export const getModule3Prediction = (destination: string) =>
  run<CrowdRiskPrediction>(
    client.get(`/api/module3/predictions/${encodeURIComponent(destination)}`),
  )

export const getModule3Summary = () =>
  run<CrowdRiskSummary>(client.get('/api/module3/summary'))

// ── Module 4 ──
export const getModule4Destinations = () =>
  run<DestinationProfile[]>(client.get('/api/module4/destinations'))

export const getRecommendations = (req: RecommendationRequest) =>
  run<DestinationRecommendation[]>(client.post('/api/module4/recommend', req))

export const getSimilarDestinations = (destination: string, topN = 4) =>
  run<SimilarDestination[]>(
    client.get(`/api/module4/similar/${encodeURIComponent(destination)}`, { params: { top_n: topN } }),
  )

export const getDestinationProfile = (name: string) =>
  run<DestinationProfile>(client.get(`/api/module4/destination/${encodeURIComponent(name)}`))

// ── Integrated ──
export const getIntegratedRecommendations = (req: RecommendationRequest) =>
  run<IntegratedResponse>(client.post('/api/integrated/recommend', req))

// ── Results ──
export const getModule1Results = () =>
  run<ResultImage[]>(client.get('/api/results/module1'))

export const getModule2Results = () =>
  run<ResultImage[]>(client.get('/api/results/module2'))

export const getModule3Results = () =>
  run<ResultImage[]>(client.get('/api/results/module3'))

export const getModule4Results = () =>
  run<ResultImage[]>(client.get('/api/results/module4'))
