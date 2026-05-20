'use client';
import { useState, useEffect } from 'react';
import Navbar from '@/components/layout/Navbar';
import ForecastChart from '@/components/charts/ForecastChart';
import HistoricalTrend from '@/components/charts/HistoricalTrend';
import { CITIES } from '@/lib/aqiUtils';
import { fetchForecast, ForecastPoint } from '@/lib/api';

const HORIZONS = [
  { label: '1 Hour', value: 1 },
  { label: '6 Hours', value: 6 },
  { label: '12 Hours', value: 12 },
  { label: '24 Hours', value: 24 },
];

export default function ForecastPage() {
  const [city, setCity] = useState('lagos');
  const [forecasts, setForecasts] = useState<ForecastPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [histHours, setHistHours] = useState(24);

  useEffect(() => {
    setLoading(true);
    fetchForecast(city)
      .then((d) => setForecasts(d.forecasts))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [city]);

  return (
    <div className='min-h-screen bg-gray-950'>
      <Navbar />
      <main className='max-w-5xl mx-auto px-4 py-8 flex flex-col gap-6'>
        <div className='flex items-center justify-between flex-wrap gap-3'>
          <h1 className='text-2xl font-bold text-white'>AQI Forecast</h1>
          <select
            value={city}
            onChange={(e) => setCity(e.target.value)}
            className='bg-gray-800 border border-gray-700 text-white rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-green-500'
          >
            {CITIES.map((c) => (
              <option key={c.key} value={c.key}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        {/* Forecast chart */}
        <div className='bg-gray-900 border border-gray-800 rounded-2xl p-5 flex flex-col gap-3'>
          <h2 className='font-semibold text-white'>Predicted AQI</h2>
          <p className='text-gray-500 text-sm'>
            1h, 6h, 12h, and 24h ahead forecasts
          </p>
          {loading ? (
            <div className='h-48 flex items-center justify-center'>
              <div className='w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin' />
            </div>
          ) : (
            <ForecastChart forecasts={forecasts} />
          )}
        </div>

        {/* Forecast cards */}
        {!loading && forecasts.length > 0 && (
          <div className='grid grid-cols-2 sm:grid-cols-4 gap-3'>
            {forecasts.map((f) => (
              <div
                key={f.horizon_hours}
                className='bg-gray-900 border border-gray-800 rounded-2xl p-4 flex flex-col gap-1 items-center text-center'
              >
                <p className='text-gray-500 text-xs'>+{f.horizon_hours}h</p>
                <p className='text-2xl font-bold' style={{ color: f.color }}>
                  {Math.round(f.predicted_aqi)}
                </p>
                <p className='text-xs font-medium' style={{ color: f.color }}>
                  {f.predicted_category.split(' ')[0]}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Historical trend */}
        <div className='bg-gray-900 border border-gray-800 rounded-2xl p-5 flex flex-col gap-3'>
          <div className='flex items-center justify-between flex-wrap gap-2'>
            <h2 className='font-semibold text-white'>Historical AQI</h2>
            <div className='flex gap-2'>
              {[24, 48, 168].map((h) => (
                <button
                  key={h}
                  onClick={() => setHistHours(h)}
                  className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                    histHours === h
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-800 text-gray-400 hover:text-white'
                  }`}
                >
                  {h === 168 ? '7d' : `${h}h`}
                </button>
              ))}
            </div>
          </div>
          <HistoricalTrend city={city} hours={histHours} />
        </div>
      </main>
    </div>
  );
}
