import { Button } from "@/components/ui/button"
import { ArrowRight, Sparkles } from "lucide-react"
import { MeshVisualization } from "@/components/mesh-visualization"

export function Hero() {
  return (
    <section className="relative pt-32 pb-20 px-4 overflow-hidden">
      <div className="container mx-auto">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-8">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full glass text-sm text-muted-foreground">
              <Sparkles className="w-4 h-4 text-primary" />
              <span>Fast Efficient Meshing for OpenSees-based Resilience Analysis</span>
            </div>

            <div className="space-y-4">
              <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold leading-tight text-balance">
                Revolutionize
                <span className="block text-primary">Seismic Analysis</span>
              </h1>
              <p className="text-xl text-muted-foreground leading-relaxed text-pretty">
                {
                  "A powerful Python framework for finite element meshing and seismic analysis. Built on OpenSees, designed for researchers and engineers."
                }
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
              <Button size="lg" className="group" asChild>
                <a
                  href="https://amnp95.github.io/Femora/introduction/quick_start.html"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Quick Start
                  <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                </a>
              </Button>
              <Button size="lg" variant="outline" asChild>
                <a href="https://amnp95.github.io/Femora/" target="_blank" rel="noopener noreferrer">
                  View Documentation
                </a>
              </Button>
            </div>

            <div className="flex items-center gap-8 pt-4">
              <div>
                <div className="text-2xl font-bold text-primary">50+</div>
                <div className="text-sm text-muted-foreground">Material Models</div>
              </div>
              <div className="w-px h-12 bg-border"></div>
              <div>
                <div className="text-2xl font-bold text-accent">3D &amp; 2D    </div>
                <div className="text-sm text-muted-foreground">Mesh Generation</div>
              </div>
              <div className="w-px h-12 bg-border"></div>
              <div>
                <div className="text-2xl font-bold text-chart-3">DRM</div>
                <div className="text-sm text-muted-foreground">Wave Propagation</div>
              </div>
            </div>
          </div>

          <div className="relative">
            <MeshVisualization />
          </div>
        </div>
      </div>
    </section>
  )
}
