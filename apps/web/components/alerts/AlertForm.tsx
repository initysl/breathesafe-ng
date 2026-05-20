'use client';
import { useState } from 'react';
import { subscribeAlert } from '@/lib/api';
import { CITIES } from '@/lib/aqiUtils';
import { Bell, CheckCircle } from 'lucide-react';
import clsx from 'clsx';

const CHANNELS = ['whatsapp', 'sms', 'email'];
const THRESHOLDS = [
  { value: 'moderate', label: 'Moderate (AQI 51+)' },
  { value: 'unhealthy_sensitive', label: 'Unhealthy for Sensitive (101+)' },
  { value: 'unhealthy', label: 'Unhealthy (151+)' },
  { value: 'very_unhealthy', label: 'Very Unhealthy (201+)' },
  { value: 'hazardous', label: 'Hazardous (301+)' },
];

export default function AlertForm() {
  const [city, setCity] = useState('lagos');
  const [channel, setChannel] = useState('whatsapp');
  const [contact, setContact] = useState('');
  const [threshold, setThreshold] = useState('unhealthy');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const contactLabel =
    channel === 'email'
      ? 'Email address'
      : 'Phone number (e.g. +2348012345678)';

  const handleSubmit = async () => {
    if (!contact.trim()) {
      setError('Please enter your contact.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await subscribeAlert({ city, channel, contact, threshold });
      setSuccess(true);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Something went wrong. Try again.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className='bg-green-950/40 border border-green-700/40 rounded-2xl p-6 flex flex-col items-center gap-3 text-center'>
        <CheckCircle className='w-10 h-10 text-green-400' />
        <p className='font-semibold text-white'>You're subscribed!</p>
        <p className='text-gray-400 text-sm'>
          We'll alert you on{' '}
          <span className='text-white capitalize'>{channel}</span> when{' '}
          <span className='text-white capitalize'>
            {city.replace('_', ' ')}
          </span>{' '}
          AQI turns{' '}
          <span className='text-white'>
            {THRESHOLDS.find((t) => t.value === threshold)?.label}
          </span>
          .
        </p>
        <button
          onClick={() => setSuccess(false)}
          className='text-green-400 text-sm hover:underline mt-1'
        >
          Add another
        </button>
      </div>
    );
  }

  return (
    <div className='bg-gray-900 border border-gray-800 rounded-2xl p-6 flex flex-col gap-4'>
      <div className='flex items-center gap-2 mb-1'>
        <Bell className='w-5 h-5 text-yellow-400' />
        <h3 className='font-semibold text-white'>Subscribe to AQI Alerts</h3>
      </div>

      {/* City */}
      <div className='flex flex-col gap-1.5'>
        <label className='text-gray-400 text-sm'>City</label>
        <select
          value={city}
          onChange={(e) => setCity(e.target.value)}
          className='bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-green-500'
        >
          {CITIES.map((c) => (
            <option key={c.key} value={c.key}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      {/* Channel */}
      <div className='flex flex-col gap-1.5'>
        <label className='text-gray-400 text-sm'>Alert channel</label>
        <div className='flex gap-2'>
          {CHANNELS.map((ch) => (
            <button
              key={ch}
              onClick={() => setChannel(ch)}
              className={clsx(
                'flex-1 py-2 rounded-xl text-sm font-medium capitalize transition-colors',
                channel === ch
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white',
              )}
            >
              {ch}
            </button>
          ))}
        </div>
      </div>

      {/* Contact */}
      <div className='flex flex-col gap-1.5'>
        <label className='text-gray-400 text-sm'>{contactLabel}</label>
        <input
          type={channel === 'email' ? 'email' : 'tel'}
          value={contact}
          onChange={(e) => setContact(e.target.value)}
          placeholder={
            channel === 'email' ? 'you@example.com' : '+234 801 234 5678'
          }
          className='bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm placeholder-gray-600 focus:outline-none focus:border-green-500'
        />
      </div>

      {/* Threshold */}
      <div className='flex flex-col gap-1.5'>
        <label className='text-gray-400 text-sm'>Alert when AQI is</label>
        <select
          value={threshold}
          onChange={(e) => setThreshold(e.target.value)}
          className='bg-gray-800 border border-gray-700 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-green-500'
        >
          {THRESHOLDS.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
      </div>

      {error && <p className='text-red-400 text-sm'>{error}</p>}

      <button
        onClick={handleSubmit}
        disabled={loading}
        className='w-full bg-green-600 hover:bg-green-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-semibold py-3 rounded-xl transition-colors text-sm'
      >
        {loading ? 'Subscribing...' : 'Subscribe'}
      </button>
    </div>
  );
}
