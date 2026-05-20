'use client';
import { AlertTriangle, X } from 'lucide-react';
import { useState } from 'react';

interface Props {
  city: string;
  aqi: number;
  category: string;
  advice: string;
}

export default function AlertBanner({ city, aqi, category, advice }: Props) {
  const [dismissed, setDismissed] = useState(false);
  if (dismissed || aqi <= 150) return null;

  return (
    <div className='bg-red-950/60 border border-red-700/50 rounded-2xl p-4 flex gap-3 items-start'>
      <AlertTriangle className='w-5 h-5 text-red-400 shrink-0 mt-0.5' />
      <div className='flex-1'>
        <p className='font-semibold text-red-300 text-sm'>
          Air Quality Alert — {city}
        </p>
        <p className='text-gray-300 text-sm mt-1'>{advice}</p>
      </div>
      <button
        onClick={() => setDismissed(true)}
        className='text-gray-500 hover:text-white'
      >
        <X className='w-4 h-4' />
      </button>
    </div>
  );
}
