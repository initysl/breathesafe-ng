import { AQI_LEVELS } from '@/lib/aqiUtils';

export default function AQILegend() {
  return (
    <div className='bg-gray-900/95 backdrop-blur border border-gray-800 rounded-xl p-3 flex flex-col gap-1.5'>
      <p className='text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1'>
        AQI Scale
      </p>
      {AQI_LEVELS.map((level) => (
        <div key={level.label} className='flex items-center gap-2'>
          <div
            className='w-3 h-3 rounded-full shrink-0'
            style={{ backgroundColor: level.color }}
          />
          <span className='text-gray-300 text-xs'>{level.label}</span>
          <span className='text-gray-600 text-xs ml-auto'>{level.range}</span>
        </div>
      ))}
    </div>
  );
}
