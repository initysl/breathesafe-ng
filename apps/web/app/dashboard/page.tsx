'use client';
import dynamic from 'next/dynamic';
import { useEffect } from 'react';
import { useCityStore } from '@/store/cityStore';
import { useAllCities, useCityAQI } from '@/hooks/useAQI';
import { CITIES } from '@/lib/aqiUtils';

import Navbar from '@/components/layout/Navbar';
import CityCard from '@/components/dashboard/CityCard';
import AQIGauge from '@/components/charts/AQIGauge';
import PollutantBreakdown from '@/components/charts/PollutantBreakdown';
import ForecastChart from '@/components/charts/ForecastChart';
import HealthAdvice from '@/components/dashboard/HealthAdvice';
import WeatherPanel from '@/components/dashboard/WeatherPanel';
import AlertBanner from '@/components/alerts/AlertBanner';
import AQILegend from '@/components/map/AQILegend';
import { RefreshCw } from 'lucide-react';

// Dynamically import map (SSR disabled — Leaflet needs browser)
const AQIMap = dynamic(() => import('@/components/map/AQIMap'), { ssr: false });

export default function DashboardPage() {
  const {
    selectedCity,
    allCities,
    cityAQI,
    cityForecasts,
    isLoading,
    lastUpdated,
    setSelectedCity,
  } = useCityStore();

  useAllCities();
  useCityAQI(selectedCity);

  const selectedMeta = CITIES.find((c) => c.key === selectedCity);

  return (
    <div className='min-h-screen bg-gray-950'>
      <Navbar />

      <main className='max-w-7xl mx-auto px-4 py-6 grid grid-cols-1 lg:grid-cols-3 gap-6'>
        {/* LEFT COLUMN — City list */}
        <aside className='flex flex-col gap-3'>
          <div className='flex items-center justify-between'>
            <h2 className='font-semibold text-white'>Cities</h2>
            {lastUpdated && (
              <span className='text-gray-500 text-xs flex items-center gap-1'>
                <RefreshCw className='w-3 h-3' />
                {lastUpdated.toLocaleTimeString('en-NG', {
                  timeZone: 'Africa/Lagos',
                  timeStyle: 'short',
                })}
              </span>
            )}
          </div>

          {allCities.length === 0
            ? Array(6)
                .fill(0)
                .map((_, i) => (
                  <div
                    key={i}
                    className='h-20 bg-gray-900 rounded-2xl border border-gray-800 animate-pulse'
                  />
                ))
            : allCities.map((c) => (
                <CityCard
                  key={c.city}
                  city={c}
                  isSelected={c.city === selectedCity}
                  onClick={() => setSelectedCity(c.city)}
                />
              ))}
        </aside>

        {/* CENTER COLUMN — Map + AQI detail */}
        <div className='lg:col-span-2 flex flex-col gap-5'>
          {/* Alert banner */}
          {cityAQI && cityAQI.aqi_value > 150 && (
            <AlertBanner
              city={cityAQI.city}
              aqi={cityAQI.aqi_value}
              category={cityAQI.aqi_category}
              advice={cityAQI.advice}
            />
          )}

          {/* Map */}
          <div className='relative h-72 md:h-80 rounded-2xl overflow-hidden border border-gray-800'>
            <AQIMap cities={allCities} onCitySelect={setSelectedCity} />
            <div className='absolute bottom-3 left-3 z-400'>
              <AQILegend />
            </div>
          </div>

          {/* City AQI detail */}
          {cityAQI ? (
            <div className='grid grid-cols-1 md:grid-cols-2 gap-5'>
              {/* Gauge + advice */}
              <div className='bg-gray-900 border border-gray-800 rounded-2xl p-5 flex flex-col gap-4'>
                <div className='flex items-center justify-between'>
                  <div>
                    <h3 className='font-bold text-white text-lg'>
                      {selectedMeta?.name}
                    </h3>
                    <p className='text-gray-500 text-sm'>Current air quality</p>
                  </div>
                  <AQIGauge aqi={cityAQI.aqi_value} size='sm' />
                </div>
                <WeatherPanel aqi={cityAQI} />
                <HealthAdvice aqi={cityAQI.aqi_value} advice={cityAQI.advice} />
              </div>

              {/* Forecast */}
              <div className='bg-gray-900 border border-gray-800 rounded-2xl p-5 flex flex-col gap-3'>
                <h3 className='font-semibold text-white'>24-Hour Forecast</h3>
                <ForecastChart forecasts={cityForecasts} />
              </div>

              {/* Pollutant breakdown */}
              <div className='md:col-span-2 bg-gray-900 border border-gray-800 rounded-2xl p-5 flex flex-col gap-4'>
                <h3 className='font-semibold text-white'>
                  Pollutant Breakdown
                </h3>
                <PollutantBreakdown aqi={cityAQI} />
              </div>
            </div>
          ) : (
            <div className='bg-gray-900 border border-gray-800 rounded-2xl p-10 flex items-center justify-center'>
              {isLoading ? (
                <div className='w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin' />
              ) : (
                <p className='text-gray-500'>Select a city to view details</p>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
