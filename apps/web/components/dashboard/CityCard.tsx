'use client';
import { CityStatus } from '@/lib/api';
import { getAQILevel, formatRelativeTime } from '@/lib/aqiUtils';
import clsx from 'clsx';

interface Props {
  city: CityStatus;
  isSelected: boolean;
  onClick: () => void;
}

export default function CityCard({ city, isSelected, onClick }: Props) {
  const level = city.aqi_value != null ? getAQILevel(city.aqi_value) : null;

  return (
    <button
      onClick={onClick}
      className={clsx(
        'w-full text-left rounded-2xl border p-4 transition-all duration-200',
        isSelected
          ? 'border-green-500/50 bg-green-950/20'
          : 'border-gray-800 bg-gray-900 hover:border-gray-700',
      )}
    >
      <div className='flex items-start justify-between gap-2'>
        <div>
          <p className='font-semibold text-white text-sm'>
            {city.display_name}
          </p>
          {city.last_updated && (
            <p className='text-gray-500 text-xs mt-0.5'>
              {formatRelativeTime(city.last_updated)}
            </p>
          )}
        </div>

        {city.aqi_value != null ? (
          <div className='flex flex-col items-end'>
            <span className='font-bold text-xl' style={{ color: city.color }}>
              {Math.round(city.aqi_value)}
            </span>
            <span
              className='text-xs px-2 py-0.5 rounded-full font-medium text-gray-900 mt-1'
              style={{ backgroundColor: city.color }}
            >
              {level?.label.split(' ')[0]}
            </span>
          </div>
        ) : (
          <span className='text-gray-600 text-sm'>No data</span>
        )}
      </div>
    </button>
  );
}
