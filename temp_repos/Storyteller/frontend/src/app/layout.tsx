import '@mantine/core/styles.css'
import '@mantine/notifications/styles.css'

import React from 'react'
import { MantineProvider, ColorSchemeScript } from '@mantine/core'
import { Notifications } from '@mantine/notifications'

export const metadata = {
  title: 'StoryShort.ai Clone',
  description: 'Generate viral faceless videos with AI',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <ColorSchemeScript />
      </head>
      <body>
        <MantineProvider>
          <Notifications />
          {children}
        </MantineProvider>
      </body>
    </html>
  )
}