import Navbar from '@/components/layout/Navbar';
import Link from 'next/link';
import { LucideGitGraph } from 'lucide-react';

export default function AboutPage() {
  return (
    <div className='min-h-screen bg-gray-950'>
      <Navbar />
      <main className='max-w-3xl mx-auto px-4 py-12 flex flex-col gap-8 text-gray-300'>
        <div>
          <h1 className='text-3xl font-bold text-white mb-3'>
            About BreatheSafe NG
          </h1>
          <p className='leading-relaxed'>
            BreatheSafe NG is a machine learning-powered air quality monitoring
            and forecasting platform built specifically for Nigerian cities. We
            combine real-time sensor data from OpenAQ, satellite aerosol
            readings from NASA, and weather data from OpenWeatherMap to predict
            AQI up to 24 hours ahead.
          </p>
        </div>

        <div>
          <h2 className='text-white font-semibold text-lg mb-3'>
            Why it matters
          </h2>
          <p className='leading-relaxed'>
            Nigeria has some of the worst air quality in West Africa, yet almost
            no accessible, localized air quality tools exist for everyday
            Nigerians. Lagos alone recorded over 11,000 premature deaths from
            air pollution in 2018. BreatheSafe NG was built to change that —
            giving everyone free access to actionable air quality data.
          </p>
        </div>

        <div>
          <h2 className='text-white font-semibold text-lg mb-3'>
            How it works
          </h2>
          <ol className='flex flex-col gap-2 list-decimal list-inside text-gray-400 text-sm leading-relaxed'>
            <li>
              Hourly pollutant data is pulled from OpenAQ monitoring stations
              across Nigeria.
            </li>
            <li>
              Weather data (temperature, wind, humidity) is pulled from
              OpenWeatherMap.
            </li>
            <li>
              An XGBoost ML model trained on Nigerian pollution patterns
              generates 1h–24h forecasts.
            </li>
            <li>
              Alerts are dispatched via WhatsApp, SMS, or email when AQI crosses
              your threshold.
            </li>
          </ol>
        </div>

        <div>
          <h2 className='text-white font-semibold text-lg mb-3'>
            Cities covered
          </h2>
          <div className='grid grid-cols-2 sm:grid-cols-3 gap-2'>
            {[
              'Abuja',
              'Lagos',
              'Kano',
              'Port Harcourt',
              'Ibadan',
              'Osogbo',
            ].map((c) => (
              <div
                key={c}
                className='bg-gray-900 border border-gray-800 rounded-xl px-3 py-2 text-sm text-gray-300'
              >
                {c}
              </div>
            ))}
          </div>
        </div>

        <div className='flex gap-3'>
          <Link
            href='/dashboard'
            className='bg-green-600 hover:bg-green-500 text-white font-semibold px-6 py-2.5 rounded-xl text-sm transition-colors'
          >
            View Dashboard
          </Link>
          <a
            href='https://github.com'
            target='_blank'
            rel='noopener noreferrer'
            className='flex items-center gap-2 border border-gray-700 hover:border-gray-500 text-gray-300 px-6 py-2.5 rounded-xl text-sm transition-colors'
          >
            <LucideGitGraph className='w-4 h-4' />
            Source Code
          </a>
        </div>
      </main>
    </div>
  );
}
