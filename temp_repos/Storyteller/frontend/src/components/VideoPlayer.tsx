'use client'

import React from 'react'
import { Player } from '@remotion/player'
import { VideoComposition } from './VideoComposition'
import { Card, Group, Text, Button } from '@mantine/core'
import { IconDownload } from '@tabler/icons-react'
import { notifications } from '@mantine/notifications'
import axios from 'axios'

interface VideoPlayerProps {
  script: string
  audioData: string
  imageSrc: string
  videoSrc: string
  onDownload?: () => void
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  script,
  audioData,
  imageSrc,
  videoSrc,
  onDownload
}) => {
  const fps = 30
  const durationInFrames = Math.max(150, script.length * 2) // Rough estimate based on script length

  const handleExportVideo = async () => {
    try {
      notifications.show({
        title: 'Exporting Video',
        message: 'Preparing video export...',
        color: 'blue'
      })

      // Create a simplified video export as a text file with metadata
      // In a full implementation, this would capture the actual video
      const exportData = {
        title: 'StoryShort Video Export',
        script: script,
        timestamp: new Date().toISOString(),
        composition: {
          fps: fps,
          duration: `${Math.round(durationInFrames / fps)} seconds`,
          resolution: '1920x1080',
          imageSrc: imageSrc,
          videoSrc: videoSrc
        },
        note: 'This is a preview export. Full video rendering requires additional setup with FFmpeg and @remotion/renderer.'
      }

      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      
      const a = document.createElement('a')
      a.href = url
      a.download = `storyshort-video-${Date.now()}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      notifications.show({
        title: 'Export Complete',
        message: 'Video metadata exported successfully. Full video rendering coming soon!',
        color: 'green'
      })
      
      if (onDownload) {
        onDownload()
      }
    } catch (error) {
      notifications.show({
        title: 'Export Failed',
        message: 'Failed to export video. Please try again.',
        color: 'red'
      })
    }
  }

  return (
    <Card shadow="md" padding="xl" radius="md">
      <Group justify="space-between" mb="md">
        <Text size="lg" fw={600}>Generated Video Preview</Text>
        <Button
          leftSection={<IconDownload size={16} />}
          variant="filled"
          color="green"
          onClick={handleExportVideo}
        >
          Export Video
        </Button>
      </Group>

      <div style={{ aspectRatio: '16/9', width: '100%', maxWidth: '800px' }}>
        <Player
          component={VideoComposition}
          compositionWidth={1920}
          compositionHeight={1080}
          durationInFrames={durationInFrames}
          fps={fps}
          inputProps={{
            script,
            audioData,
            imageSrc,
            videoSrc,
            durationInFrames,
            fps
          }}
          controls
          style={{
            width: '100%',
            height: '100%'
          }}
        />
      </div>
    </Card>
  )
}