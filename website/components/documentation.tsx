import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { BookOpen, Code, GraduationCap, FileText, ArrowRight } from "lucide-react"

const docSections = [
  {
    icon: BookOpen,
    title: "Getting Started",
    description: "Installation, setup, and your first FEMORA model",
    link: "/docs/getting_started/",
  },
  {
    icon: Code,
    title: "API Reference",
    description: "Complete documentation of classes, methods, and functions",
    link: "/docs/reference/",
  },
  {
    icon: GraduationCap,
    title: "Examples & Tutorials",
    description: "Practical examples from simple to advanced applications",
    link: "/docs/advanced/",
  },
  {
    icon: FileText,
    title: "Developer Guide",
    description: "Contributing, code style, and development setup",
    link: "/docs/reference/",
  },
]

export function Documentation() {
  return (
    <section id="docs" className="py-20 px-4 relative">
      <div className="container mx-auto">
        <div className="text-center mb-16 space-y-4">
          <h2 className="text-4xl md:text-5xl font-bold text-balance">
            {"Comprehensive"}
            <span className="block text-primary">Documentation</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto text-pretty">
            {"Everything you need to master FEMORA, from quick starts to advanced techniques"}
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto mb-12">
          {docSections.map((section, index) => (
            <Card key={index} className="glass-strong p-6 hover:bg-card/50 transition-all group cursor-pointer" asChild>
              <a href={section.link}>
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors flex-shrink-0">
                    <section.icon className="w-6 h-6 text-primary" />
                  </div>
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold">{section.title}</h3>
                      <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
                    </div>
                    <p className="text-sm text-muted-foreground leading-relaxed">{section.description}</p>
                  </div>
                </div>
              </a>
            </Card>
          ))}
        </div>

        <div className="glass-strong rounded-2xl p-8 md:p-12 max-w-4xl mx-auto">
          <div className="flex flex-col md:flex-row items-center gap-8">
            <div className="flex-1 space-y-4">
              <h3 className="text-2xl font-bold">Ready to Get Started?</h3>
              <p className="text-muted-foreground leading-relaxed">
                {"Install FEMORA with pip and start building your first finite element model in minutes."}
              </p>
              <pre className="glass p-4 rounded-lg text-sm font-mono">
                <code className="text-accent">pip install femora</code>
              </pre>
            </div>
            <div className="flex flex-col gap-3">
              <Button size="lg" asChild>
                <a
                  href="/docs/getting_started/"
                >
                  Quick Start Guide
                </a>
              </Button>
              <Button size="lg" variant="outline" asChild>
                <a href="https://github.com/amnp95/Femora" target="_blank" rel="noopener noreferrer">
                  View on GitHub
                </a>
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
