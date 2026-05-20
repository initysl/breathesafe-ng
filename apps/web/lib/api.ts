import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
});

// ── Types ──────────────────────────────────────────────
export interface AQIReading {
  city: string;
  aqi_value: number;
  aqi_category: string;
  pm25: number | null;
  pm10: number | null;
  no2: number | null;
  o3: number | null;
  co: number | null;
  so2: number | null;
  temperature_c: number | null;
  humidity_pct: number | null;
  timestamp_utc: string;
  color: string;
  advice: string;
}

export interface ForecastPoint {
  forecast_for: string;
  horizon_hours: number;
  predicted_aqi: number;
  predicted_category: string;
  color: string;
}

export interface CityStatus {
  city: string;
  display_name: string;
  aqi_value: number | null;
  aqi_category: string | null;
  color: string;
  latitude: number;
  longitude: number;
  last_updated: string | null;
}

export interface HistoricalPoint {
  timestamp_utc: string;
  aqi_value: number;
  pm25: number | null;
  temperature_c: number | null;
  humidity_pct: number | null;
}

//  API calls
export const fetchAllCities = (): Promise<CityStatus[]> =>
  api.get('/aqi').then((r) => r.data);
export const fetchCityAQI = (city: string): Promise<AQIReading> =>
  api.get(`/aqi/${city}`).then((r) => r.data);
export const fetchForecast = (
  city: string,
): Promise<{ city: string; forecasts: ForecastPoint[] }> =>
  api.get(`/forecast/${city}`).then((r) => r.data);
export const fetchHistory = (
  city: string,
  hours = 24,
): Promise<HistoricalPoint[]> =>
  api.get(`/aqi/${city}/history?hours=${hours}`).then((r) => r.data);
export const subscribeAlert = (payload: {
  city: string;
  channel: string;
  contact: string;
  threshold: string;
}) => api.post('/alerts/subscribe', payload).then((r) => r.data);
