import Link from 'next/link';
import { Wind, Bell, BarChart3, MapPin } from 'lucide-react';

export default function HomePage() {
  return (
    <main className='min-h-screen bg-gray-950 flex flex-col'>
      {/* Nav */}
      <nav className='border-b border-gray-800 px-6 py-4 flex items-center justify-between'>
        <div className='flex items-center gap-2'>
          <Wind className='text-green-400 w-6 h-6' />
          <span className='font-bold text-lg tracking-tight'>
            BreatheSafe NG
          </span>
        </div>
        <div className='flex items-center gap-4 text-sm text-gray-400'>
          <Link
            href='/dashboard'
            className='hover:text-white transition-colors'
          >
            Dashboard
          </Link>
          <Link href='/alerts' className='hover:text-white transition-colors'>
            Alerts
          </Link>
          <Link href='/about' className='hover:text-white transition-colors'>
            About
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className='flex-1 flex flex-col items-center justify-center text-center px-6 py-24 gap-8'>
        <div className='inline-flex items-center gap-2 bg-green-900/30 border border-green-700/40 rounded-full px-4 py-1.5 text-green-400 text-sm'>
          <span className='w-2 h-2 bg-green-400 rounded-full aqi-pulse'></span>
          Live data · 6 Nigerian cities
        </div>

        <h1 className='text-5xl md:text-7xl font-extrabold tracking-tight max-w-3xl leading-tight'>
          Know the air <br />
          <span className='text-green-400'>before you breathe it.</span>
        </h1>

        <p className='text-gray-400 max-w-xl text-lg leading-relaxed'>
          Real-time AQI monitoring and 24-hour pollution forecasts for Abuja,
          Lagos, Kano, Port Harcourt, Ibadan, and Osogbo.
        </p>

        <div className='flex flex-col sm:flex-row gap-4'>
          <Link
            href='/dashboard'
            className='bg-green-500 hover:bg-green-400 text-black font-semibold px-8 py-3 rounded-xl transition-colors'
          >
            View Dashboard
          </Link>
          <Link
            href='/alerts'
            className='border border-gray-700 hover:border-gray-500 text-white px-8 py-3 rounded-xl transition-colors'
          >
            Set Up Alerts
          </Link>
        </div>
      </section>

      {/* Feature Cards */}
      <section className='grid grid-cols-1 md:grid-cols-3 gap-4 px-6 pb-24 max-w-5xl mx-auto w-full'>
        {[
          {
            icon: <MapPin className='w-5 h-5 text-green-400' />,
            title: 'Live City Map',
            desc: 'Color-coded AQI map across all 6 cities updated every hour.',
          },
          {
            icon: <BarChart3 className='w-5 h-5 text-blue-400' />,
            title: '24-Hour Forecasts',
            desc: 'ML-powered predictions at 1h, 6h, 12h, and 24h horizons.',
          },
          {
            icon: <Bell className='w-5 h-5 text-yellow-400' />,
            title: 'WhatsApp Alerts',
            desc: 'Get notified instantly when air quality turns dangerous.',
          },
        ].map((f) => (
          <div
            key={f.title}
            className='bg-gray-900 border border-gray-800 rounded-2xl p-6 flex flex-col gap-3'
          >
            <div className='w-10 h-10 bg-gray-800 rounded-xl flex items-center justify-center'>
              {f.icon}
            </div>
            <h3 className='font-semibold text-white'>{f.title}</h3>
            <p className='text-gray-400 text-sm leading-relaxed'>{f.desc}</p>
          </div>
        ))}
      </section>

      {/* Footer */}
      <footer className='border-t border-gray-800 px-6 py-6 text-center text-gray-600 text-sm'>
        © {new Date().getFullYear()} BreatheSafe NG · Built for Nigerian cities
      </footer>
    </main>
  );
}
