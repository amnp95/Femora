"use client"

import { useEffect, useRef } from "react"

export function MeshVisualization() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    // Set canvas size
    canvas.width = 600
    canvas.height = 600

    const nodes: Array<{ x: number; y: number; z: number; vx: number; vy: number }> = []
    const gridSize = 8
    const spacing = 60

    // Create 3D grid of nodes
    for (let i = 0; i < gridSize; i++) {
      for (let j = 0; j < gridSize; j++) {
        for (let k = 0; k < 3; k++) {
          nodes.push({
            x: i * spacing + 80,
            y: j * spacing + 80,
            z: k * spacing,
            vx: (Math.random() - 0.5) * 0.3,
            vy: (Math.random() - 0.5) * 0.3,
          })
        }
      }
    }

    let rotation = 0

    function animate() {
      if (!ctx || !canvas) return

      ctx.fillStyle = "rgba(14, 16, 26, 0.1)"
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      rotation += 0.003

      // Sort nodes by z-depth for proper rendering
      const sortedNodes = [...nodes].sort((a, b) => {
        const az = a.z * Math.cos(rotation) - a.x * Math.sin(rotation)
        const bz = b.z * Math.cos(rotation) - b.x * Math.sin(rotation)
        return az - bz
      })

      // Draw connections
      ctx.strokeStyle = "rgba(99, 179, 237, 0.15)"
      ctx.lineWidth = 1

      for (let i = 0; i < sortedNodes.length; i++) {
        const node = sortedNodes[i]
        const rotatedX = node.x * Math.cos(rotation) + node.z * Math.sin(rotation)
        const rotatedZ = node.z * Math.cos(rotation) - node.x * Math.sin(rotation)

        for (let j = i + 1; j < sortedNodes.length; j++) {
          const other = sortedNodes[j]
          const otherRotatedX = other.x * Math.cos(rotation) + other.z * Math.sin(rotation)
          const otherRotatedZ = other.z * Math.cos(rotation) - other.x * Math.sin(rotation)

          const dx = rotatedX - otherRotatedX
          const dy = node.y - other.y
          const dz = rotatedZ - otherRotatedZ
          const distance = Math.sqrt(dx * dx + dy * dy + dz * dz)

          if (distance < spacing * 1.5) {
            ctx.beginPath()
            ctx.moveTo(rotatedX + 300, node.y)
            ctx.lineTo(otherRotatedX + 300, other.y)
            ctx.stroke()
          }
        }
      }

      // Draw nodes
      sortedNodes.forEach((node) => {
        const rotatedX = node.x * Math.cos(rotation) + node.z * Math.sin(rotation)
        const rotatedZ = node.z * Math.cos(rotation) - node.x * Math.sin(rotation)
        const scale = 1 + rotatedZ / 500

        // Update node position slightly
        node.x += node.vx
        node.y += node.vy

        // Bounce off edges
        if (node.x < 50 || node.x > 550) node.vx *= -1
        if (node.y < 50 || node.y > 550) node.vy *= -1

        const gradient = ctx.createRadialGradient(rotatedX + 300, node.y, 0, rotatedX + 300, node.y, 4 * scale)
        gradient.addColorStop(0, "rgba(99, 179, 237, 0.8)")
        gradient.addColorStop(1, "rgba(99, 179, 237, 0)")

        ctx.fillStyle = gradient
        ctx.beginPath()
        ctx.arc(rotatedX + 300, node.y, 4 * scale, 0, Math.PI * 2)
        ctx.fill()

        // Node core
        ctx.fillStyle = "rgba(99, 179, 237, 1)"
        ctx.beginPath()
        ctx.arc(rotatedX + 300, node.y, 1.5 * scale, 0, Math.PI * 2)
        ctx.fill()
      })

      requestAnimationFrame(animate)
    }

    animate()
  }, [])

  return (
    <div className="relative">
      <div className="glass-strong rounded-2xl p-8 shadow-2xl">
        <canvas ref={canvasRef} className="w-full h-auto rounded-lg" style={{ maxWidth: "100%", height: "auto" }} />
      </div>
      <div className="absolute -bottom-4 -right-4 w-24 h-24 bg-primary/20 rounded-full blur-3xl"></div>
      <div className="absolute -top-4 -left-4 w-24 h-24 bg-accent/20 rounded-full blur-3xl"></div>
    </div>
  )
}
