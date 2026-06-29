import { useCallback, useRef, useState } from 'react'
import { useNodesState, useEdgesState, addEdge, type Node, type Edge, type Connection } from '@xyflow/react'

interface HistoryEntry {
  nodes: Node[]
  edges: Edge[]
}

const MAX_HISTORY = 50

export function useWorkflowEditor(initialNodes: Node[] = [], initialEdges: Edge[] = []) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)

  const historyRef = useRef<HistoryEntry[]>([{ nodes: initialNodes, edges: initialEdges }])
  const historyIndexRef = useRef(0)

  const pushHistory = useCallback(() => {
    const newEntry = { nodes: structuredClone(nodes), edges: structuredClone(edges) }
    const history = historyRef.current.slice(0, historyIndexRef.current + 1)
    history.push(newEntry)
    if (history.length > MAX_HISTORY) history.shift()
    historyRef.current = history
    historyIndexRef.current = history.length - 1
  }, [nodes, edges])

  const undo = useCallback(() => {
    if (historyIndexRef.current <= 0) return
    historyIndexRef.current -= 1
    const entry = historyRef.current[historyIndexRef.current]
    setNodes(entry.nodes)
    setEdges(entry.edges)
  }, [setNodes, setEdges])

  const redo = useCallback(() => {
    if (historyIndexRef.current >= historyRef.current.length - 1) return
    historyIndexRef.current += 1
    const entry = historyRef.current[historyIndexRef.current]
    setNodes(entry.nodes)
    setEdges(entry.edges)
  }, [setNodes, setEdges])

  const onConnect = useCallback(
    (connection: Connection) => {
      const { source, target } = connection

      // Reject self-loops
      if (source === target) return

      // Find source and target node types
      const sourceNode = nodes.find((n) => n.id === source)
      const targetNode = nodes.find((n) => n.id === target)
      const sourceType = (sourceNode?.data?.nodeType as string) ?? sourceNode?.type
      const targetType = (targetNode?.data?.nodeType as string) ?? targetNode?.type

      // End nodes should not have outgoing edges
      if (sourceType === 'end') return

      // Start nodes should not have incoming edges
      if (targetType === 'start') return

      setEdges((eds) => addEdge({ ...connection, id: `e-${Date.now()}` }, eds))
      pushHistory()
    },
    [nodes, setEdges, pushHistory]
  )

  const addNode = useCallback(
    (type: string, position: { x: number; y: number }, data: Record<string, unknown> = {}) => {
      const id = `node-${Date.now()}`
      const newNode: Node = { id, type, position, data: { label: data.label ?? type, ...data } }
      setNodes((nds) => [...nds, newNode])
      pushHistory()
      return id
    },
    [setNodes, pushHistory]
  )

  const removeSelected = useCallback(() => {
    setNodes((nds) => nds.filter((n) => !n.selected))
    setEdges((eds) => eds.filter((e) => !e.selected))
    setSelectedNode(null)
    pushHistory()
  }, [setNodes, setEdges, pushHistory])

  const updateNodeData = useCallback(
    (nodeId: string, data: Record<string, unknown>) => {
      setNodes((nds) =>
        nds.map((n) => (n.id === nodeId ? { ...n, data: { ...n.data, ...data } } : n))
      )
      pushHistory()
    },
    [setNodes, pushHistory]
  )

  const getDefinition = useCallback(() => {
    return {
      nodes: nodes.map((n) => ({ id: n.id, type: n.type, position: n.position, data: n.data })),
      edges: edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        source_handle: e.sourceHandle,
        target_handle: e.targetHandle,
        label: typeof e.label === 'string' ? e.label : undefined,
      })),
    }
  }, [nodes, edges])

  const loadDefinition = useCallback(
    (def: { nodes: Node[]; edges: Edge[] }) => {
      setNodes(def.nodes)
      setEdges(def.edges)
      historyRef.current = [{ nodes: def.nodes, edges: def.edges }]
      historyIndexRef.current = 0
    },
    [setNodes, setEdges]
  )

  return {
    nodes, edges, selectedNode,
    onNodesChange, onEdgesChange, onConnect,
    setSelectedNode, addNode, removeSelected, updateNodeData,
    undo, redo,
    canUndo: historyIndexRef.current > 0,
    canRedo: historyIndexRef.current < historyRef.current.length - 1,
    getDefinition, loadDefinition,
  }
}
