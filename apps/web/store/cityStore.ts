import { create } from 'zustand';
import { CityStatus, AQIReading, ForecastPoint } from '@/lib/api';

interface CityStore {
  selectedCity: string;
  allCities: CityStatus[];
  cityAQI: AQIReading | null;
  cityForecasts: ForecastPoint[];
  isLoading: boolean;
  lastUpdated: Date | null;
  setSelectedCity: (city: string) => void;
  setAllCities: (cities: CityStatus[]) => void;
  setCityAQI: (aqi: AQIReading | null) => void;
  setCityForecasts: (forecasts: ForecastPoint[]) => void;
  setLoading: (loading: boolean) => void;
  setLastUpdated: (date: Date) => void;
}

export const useCityStore = create<CityStore>((set) => ({
  selectedCity: 'lagos',
  allCities: [],
  cityAQI: null,
  cityForecasts: [],
  isLoading: false,
  lastUpdated: null,
  setSelectedCity: (city) => set({ selectedCity: city }),
  setAllCities: (cities) => set({ allCities: cities }),
  setCityAQI: (aqi) => set({ cityAQI: aqi }),
  setCityForecasts: (forecasts) => set({ cityForecasts: forecasts }),
  setLoading: (loading) => set({ isLoading: loading }),
  setLastUpdated: (date) => set({ lastUpdated: date }),
}));
