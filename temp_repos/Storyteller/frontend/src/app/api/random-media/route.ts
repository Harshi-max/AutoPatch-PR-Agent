import { NextRequest, NextResponse } from 'next/server'

export async function GET() {
  try {
    // Forward request to backend
    const response = await fetch('http://localhost:8000/api/random-media', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}`)
    }
    
    const data = await response.json()
    return NextResponse.json(data)
    
  } catch (error) {
    console.error('Proxy error:', error)
    return NextResponse.json(
      { error: 'Failed to get random media' },
      { status: 500 }
    )
  }
}