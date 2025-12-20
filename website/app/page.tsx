import { Hero } from "@/components/hero"
import { Features } from "@/components/features"
import { ModesSection } from "@/components/modes-section"
import { Documentation } from "@/components/documentation"
import { AISection } from "@/components/ai-section"
import { Footer } from "@/components/footer"
import { Navigation } from "@/components/navigation"

export default function Home() {
  return (
    <main className="min-h-screen bg-background relative overflow-hidden">
      {/* Background mesh pattern */}
      <div className="fixed inset-0 -z-10 opacity-20">
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `
            linear-gradient(to right, rgba(99, 179, 237, 0.1) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(99, 179, 237, 0.1) 1px, transparent 1px)
          `,
            backgroundSize: "40px 40px",
          }}
        ></div>
      </div>

      {/* Animated gradient orbs */}
      <div className="fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute top-1/4 -left-48 w-96 h-96 bg-primary/20 rounded-full blur-[128px] animate-pulse"></div>
        <div
          className="absolute bottom-1/4 -right-48 w-96 h-96 bg-accent/20 rounded-full blur-[128px] animate-pulse"
          style={{ animationDelay: "1s" }}
        ></div>
      </div>

      <Navigation />
      <Hero />
      <Features />
      <ModesSection />
      <Documentation />
      <AISection />
      <Footer />
    </main>
  )
}
