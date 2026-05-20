'use client';
import { useEffect } from 'react';
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
  useMap,
} from 'react-leaflet';
import type { LatLngExpression } from 'leaflet';
import { CityStatus } from '@/lib/api';
import { CITIES } from '@/lib/aqiUtils';
import { useCityStore } from '@/store/cityStore';

interface Props {
  cities: CityStatus[];
  onCitySelect: (city: string) => void;
}

function MapController({ city }: { city: string }) {
  const map = useMap();
  const cityMeta = CITIES.find((c) => c.key === city);
  useEffect(() => {
    if (cityMeta) {
      const pos: LatLngExpression = [cityMeta.lat, cityMeta.lng];
      map.flyTo(pos, 9, { duration: 1.2 });
    }
  }, [city, cityMeta, map]);
  return null;
}

export default function AQIMap({ cities, onCitySelect }: Props) {
  const selectedCity = useCityStore((s) => s.selectedCity);
  const getCityData = (key: string) => cities.find((c) => c.city === key);

  const NIGERIA: LatLngExpression = [9.082, 8.6753];

  return (
    <MapContainer
      {...({ center: NIGERIA, zoom: 6 } as any)}
      style={{ height: '100%', width: '100%' }}
      zoomControl={true}
    >
      <TileLayer
        {...({
          url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
          attribution: '© OpenStreetMap © CARTO',
        } as any)}
      />

      <MapController city={selectedCity} />

      {CITIES.map((city) => {
        const data = getCityData(city.key);
        const aqi = data?.aqi_value ?? 0;
        const color = data?.color ?? '#6b7280';
        const isSelected = city.key === selectedCity;
        const pos: LatLngExpression = [city.lat, city.lng];

        return (
          <CircleMarker
            key={city.key}
            {...({ center: pos, radius: isSelected ? 22 : 16 } as any)}
            pathOptions={{
              fillColor: color,
              fillOpacity: 0.85,
              color: isSelected ? '#fff' : color,
              weight: isSelected ? 3 : 1,
            }}
            eventHandlers={{ click: () => onCitySelect(city.key) }}
          >
            <Popup>
              <div className='text-gray-900 font-sans p-1'>
                <p className='font-bold text-base'>{city.name}</p>
                <p className='text-2xl font-extrabold' style={{ color }}>
                  {aqi ? Math.round(aqi) : '—'}
                </p>
                <p className='text-xs text-gray-600'>
                  {data?.aqi_category ?? 'No data'}
                </p>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
