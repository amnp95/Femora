import { Box, Network, Layers, Radio, Eye, FileCode } from "lucide-react"
import { Card } from "@/components/ui/card"

const features = [
  {
    icon: Box,
    title: "Powerful Mesh Generation",
    description: "Create complex 3D soil and structural models with minimal code and intuitive API",
  },
  {
    icon: Network,
    title: "Domain Decomposition",
    description: "HPC-ready parallel computing with advanced domain decomposition for large-scale simulations",
  },
  {
    icon: Layers,
    title: "Comprehensive Interface",
    description: "Support all materials, analysis types, elements, and everything available in OpenSees",
  },
  {
    icon: Radio,
    title: "Domain Reduction & PML",
    description: "Advanced DRM technique and Perfectly Matched Layer elements for realistic seismic wave propagation",
  },
  {
    icon: Eye,
    title: "Built-in Visualization",
    description: "Powerful visualization tools for model inspection and result analysis",
  },
  {
    icon: FileCode,
    title: "OpenSees Integration",
    description: "Seamless export to OpenSees TCL files for immediate simulation",
  },
]

export function Features() {
  return (
    <section id="features" className="py-20 px-4">
      <div className="container mx-auto">
        <div className="text-center mb-16 space-y-4">
          <h2 className="text-4xl md:text-5xl font-bold text-balance">
            {"Everything You Need for"}
            <span className="block text-primary">Finite Element Analysis</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto text-pretty">
            {"Built with modern Python, optimized for researchers and engineers working with OpenSees"}
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <Card key={index} className="glass-strong p-6 hover:bg-card/50 transition-colors group">
              <div className="space-y-4">
                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                  <feature.icon className="w-6 h-6 text-primary" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold">{feature.title}</h3>
                  <p className="text-muted-foreground leading-relaxed">{feature.description}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}
