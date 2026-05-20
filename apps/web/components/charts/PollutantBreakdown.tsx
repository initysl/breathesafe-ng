'use client';
import { AQIReading } from '@/lib/api';

interface Props {
  aqi: AQIReading;
}

const POLLUTANTS = [
  { key: 'pm25', label: 'PM2.5', unit: 'µg/m³', limit: 15, color: '#f97316' },
  { key: 'pm10', label: 'PM10', unit: 'µg/m³', limit: 45, color: '#eab308' },
  { key: 'no2', label: 'NO₂', unit: 'µg/m³', limit: 25, color: '#8b5cf6' },
  { key: 'o3', label: 'O₃', unit: 'µg/m³', limit: 100, color: '#06b6d4' },
  { key: 'co', label: 'CO', unit: 'mg/m³', limit: 4, color: '#ef4444' },
  { key: 'so2', label: 'SO₂', unit: 'µg/m³', limit: 40, color: '#ec4899' },
];

export default function PollutantBreakdown({ aqi }: Props) {
  return (
    <div className='grid grid-cols-2 sm:grid-cols-3 gap-3'>
      {POLLUTANTS.map((p) => {
        const value = aqi[p.key as keyof AQIReading] as number | null;
        const pct =
          value != null ? Math.min((value / (p.limit * 2)) * 100, 100) : 0;

        return (
          <div
            key={p.key}
            className='bg-gray-800/50 rounded-xl p-3 flex flex-col gap-2'
          >
            <div className='flex items-center justify-between'>
              <span className='text-gray-400 text-xs font-medium'>
                {p.label}
              </span>
              <span className='text-xs text-gray-500'>{p.unit}</span>
            </div>
            <span className='text-white font-bold text-lg'>
              {value != null ? value.toFixed(1) : '—'}
            </span>
            {/* Progress bar vs WHO limit */}
            <div className='h-1.5 bg-gray-700 rounded-full overflow-hidden'>
              <div
                className='h-full rounded-full transition-all duration-500'
                style={{ width: `${pct}%`, backgroundColor: p.color }}
              />
            </div>
            <span className='text-gray-600 text-xs'>WHO limit: {p.limit}</span>
          </div>
        );
      })}
    </div>
  );
}
