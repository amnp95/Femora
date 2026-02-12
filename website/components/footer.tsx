import { Github, FileText } from "lucide-react"

export function Footer() {
  return (
    <footer className="border-t border-border/50 py-12 px-4 mt-20">
      <div className="container mx-auto">
        <div className="grid md:grid-cols-4 gap-8 mb-8">
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-md flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-sm">F</span>
              </div>
              <span className="font-bold text-xl">FEMORA</span>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {"Fast Efficient Meshing for OpenSees-based Resilience Analysis"}
            </p>
          </div>

          <div className="space-y-4">
            <h4 className="font-semibold">Documentation</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a
                  href="https://amnp95.github.io/Femora/introduction/getting_started.html"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  Getting Started
                </a>
              </li>
              <li>
                <a
                  href="https://amnp95.github.io/Femora/introduction/installation.html"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  Installation
                </a>
              </li>
              <li>
                <a
                  href="https://amnp95.github.io/Femora/introduction/examples.html"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  Examples
                </a>
              </li>
              <li>
                <a
                  href="https://amnp95.github.io/Femora/technical/index.html"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  API Reference
                </a>
              </li>
            </ul>
          </div>

          <div className="space-y-4">
            <h4 className="font-semibold">Resources</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a
                  href="https://github.com/amnp95/Femora"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  GitHub Repository
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/amnp95/Femora/issues"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  Issue Tracker
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/amnp95/Femora/discussions"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  Discussions
                </a>
              </li>
              <li>
                <a
                  href="https://amnp95.github.io/Femora/developer/index.html"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  Contributing
                </a>
              </li>
            </ul>
          </div>

          <div className="space-y-4">
            <h4 className="font-semibold">Connect</h4>
            <div className="flex gap-3">
              <a
                href="https://github.com/amnp95/Femora"
                target="_blank"
                rel="noopener noreferrer"
                className="w-10 h-10 rounded-lg bg-secondary hover:bg-primary/20 flex items-center justify-center transition-colors"
              >
                <Github className="w-5 h-5" />
              </a>
              <a
                href="https://amnp95.github.io/Femora/"
                target="_blank"
                rel="noopener noreferrer"
                className="w-10 h-10 rounded-lg bg-secondary hover:bg-primary/20 flex items-center justify-center transition-colors"
              >
                <FileText className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>

        <div className="pt-8 border-t border-border/50 flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-muted-foreground">
          <p>© 2025 FEMORA. Developed by Amin Pakzad & Pedro Arduino</p>
          <div className="flex gap-6">
            <a
              href="https://github.com/amnp95/Femora/blob/main/LICENSE"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-foreground transition-colors"
            >
              License
            </a>
            <a
              href="https://github.com/amnp95/Femora"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-foreground transition-colors"
            >
              GitHub
            </a>
          </div>
        </div>
      </div>
    </footer>
  )
}
