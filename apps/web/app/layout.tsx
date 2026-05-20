import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'BreatheSafe NG — Nigeria Air Quality Forecaster',
  description:
    'Real-time AQI monitoring and 24-hour forecasts for Nigerian cities',
  keywords: ['air quality', 'AQI', 'Nigeria', 'Lagos', 'Abuja', 'pollution'],
  openGraph: {
    title: 'BreatheSafe NG',
    description: 'Real-time air quality monitoring for Nigerian cities',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang='en'>
      <body className={`${inter.className} bg-gray-950 text-white antialiased`}>
        {children}
      </body>
    </html>
  );
}
