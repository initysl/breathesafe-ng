'use client';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { ForecastPoint } from '@/lib/api';
import { formatTimestamp } from '@/lib/aqiUtils';

interface Props {
  forecasts: ForecastPoint[];
}

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className='bg-gray-800 border border-gray-700 rounded-xl p-3 text-sm shadow-xl'>
      <p className='text-gray-400 text-xs mb-1'>
        {formatTimestamp(d.forecast_for)}
      </p>
      <p className='font-bold text-white text-lg'>{d.predicted_aqi} AQI</p>
      <p style={{ color: d.color }} className='font-medium'>
        {d.predicted_category}
      </p>
    </div>
  );
};

export default function ForecastChart({ forecasts }: Props) {
  if (!forecasts.length) {
    return (
      <div className='h-48 flex items-center justify-center text-gray-500 text-sm'>
        No forecast data available
      </div>
    );
  }

  const data = forecasts.map((f) => ({
    ...f,
    label: `+${f.horizon_hours}h`,
  }));

  return (
    <ResponsiveContainer width='100%' height={220}>
      <LineChart
        data={data}
        margin={{ top: 8, right: 16, left: -10, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray='3 3' stroke='#1f2937' />
        <XAxis
          dataKey='label'
          tick={{ fill: '#6b7280', fontSize: 12 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          domain={[0, 300]}
          tick={{ fill: '#6b7280', fontSize: 12 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} />
        {/* AQI threshold lines */}
        <ReferenceLine
          y={50}
          stroke='#00e400'
          strokeDasharray='4 4'
          strokeOpacity={0.4}
        />
        <ReferenceLine
          y={100}
          stroke='#ffff00'
          strokeDasharray='4 4'
          strokeOpacity={0.4}
        />
        <ReferenceLine
          y={150}
          stroke='#ff7e00'
          strokeDasharray='4 4'
          strokeOpacity={0.4}
        />
        <ReferenceLine
          y={200}
          stroke='#ff0000'
          strokeDasharray='4 4'
          strokeOpacity={0.4}
        />
        <Line
          type='monotone'
          dataKey='predicted_aqi'
          stroke='#22c55e'
          strokeWidth={2.5}
          dot={(props: any) => (
            <circle
              key={props.index}
              cx={props.cx}
              cy={props.cy}
              r={5}
              fill={props.payload.color}
              stroke='#111827'
              strokeWidth={2}
            />
          )}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
