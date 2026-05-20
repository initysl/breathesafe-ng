'use client';
import { getAQILevel } from '@/lib/aqiUtils';

interface Props {
  aqi: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

const SIZE_MAP = {
  sm: { outer: 100, inner: 70, fontSize: 'text-xl', labelSize: 'text-xs' },
  md: { outer: 140, inner: 100, fontSize: 'text-3xl', labelSize: 'text-sm' },
  lg: { outer: 180, inner: 130, fontSize: 'text-4xl', labelSize: 'text-base' },
};

export default function AQIGauge({
  aqi,
  size = 'md',
  showLabel = true,
}: Props) {
  const level = getAQILevel(aqi);
  const dim = SIZE_MAP[size];

  // Arc calculation — 180° gauge (semicircle)
  const radius = dim.outer / 2 - 8;
  const cx = dim.outer / 2;
  const cy = dim.outer / 2;
  const circumference = Math.PI * radius; // half circle
  const pct = Math.min(aqi / 500, 1);
  const offset = circumference * (1 - pct);

  return (
    <div className='flex flex-col items-center gap-2'>
      <div
        className='relative'
        style={{ width: dim.outer, height: dim.outer / 2 + 16 }}
      >
        <svg
          width={dim.outer}
          height={dim.outer}
          viewBox={`0 0 ${dim.outer} ${dim.outer}`}
        >
          {/* Background arc */}
          <circle
            cx={cx}
            cy={cy}
            r={radius}
            fill='none'
            stroke='#1f2937'
            strokeWidth='12'
            strokeDasharray={`${circumference} ${circumference}`}
            strokeDashoffset={0}
            strokeLinecap='round'
            transform={`rotate(-180 ${cx} ${cy})`}
          />
          {/* Value arc */}
          <circle
            cx={cx}
            cy={cy}
            r={radius}
            fill='none'
            stroke={level.color}
            strokeWidth='12'
            strokeDasharray={`${circumference} ${circumference}`}
            strokeDashoffset={offset}
            strokeLinecap='round'
            transform={`rotate(-180 ${cx} ${cy})`}
            style={{ transition: 'stroke-dashoffset 0.8s ease' }}
          />
        </svg>

        {/* Center value */}
        <div className='absolute inset-0 flex flex-col items-center justify-end pb-2'>
          <span
            className={`font-bold ${dim.fontSize}`}
            style={{ color: level.color }}
          >
            {Math.round(aqi)}
          </span>
          <span className='text-gray-500 text-xs'>AQI</span>
        </div>
      </div>

      {showLabel && (
        <span
          className={`px-3 py-1 rounded-full text-xs font-semibold text-gray-900`}
          style={{ backgroundColor: level.color }}
        >
          {level.label}
        </span>
      )}
    </div>
  );
}
