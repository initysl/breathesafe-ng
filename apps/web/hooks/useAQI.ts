'use client';
import { useEffect, useCallback } from 'react';
import { fetchAllCities, fetchCityAQI, fetchForecast } from '@/lib/api';
import { useCityStore } from '@/store/cityStore';

// Poll every 5 minutes
const POLL_INTERVAL = 5 * 60 * 1000;

export function useAllCities() {
  const { setAllCities, setLoading } = useCityStore();

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchAllCities();
      setAllCities(data);
    } catch (err) {
      console.error('Failed to fetch all cities:', err);
    } finally {
      setLoading(false);
    }
  }, [setAllCities, setLoading]);

  useEffect(() => {
    load();
    const interval = setInterval(load, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [load]);
}

export function useCityAQI(city: string) {
  const { setCityAQI, setCityForecasts, setLoading, setLastUpdated } =
    useCityStore();

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const [aqi, forecast] = await Promise.all([
        fetchCityAQI(city),
        fetchForecast(city),
      ]);
      setCityAQI(aqi);
      setCityForecasts(forecast.forecasts);
      setLastUpdated(new Date());
    } catch (err) {
      console.error(`Failed to fetch AQI for ${city}:`, err);
    } finally {
      setLoading(false);
    }
  }, [city, setCityAQI, setCityForecasts, setLoading, setLastUpdated]);

  useEffect(() => {
    load();
    const interval = setInterval(load, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [load]);
}
