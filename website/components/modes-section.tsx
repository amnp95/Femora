import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Terminal, Layout, ArrowRight } from "lucide-react"

export function ModesSection() {
  return (
    <section id="modes" className="py-20 px-4 relative">
      <div className="container mx-auto">
        <div className="text-center mb-16 space-y-4">
          <h2 className="text-4xl md:text-5xl font-bold text-balance">
            {"Two Powerful"}
            <span className="block text-primary">Working Modes</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto text-pretty">
            {"Choose the workflow that fits your needs - code-first or visual-first"}
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {/* Headless Mode */}
          <Card className="glass-strong p-8 space-y-6 hover:bg-card/50 transition-all group">
            <div className="space-y-4">
              <div className="w-16 h-16 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                <Terminal className="w-8 h-8 text-primary" />
              </div>
              <div className="space-y-2">
                <h3 className="text-2xl font-bold">Headless Mode</h3>
                <p className="text-muted-foreground leading-relaxed">
                  {
                    "Pure Python API for programmatic model creation. Perfect for automation, batch processing, and integration into larger workflows."
                  }
                </p>
              </div>
            </div>

            <div className="space-y-3 pt-4">
              <div className="flex items-start gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2"></div>
                <p className="text-sm text-muted-foreground">{"Scriptable and reproducible workflows"}</p>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2"></div>
                <p className="text-sm text-muted-foreground">{"Integration with CI/CD pipelines"}</p>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2"></div>
                <p className="text-sm text-muted-foreground">{"Parametric studies and optimization"}</p>
              </div>
            </div>

            <div className="pt-4">
              <pre className="glass p-4 rounded-lg text-xs font-mono overflow-x-auto">
                <code className="text-accent">{`from femora import Model

model = Model()
model.add_mesh(type='soil', layers=3)
model.export_to_opensees('model.tcl')`}</code>
              </pre>
            </div>

            <Button variant="outline" className="w-full group/btn bg-transparent" asChild>
              <a
                href="https://amnp95.github.io/Femora/introduction/quick_start.html"
                target="_blank"
                rel="noopener noreferrer"
              >
                Learn More
                <ArrowRight className="w-4 h-4 ml-2 group-hover/btn:translate-x-1 transition-transform" />
              </a>
            </Button>
          </Card>

          {/* GUI Mode */}
          <Card className="glass-strong p-8 space-y-6 hover:bg-card/50 transition-all group">
            <div className="space-y-4">
              <div className="w-16 h-16 rounded-xl bg-accent/10 flex items-center justify-center group-hover:bg-accent/20 transition-colors">
                <Layout className="w-8 h-8 text-accent" />
              </div>
              <div className="space-y-2">
                <h3 className="text-2xl font-bold">GUI Mode</h3>
                <p className="text-muted-foreground leading-relaxed">
                  {
                    "Visual interface for interactive model construction. Ideal for rapid prototyping, teaching, and exploratory analysis."
                  }
                </p>
              </div>
            </div>

            <div className="space-y-3 pt-4">
              <div className="flex items-start gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-accent mt-2"></div>
                <p className="text-sm text-muted-foreground">{"Interactive 3D visualization"}</p>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-accent mt-2"></div>
                <p className="text-sm text-muted-foreground">{"Real-time model preview"}</p>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-accent mt-2"></div>
                <p className="text-sm text-muted-foreground">{"Beginner-friendly interface"}</p>
              </div>
            </div>

            <div className="pt-4 glass p-4 rounded-lg">
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <div className="w-2 h-2 rounded-full bg-green-500"></div>
                  <span>{"Visual model builder"}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <div className="w-2 h-2 rounded-full bg-accent"></div>
                  <span>{"Material property editor"}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <div className="w-2 h-2 rounded-full bg-primary"></div>
                  <span>{"Analysis configuration"}</span>
                </div>
              </div>
            </div>

            <Button variant="outline" className="w-full group/btn bg-transparent" asChild>
              <a
                href="https://amnp95.github.io/Femora/introduction/installation.html"
                target="_blank"
                rel="noopener noreferrer"
              >
                Learn More
                <ArrowRight className="w-4 h-4 ml-2 group-hover/btn:translate-x-1 transition-transform" />
              </a>
            </Button>
          </Card>
        </div>
      </div>
    </section>
  )
}
