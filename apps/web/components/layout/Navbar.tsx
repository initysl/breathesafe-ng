'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Wind } from 'lucide-react';
import clsx from 'clsx';

const LINKS = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/forecast', label: 'Forecast' },
  { href: '/alerts', label: 'Alerts' },
  { href: '/about', label: 'About' },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className='sticky top-0 z-50 bg-gray-950/90 backdrop-blur border-b border-gray-800 px-6 py-4'>
      <div className='max-w-7xl mx-auto flex items-center justify-between'>
        <Link
          href='/'
          className='flex items-center gap-2 font-bold text-lg tracking-tight'
        >
          <Wind className='text-green-400 w-5 h-5' />
          BreatheSafe NG
        </Link>

        <div className='flex items-center gap-1'>
          {LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={clsx(
                'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                pathname === link.href
                  ? 'bg-gray-800 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/50',
              )}
            >
              {link.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
