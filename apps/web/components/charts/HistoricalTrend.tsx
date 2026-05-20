'use client';
import { useEffect, useState } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { fetchHistory, HistoricalPoint } from '@/lib/api';

interface Props {
  city: string;
  hours?: number;
}

export default function HistoricalTrend({ city, hours = 24 }: Props) {
  const [data, setData] = useState<HistoricalPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchHistory(city, hours)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [city, hours]);

  if (loading)
    return (
      <div className='h-48 flex items-center justify-center text-gray-500 text-sm'>
        Loading...
      </div>
    );
  if (!data.length)
    return (
      <div className='h-48 flex items-center justify-center text-gray-500 text-sm'>
        No history available
      </div>
    );

  const formatted = data.map((d) => ({
    ...d,
    time: new Date(d.timestamp_utc).toLocaleTimeString('en-NG', {
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Africa/Lagos',
    }),
  }));

  return (
    <ResponsiveContainer width='100%' height={200}>
      <AreaChart
        data={formatted}
        margin={{ top: 8, right: 16, left: -10, bottom: 0 }}
      >
        <defs>
          <linearGradient id='aqiGradient' x1='0' y1='0' x2='0' y2='1'>
            <stop offset='5%' stopColor='#22c55e' stopOpacity={0.3} />
            <stop offset='95%' stopColor='#22c55e' stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray='3 3' stroke='#1f2937' />
        <XAxis
          dataKey='time'
          tick={{ fill: '#6b7280', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          interval='preserveStartEnd'
        />
        <YAxis
          tick={{ fill: '#6b7280', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{
            background: '#1f2937',
            border: '1px solid #374151',
            borderRadius: 12,
          }}
          labelStyle={{ color: '#9ca3af', fontSize: 12 }}
          itemStyle={{ color: '#22c55e' }}
        />
        <Area
          type='monotone'
          dataKey='aqi_value'
          stroke='#22c55e'
          strokeWidth={2}
          fill='url(#aqiGradient)'
          name='AQI'
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
