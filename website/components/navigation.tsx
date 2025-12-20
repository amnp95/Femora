import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Github } from "lucide-react"
import { ThemeToggle } from "@/components/theme-toggle"

export function Navigation() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded-md flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-sm">F</span>
            </div>
            <span className="font-bold text-xl">FEMORA</span>
          </div>

          <div className="hidden md:flex items-center gap-8">
            <Link href="#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Features
            </Link>
            <Link href="#modes" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Modes
            </Link>
            <Link href="#docs" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Documentation
            </Link>
            <Link href="#ai" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              AI Features
            </Link>
          </div>

          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Button variant="ghost" size="sm" asChild>
              <a href="https://github.com/GeotechUW/Femora.git" target="_blank" rel="noopener noreferrer">
                <Github className="w-4 h-4" />
              </a>
            </Button>
            <Button size="sm" asChild>
              <a
                href="https://amnp95.github.io/Femora/introduction/getting_started.html"
                target="_blank"
                rel="noopener noreferrer"
              >
                Get Started
              </a>
            </Button>
          </div>
        </div>
      </div>
    </nav>
  )
}
