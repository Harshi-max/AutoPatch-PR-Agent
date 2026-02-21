'use client'

import {
  Container,
  Title,
  Text,
  Stack,
  Group,
  Badge,
  Box,
  Card,
  SimpleGrid,
  ThemeIcon,
  Center
} from '@mantine/core'
import { IconVideo, IconSparkles, IconRocket, IconMicrophone, IconDownload, IconBolt } from '@tabler/icons-react'
import { VideoGenerator } from '../components/VideoGenerator'

export default function HomePage() {
  const features = [
    {
      icon: IconSparkles,
      title: "AI-Powered Scripts",
      description: "Generate engaging stories with DeepSeek AI"
    },
    {
      icon: IconMicrophone,
      title: "Text-to-Speech",
      description: "Natural voice narration in multiple languages"
    },
    {
      icon: IconVideo,
      title: "Video Composition",
      description: "Professional video creation with Remotion"
    },
    {
      icon: IconDownload,
      title: "Easy Export",
      description: "Download your videos instantly"
    }
  ]

  return (
      <Box style={{ backgroundColor: '#0d0d0d', color: '#fff' }}>
        {/* Hero Section */}
        <Box
            style={{
              background: 'linear-gradient(135deg, #1e1e2f 0%, #2e0f4a 100%)',
              minHeight: '60vh',
              position: 'relative'
            }}
        >
          <Container size="xl" py={80}>
            <Center style={{ minHeight: '40vh' }}>
              <Stack gap="xl" align="center" ta="center">
                <Badge
                    size="lg"
                    variant="filled"
                    color="yellow"
                    leftSection={<IconBolt size={16} />}
                >
                  AI-Powered Video Creation
                </Badge>

                <Title
                    order={1}
                    size={60}
                    fw={900}
                    style={{
                      lineHeight: 1.2,
                      textShadow: '2px 2px 8px rgba(0,0,0,0.5)'
                    }}
                >
                  Create Viral Faceless Videos
                  <Text
                      component="span"
                      inherit
                      c="yellow.4"
                      style={{ display: 'block' }}
                  >
                    in Minutes with AI
                  </Text>
                </Title>

                <Text
                    size="xl"
                    c="gray.4"
                    maw={600}
                    style={{ fontSize: '1.3rem', lineHeight: 1.6 }}
                >
                  Transform your ideas into engaging videos with AI-powered script generation,
                  professional narration, and stunning visuals. No recording required.
                </Text>

                <Group gap="md">
                  <Badge variant="filled" color="green" size="lg">
                    <IconRocket size={14} style={{ marginRight: 4 }} />
                    Ready to Use
                  </Badge>
                  <Badge variant="filled" color="blue" size="lg">
                    Free AI Models
                  </Badge>
                  <Badge variant="filled" color="purple" size="lg">
                    Professional Quality
                  </Badge>
                </Group>
              </Stack>
            </Center>
          </Container>
        </Box>

        {/* Features Section */}
        <Container size="xl" py={80}>
          <Stack gap="xl" align="center">
            <Box ta="center">
              <Title order={2} size={36} mb="md" c="white">
                Everything You Need to Create Amazing Videos
              </Title>
              <Text size="lg" c="gray.5" maw={600}>
                Our platform combines the latest AI technology with professional video tools
              </Text>
            </Box>

            <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} spacing="xl">
              {features.map((feature, index) => (
                  <Card
                      key={index}
                      shadow="xl"
                      padding="xl"
                      radius="lg"
                      style={{
                        backgroundColor: '#1a1a2e',
                        border: '1px solid #333',
                        transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                        cursor: 'pointer'
                      }}
                      onMouseEnter={e => {
                        const el = e.currentTarget;
                        el.style.transform = 'translateY(-5px)';
                        el.style.boxShadow = '0 15px 30px rgba(0,0,0,0.5)';
                      }}
                      onMouseLeave={e => {
                        const el = e.currentTarget;
                        el.style.transform = 'translateY(0)';
                        el.style.boxShadow = '0 5px 15px rgba(0,0,0,0.2)';
                      }}
                  >
                    <Stack align="center" ta="center" gap="md">
                      <ThemeIcon
                          size={60}
                          radius="xl"
                          variant="gradient"
                          gradient={{ from: 'blue', to: 'purple', deg: 45 }}
                      >
                        <feature.icon size={30} />
                      </ThemeIcon>
                      <Title order={4} size={18} c="white">
                        {feature.title}
                      </Title>
                      <Text size="sm" c="gray.4" style={{ lineHeight: 1.6 }}>
                        {feature.description}
                      </Text>
                    </Stack>
                  </Card>
              ))}
            </SimpleGrid>
          </Stack>
        </Container>

        {/* Video Generator Section */}
        <Box style={{ backgroundColor: '#111122' }}>
          <Container size="xl" py={80}>
            <Stack gap="xl" align="center">
              <Box ta="center">
                <Title order={2} size={36} mb="md" c="white">
                  Start Creating Your Video
                </Title>
                <Text size="lg" c="gray.5" maw={600}>
                  Enter your story idea and let our AI create an engaging video for you
                </Text>
              </Box>

              <VideoGenerator />
            </Stack>
          </Container>
        </Box>
      </Box>
  )
}
