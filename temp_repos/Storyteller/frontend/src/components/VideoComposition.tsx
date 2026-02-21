'use client'

import React from 'react'
import { AbsoluteFill, Sequence, Audio, Img, Video } from 'remotion'

interface VideoCompositionProps {
  script: string
  audioData: string
  imageSrc: string
  videoSrc: string
  durationInFrames: number
  fps: number
}

export const VideoComposition: React.FC<VideoCompositionProps> = ({
  script,
  audioData,
  imageSrc,
  videoSrc,
  durationInFrames,
  fps
}) => {
  const halfDuration = Math.floor(durationInFrames / 2)

  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>
      {/* Audio track */}
      <Audio 
        src={`data:audio/mp3;base64,${audioData}`}
        volume={0.8}
      />
      
      {/* First half: Image with script overlay */}
      <Sequence from={0} durationInFrames={halfDuration}>
        <AbsoluteFill>
          <Img
            src={imageSrc}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover'
            }}
          />
          {/* Text overlay */}
          <AbsoluteFill
            style={{
              justifyContent: 'center',
              alignItems: 'center',
              background: 'linear-gradient(transparent 0%, rgba(0,0,0,0.7) 70%, rgba(0,0,0,0.9) 100%)',
              padding: '40px'
            }}
          >
            <div
              style={{
                color: 'white',
                fontSize: '36px',
                fontWeight: 'bold',
                textAlign: 'center',
                fontFamily: 'Arial, sans-serif',
                textShadow: '2px 2px 4px rgba(0,0,0,0.8)',
                lineHeight: '1.2',
                maxWidth: '80%'
              }}
            >
              {script.substring(0, 120) + '...'}
            </div>
          </AbsoluteFill>
        </AbsoluteFill>
      </Sequence>

      {/* Second half: Video background */}
      <Sequence from={halfDuration} durationInFrames={halfDuration}>
        <AbsoluteFill>
          <Video
            src={videoSrc}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover'
            }}
            volume={0}
            loop
          />
          {/* Text overlay for second part */}
          <AbsoluteFill
            style={{
              justifyContent: 'center',
              alignItems: 'center',
              background: 'linear-gradient(transparent 0%, rgba(0,0,0,0.6) 70%, rgba(0,0,0,0.8) 100%)',
              padding: '40px'
            }}
          >
            <div
              style={{
                color: 'white',
                fontSize: '32px',
                fontWeight: 'bold',
                textAlign: 'center',
                fontFamily: 'Arial, sans-serif',
                textShadow: '2px 2px 4px rgba(0,0,0,0.8)',
                lineHeight: '1.2',
                maxWidth: '80%'
              }}
            >
              {script.substring(120)}
            </div>
          </AbsoluteFill>
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  )
}