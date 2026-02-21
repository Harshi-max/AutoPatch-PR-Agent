'use client'

import React, { useState } from 'react'
import {
  Stack,
  Card,
  TextInput,
  Select,
  Button,
  Group,
  Text,
  Loader,
  Alert,
  Box,
  ActionIcon
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconVideo, IconDownload, IconMicrophone, IconSparkles } from '@tabler/icons-react'
import axios from 'axios'
import { VideoPlayer } from './VideoPlayer'

interface GeneratedVideo {
  script: string
  audioData: string
  mediaPaths: {
    image: string
    video: string
  }
}

export function VideoGenerator() {
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedVideo, setGeneratedVideo] = useState<GeneratedVideo | null>(null)
  const [currentStep, setCurrentStep] = useState('')

  const form = useForm({
    initialValues: {
      prompt: '',
      length: 'short',
      voice: 'en'
    },
    validate: {
      prompt: (value) => (value.length < 10 ? 'Prompt must be at least 10 characters' : null)
    }
  })

  const handleGenerateVideo = async (values: typeof form.values) => {
    setIsGenerating(true)
    setCurrentStep('Generating script...')
    
    try {
      // Step 1: Generate script - using local API route
      const scriptResponse = await axios.post('/api/generate-script', {
        prompt: values.prompt,
        length: values.length
      })

      if (!scriptResponse.data.success) {
        throw new Error('Failed to generate script')
      }

      const script = scriptResponse.data.script
      setCurrentStep('Generating audio...')

      // Step 2: Generate audio - using local API route
      const audioResponse = await axios.post('/api/generate-audio', {
        script: script,
        voice: values.voice
      })

      if (!audioResponse.data.success) {
        throw new Error('Failed to generate audio')
      }

      setCurrentStep('Selecting media...')

      // Step 3: Get random media - using local API route
      const mediaResponse = await axios.get('/api/random-media')

      if (!mediaResponse.data.success) {
        throw new Error('Failed to get media')
      }

      // Store the generated content
      const videoData: GeneratedVideo = {
        script: script,
        audioData: audioResponse.data.audio_data,
        mediaPaths: {
          image: mediaResponse.data.image,
          video: mediaResponse.data.video
        }
      }

      setGeneratedVideo(videoData)
      setCurrentStep('Video ready!')

      notifications.show({
        title: 'Success!',
        message: 'Your video has been generated successfully',
        color: 'green'
      })

    } catch (error) {
      console.error('Generation error:', error)
      notifications.show({
        title: 'Error',
        message: 'Failed to generate video. Please try again.',
        color: 'red'
      })
    } finally {
      setIsGenerating(false)
      setCurrentStep('')
    }
  }

  const handleDownload = () => {
    if (!generatedVideo) return

    // Create a simple text file with the script for now
    // In a real implementation, this would be the actual video file
    const content = `StoryShort Video Script:\n\n${generatedVideo.script}\n\nGenerated at: ${new Date().toLocaleString()}`
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    
    const a = document.createElement('a')
    a.href = url
    a.download = `storyshort-script-${Date.now()}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    notifications.show({
      title: 'Downloaded',
      message: 'Script has been downloaded. Video export coming soon!',
      color: 'blue'
    })
  }

  return (
    <Stack gap="xl" w="100%" maw={900}>
      <Card 
        shadow="lg" 
        padding="xl" 
        radius="xl"
        style={{
          background: 'linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%)',
          border: '1px solid #e9ecef'
        }}
      >
        <form onSubmit={form.onSubmit(handleGenerateVideo)}>
          <Stack gap="md">
            <TextInput
              label="Video Prompt"
              placeholder="e.g., 'The mysterious disappearance of Amelia Earhart' or 'Ancient secrets of the pyramids'"
              required
              size="lg"
              {...form.getInputProps('prompt')}
              leftSection={<IconSparkles size={18} />}
              styles={{
                input: {
                  fontSize: '16px',
                  padding: '12px 16px'
                }
              }}
            />
            
            <Group grow>
              <Select
                label="Video Length"
                data={[
                  { value: 'short', label: 'Short (30-60s)' },
                  { value: 'medium', label: 'Medium (60-90s)' },
                  { value: 'long', label: 'Long (90-180s)' }
                ]}
                {...form.getInputProps('length')}
              />
              
              <Select
                label="Voice Language"
                data={[
                  { value: 'en', label: 'English' },
                  { value: 'es', label: 'Spanish' },
                  { value: 'fr', label: 'French' }
                ]}
                {...form.getInputProps('voice')}
                leftSection={<IconMicrophone size={16} />}
              />
            </Group>

            <Button
              type="submit"
              loading={isGenerating}
              leftSection={<IconVideo size={18} />}
              size="xl"
              fullWidth
              variant="gradient"
              gradient={{ from: 'blue', to: 'purple', deg: 45 }}
              style={{
                height: '60px',
                fontSize: '18px',
                fontWeight: 600
              }}
            >
              {isGenerating ? currentStep : '✨ Generate Amazing Video'}
            </Button>
          </Stack>
        </form>
      </Card>

      {isGenerating && (
        <Alert color="blue" variant="light">
          <Group>
            <Loader size="sm" />
            <Text>{currentStep}</Text>
          </Group>
        </Alert>
      )}

      {generatedVideo && (
        <Stack gap="md">
          <VideoPlayer
            script={generatedVideo.script}
            audioData={generatedVideo.audioData}
            imageSrc={generatedVideo.mediaPaths.image}
            videoSrc={generatedVideo.mediaPaths.video}
            onDownload={handleDownload}
          />
          
          <Card shadow="md" padding="xl" radius="md">
            <Stack gap="md">
              <Text size="lg" fw={600}>Script Details</Text>
              
              <Box>
                <Text size="sm" fw={500} mb="xs">Generated Script:</Text>
                <Text size="sm" c="dimmed" style={{ 
                  whiteSpace: 'pre-wrap', 
                  background: '#f8f9fa',
                  padding: '12px',
                  borderRadius: '8px'
                }}>
                  {generatedVideo.script}
                </Text>
              </Box>

              <Group>
                <Text size="sm" c="dimmed">
                  Selected Media: Image & Video from CC0 sources
                </Text>
              </Group>

              {generatedVideo.audioData && (
                <Box>
                  <Text size="sm" fw={500} mb="xs">Generated Audio:</Text>
                  <audio 
                    controls 
                    src={`data:audio/mp3;base64,${generatedVideo.audioData}`}
                    style={{ width: '100%' }}
                  />
                </Box>
              )}
            </Stack>
          </Card>
        </Stack>
      )}
    </Stack>
  )
}