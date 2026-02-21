"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import Link from "next/link"
import { HeroScene3D } from "./hero-3d"

export function LandingHero() {
  return (
    <header className="border-b bg-background">
      <div className="container mx-auto px-4 py-12 md:py-16">
        <div className="flex flex-col-reverse items-start gap-10 md:flex-row md:items-center md:justify-between">
          <div className="flex-1">
            <div className="mb-4 flex items-center gap-2">
              <Badge variant="secondary">New</Badge>
              <span className="text-sm text-muted-foreground">Multilingual voice → code + visualization</span>
            </div>

            <h1 className="text-pretty text-4xl font-semibold leading-tight md:text-6xl">
              Voice-to-Code Algorithm Visualizer
            </h1>
            <p className="mt-3 max-w-prose text-pretty text-muted-foreground md:text-lg">
              Speak in English, Hindi, or Telugu. Instantly generate JavaScript or Python and watch arrays, loops, and
              variables animate step-by-step in 2D and 3D. Learn by seeing your logic come to life.
            </p>

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <a href="#playground">
                <Button size="lg">Start Building</Button>
              </a>
              <Link
                href="#how-it-works"
                className="text-sm font-medium text-primary underline-offset-4 hover:underline"
              >
                How it works
              </Link>
            </div>

            <ul className="mt-6 grid grid-cols-2 gap-4 text-sm text-muted-foreground md:grid-cols-4">
              <li className="rounded-lg border p-3 transition-transform hover:-translate-y-0.5">
                Multilingual Input
                <div className="mt-1 text-foreground">EN / HI / TE</div>
              </li>
              <li className="rounded-lg border p-3 transition-transform hover:-translate-y-0.5">
                Real-Time Code
                <div className="mt-1 text-foreground">JS & Python</div>
              </li>
              <li className="rounded-lg border p-3 transition-transform hover:-translate-y-0.5">
                Step-by-Step Viz
                <div className="mt-1 text-foreground">2D / 3D Views</div>
              </li>
              <li className="rounded-lg border p-3 transition-transform hover:-translate-y-0.5">
                Beginner-Friendly
                <div className="mt-1 text-foreground">Play / Pause / Step</div>
              </li>
            </ul>
          </div>

          <div className="flex-1">
            <div className="relative mx-auto max-w-[640px] overflow-hidden rounded-xl">
              <HeroScene3D />
              <div className="pointer-events-none absolute inset-0 rounded-xl ring-1 ring-black/5" />
            </div>
          </div>
        </div>

        <div id="how-it-works" className="mt-12 grid gap-4 md:grid-cols-3">
          <div className="rounded-xl border p-5">
            <h3 className="font-medium">1. Speak Your Idea</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Use the mic to describe your algorithm in your language.
            </p>
          </div>
          <div className="rounded-xl border p-5">
            <h3 className="font-medium">2. Generate Code</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Get Python or JavaScript with clear structure and comments.
            </p>
          </div>
          <div className="rounded-xl border p-5">
            <h3 className="font-medium">3. Visualize Steps</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Watch variables and arrays update step-by-step with controls.
            </p>
          </div>
        </div>
      </div>
    </header>
  )
}
