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

    const floors = 5
    const baysX = 3
    const floorHeight = 70
    const bayWidth = 80
    const buildingBaseY = 450
    const buildingBaseX = 150

    // Create building nodes (columns and beam connections)
    const buildingNodes: Array<{
      x: number
      y: number
      baseX: number
      baseY: number
      isColumn: boolean
      floor: number
    }> = []

    for (let floor = 0; floor <= floors; floor++) {
      for (let bay = 0; bay <= baysX; bay++) {
        buildingNodes.push({
          x: buildingBaseX + bay * bayWidth,
          y: buildingBaseY - floor * floorHeight,
          baseX: buildingBaseX + bay * bayWidth,
          baseY: buildingBaseY - floor * floorHeight,
          isColumn: true,
          floor,
        })
      }
    }

    // Soil layers
    const soilLayers = 4
    const soilNodes: Array<{ x: number; y: number; baseX: number; baseY: number; layer: number }> = []

    for (let layer = 0; layer < soilLayers; layer++) {
      for (let i = 0; i <= 8; i++) {
        soilNodes.push({
          x: 50 + i * 60,
          y: buildingBaseY + 20 + layer * 30,
          baseX: 50 + i * 60,
          baseY: buildingBaseY + 20 + layer * 30,
          layer,
        })
      }
    }

    let time = 0

    function animate() {
      if (!ctx || !canvas) return

      // Clear canvas
      ctx.fillStyle = "rgba(14, 16, 26, 0.95)"
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      time += 0.015

      // Animate building (slight sway for seismic motion)
      const seismicWave = Math.sin(time * 1.5) * 8
      buildingNodes.forEach((node) => {
        const floorMultiplier = node.floor / floors
        node.x = node.baseX + seismicWave * floorMultiplier
      })

      // Animate soil (wave propagation)
      soilNodes.forEach((node, i) => {
        const wave = Math.sin(time * 2 + node.baseX * 0.02 - node.layer * 0.5) * 3
        node.y = node.baseY + wave
      })

      // Draw soil layers
      for (let layer = 0; layer < soilLayers; layer++) {
        const layerNodes = soilNodes.filter((n) => n.layer === layer)

        // Draw soil mesh
        for (let i = 0; i < layerNodes.length - 1; i++) {
          const node = layerNodes[i]
          const nextNode = layerNodes[i + 1]

          ctx.strokeStyle = `rgba(120, 80, 40, ${0.6 - layer * 0.1})`
          ctx.lineWidth = 2
          ctx.beginPath()
          ctx.moveTo(node.x, node.y)
          ctx.lineTo(nextNode.x, nextNode.y)
          ctx.stroke()

          // Vertical connections
          if (layer < soilLayers - 1) {
            const belowNode = soilNodes.find((n) => n.layer === layer + 1 && n.baseX === node.baseX)
            if (belowNode) {
              ctx.beginPath()
              ctx.moveTo(node.x, node.y)
              ctx.lineTo(belowNode.x, belowNode.y)
              ctx.stroke()
            }
          }
        }

        // Draw soil nodes
        layerNodes.forEach((node) => {
          ctx.fillStyle = `rgba(160, 100, 50, ${0.8 - layer * 0.15})`
          ctx.beginPath()
          ctx.arc(node.x, node.y, 3, 0, Math.PI * 2)
          ctx.fill()
        })
      }

      // Draw building structure
      // Draw beams (horizontal elements)
      for (let floor = 0; floor <= floors; floor++) {
        for (let bay = 0; bay < baysX; bay++) {
          const node1 = buildingNodes.find((n) => n.floor === floor && n.baseX === buildingBaseX + bay * bayWidth)
          const node2 = buildingNodes.find((n) => n.floor === floor && n.baseX === buildingBaseX + (bay + 1) * bayWidth)

          if (node1 && node2) {
            // Stress visualization (thicker = more stress)
            const stress = Math.abs(Math.sin(time * 2 + floor * 0.5)) * 0.5 + 0.5
            ctx.strokeStyle = `rgba(251, 146, 60, ${0.7 + stress * 0.3})`
            ctx.lineWidth = 2 + stress * 2
            ctx.beginPath()
            ctx.moveTo(node1.x, node1.y)
            ctx.lineTo(node2.x, node2.y)
            ctx.stroke()
          }
        }
      }

      // Draw columns (vertical elements)
      for (let bay = 0; bay <= baysX; bay++) {
        for (let floor = 0; floor < floors; floor++) {
          const node1 = buildingNodes.find((n) => n.floor === floor && n.baseX === buildingBaseX + bay * bayWidth)
          const node2 = buildingNodes.find((n) => n.floor === floor + 1 && n.baseX === buildingBaseX + bay * bayWidth)

          if (node1 && node2) {
            const stress = Math.abs(Math.sin(time * 2 + bay * 0.3)) * 0.5 + 0.5
            ctx.strokeStyle = `rgba(251, 146, 60, ${0.8 + stress * 0.2})`
            ctx.lineWidth = 3 + stress * 1
            ctx.beginPath()
            ctx.moveTo(node1.x, node1.y)
            ctx.lineTo(node2.x, node2.y)
            ctx.stroke()
          }
        }
      }

      // Draw building nodes (beam-column joints)
      buildingNodes.forEach((node) => {
        const pulse = 1 + Math.sin(time * 3 + node.floor * 0.5) * 0.3
        ctx.fillStyle = "rgba(251, 146, 60, 1)"
        ctx.beginPath()
        ctx.arc(node.x, node.y, 4 * pulse, 0, Math.PI * 2)
        ctx.fill()

        // Node glow
        const gradient = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, 10)
        gradient.addColorStop(0, "rgba(251, 146, 60, 0.5)")
        gradient.addColorStop(1, "rgba(251, 146, 60, 0)")
        ctx.fillStyle = gradient
        ctx.beginPath()
        ctx.arc(node.x, node.y, 10, 0, Math.PI * 2)
        ctx.fill()
      })

      // Draw ground line
      ctx.strokeStyle = "rgba(251, 146, 60, 0.3)"
      ctx.lineWidth = 2
      ctx.setLineDash([5, 5])
      ctx.beginPath()
      ctx.moveTo(0, buildingBaseY)
      ctx.lineTo(canvas.width, buildingBaseY)
      ctx.stroke()
      ctx.setLineDash([])

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
