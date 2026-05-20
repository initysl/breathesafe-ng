import { NextResponse } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET() {
  try {
    const res = await fetch(`${API_URL}/aqi`, { next: { revalidate: 300 } });
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { error: 'Failed to fetch AQI data' },
      { status: 503 },
    );
  }
}
