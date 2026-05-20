import { Thermometer, Droplets, Wind } from 'lucide-react';
import { AQIReading } from '@/lib/api';

interface Props {
  aqi: AQIReading;
}

export default function WeatherPanel({ aqi }: Props) {
  const stats = [
    {
      icon: <Thermometer className='w-4 h-4 text-orange-400' />,
      label: 'Temp',
      value:
        aqi.temperature_c != null ? `${aqi.temperature_c.toFixed(1)}°C` : '—',
    },
    {
      icon: <Droplets className='w-4 h-4 text-blue-400' />,
      label: 'Humidity',
      value: aqi.humidity_pct != null ? `${aqi.humidity_pct.toFixed(0)}%` : '—',
    },
  ];

  return (
    <div className='flex gap-3'>
      {stats.map((s) => (
        <div
          key={s.label}
          className='flex-1 bg-gray-800/50 rounded-xl p-3 flex items-center gap-2'
        >
          {s.icon}
          <div>
            <p className='text-gray-500 text-xs'>{s.label}</p>
            <p className='text-white font-semibold text-sm'>{s.value}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
