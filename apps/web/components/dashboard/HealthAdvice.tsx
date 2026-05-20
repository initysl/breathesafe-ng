import { AlertTriangle, CheckCircle, Info } from 'lucide-react';
import { getAQILevel } from '@/lib/aqiUtils';

interface Props {
  aqi: number;
  advice: string;
}

export default function HealthAdvice({ aqi, advice }: Props) {
  const level = getAQILevel(aqi);

  const Icon = aqi <= 50 ? CheckCircle : aqi <= 100 ? Info : AlertTriangle;

  return (
    <div
      className='rounded-2xl border p-4 flex gap-3 items-start'
      style={{
        borderColor: `${level.color}40`,
        backgroundColor: `${level.color}0d`,
      }}
    >
      <Icon
        className='w-5 h-5 mt-0.5 shrink-0'
        style={{ color: level.color }}
      />
      <div>
        <p className='font-semibold text-sm' style={{ color: level.color }}>
          {level.label}
        </p>
        <p className='text-gray-300 text-sm mt-1 leading-relaxed'>{advice}</p>
      </div>
    </div>
  );
}
