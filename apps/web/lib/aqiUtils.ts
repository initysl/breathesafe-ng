export const CITIES = [
  { key: 'abuja', name: 'Abuja', lat: 9.0765, lng: 7.3986 },
  { key: 'lagos', name: 'Lagos', lat: 6.5244, lng: 3.3792 },
  { key: 'kano', name: 'Kano', lat: 12.0022, lng: 8.5919 },
  { key: 'port_harcourt', name: 'Port Harcourt', lat: 4.8156, lng: 7.0498 },
  { key: 'ibadan', name: 'Ibadan', lat: 7.3776, lng: 3.947 },
  { key: 'osogbo', name: 'Osogbo', lat: 7.7719, lng: 4.5624 },
];

export const AQI_LEVELS = [
  {
    label: 'Good',
    range: '0–50',
    color: '#00e400',
    bg: 'bg-green-100',
    text: 'text-green-800',
  },
  {
    label: 'Moderate',
    range: '51–100',
    color: '#ffff00',
    bg: 'bg-yellow-100',
    text: 'text-yellow-800',
  },
  {
    label: 'Unhealthy for Sensitive Groups',
    range: '101–150',
    color: '#ff7e00',
    bg: 'bg-orange-100',
    text: 'text-orange-800',
  },
  {
    label: 'Unhealthy',
    range: '151–200',
    color: '#ff0000',
    bg: 'bg-red-100',
    text: 'text-red-800',
  },
  {
    label: 'Very Unhealthy',
    range: '201–300',
    color: '#8f3f97',
    bg: 'bg-purple-100',
    text: 'text-purple-800',
  },
  {
    label: 'Hazardous',
    range: '301+',
    color: '#7e0023',
    bg: 'bg-rose-100',
    text: 'text-rose-900',
  },
];

export function getAQILevel(aqi: number) {
  if (aqi <= 50) return AQI_LEVELS[0];
  if (aqi <= 100) return AQI_LEVELS[1];
  if (aqi <= 150) return AQI_LEVELS[2];
  if (aqi <= 200) return AQI_LEVELS[3];
  if (aqi <= 300) return AQI_LEVELS[4];
  return AQI_LEVELS[5];
}

export function formatTimestamp(ts: string): string {
  return new Date(ts).toLocaleString('en-NG', {
    timeZone: 'Africa/Lagos',
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

export function formatRelativeTime(ts: string): string {
  const diffMs = Date.now() - new Date(ts).getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  const hrs = Math.floor(diffMins / 60);
  return `${hrs}h ago`;
}
