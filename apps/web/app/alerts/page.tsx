import Navbar from '@/components/layout/Navbar';
import AlertForm from '@/components/alerts/AlertForm';
import { Bell, Shield, Zap } from 'lucide-react';

export default function AlertsPage() {
  return (
    <div className='min-h-screen bg-gray-950'>
      <Navbar />
      <main className='max-w-4xl mx-auto px-4 py-10 grid grid-cols-1 md:grid-cols-2 gap-8 items-start'>
        {/* Left — info */}
        <div className='flex flex-col gap-6'>
          <div>
            <h1 className='text-3xl font-bold text-white mb-3'>
              Stay Protected
            </h1>
            <p className='text-gray-400 leading-relaxed'>
              Get notified the moment air quality in your city turns dangerous.
              Choose your preferred channel — WhatsApp, SMS, or Email.
            </p>
          </div>

          <div className='flex flex-col gap-4'>
            {[
              {
                icon: <Zap className='w-5 h-5 text-yellow-400' />,
                title: 'Instant Alerts',
                desc: 'Notifications sent within minutes of AQI crossing your threshold.',
              },
              {
                icon: <Bell className='w-5 h-5 text-green-400' />,
                title: 'No Spam',
                desc: 'Maximum one alert per 6 hours per city. Only when it matters.',
              },
              {
                icon: <Shield className='w-5 h-5 text-blue-400' />,
                title: "You're in Control",
                desc: 'Unsubscribe any time. Choose your own AQI threshold.',
              },
            ].map((f) => (
              <div key={f.title} className='flex gap-3 items-start'>
                <div className='w-9 h-9 bg-gray-800 rounded-xl flex items-center justify-center shrink-0'>
                  {f.icon}
                </div>
                <div>
                  <p className='font-semibold text-white text-sm'>{f.title}</p>
                  <p className='text-gray-500 text-sm mt-0.5'>{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right — form */}
        <AlertForm />
      </main>
    </div>
  );
}
