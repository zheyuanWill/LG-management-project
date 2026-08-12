import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, Save, Truck, Package, CheckCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useApiGet, useApiPost, useApiDelete } from '@/hooks/useApi'
import { apiFetch } from '@/lib/api'
import { cn } from '@/lib/utils'
import { formatDate } from '@/lib/utils'

interface LogisticsNodeItem {
  id: number
  node_type: string
  node_date: string
  remark?: string
  tracking_no?: string
  attachment_key?: string
  created_at: string
}

interface LogisticsTimelineProps {
  projectId: string
}

// Keys MUST match the backend LogisticsNodeType enum.
const nodeTypeConfig: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  ordered: { label: '已下单', icon: <Package className="h-4 w-4" />, color: 'bg-blue-500' },
  supplier_shipped: { label: '供应商发货', icon: <Truck className="h-4 w-4" />, color: 'bg-purple-500' },
  in_transit: { label: '运输中', icon: <Truck className="h-4 w-4" />, color: 'bg-amber-500' },
  arrived: { label: '到港', icon: <Package className="h-4 w-4" />, color: 'bg-cyan-500' },
  warehoused: { label: '入库', icon: <Package className="h-4 w-4" />, color: 'bg-teal-500' },
  sent_to_owner: { label: '发给船东', icon: <Truck className="h-4 w-4" />, color: 'bg-indigo-500' },
  hk_signed: { label: '香港签收', icon: <CheckCircle className="h-4 w-4" />, color: 'bg-green-500' },
  settled: { label: '结算完成', icon: <CheckCircle className="h-4 w-4" />, color: 'bg-emerald-500' },
}

const nodeTypes = Object.keys(nodeTypeConfig)

export default function LogisticsTimeline({ projectId }: LogisticsTimelineProps) {
  const queryClient = useQueryClient()
  const { data: nodes, isLoading } = useApiGet<LogisticsNodeItem[]>(
    `/projects/${projectId}/logistics`
  )
  const postNode = useApiPost<LogisticsNodeItem>(`/projects/${projectId}/logistics`)
  const deleteNode = useApiDelete<void>(`/projects/${projectId}/logistics`)

  const [showAddForm, setShowAddForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [newNode, setNewNode] = useState({
    node_type: 'ordered',
    node_date: new Date().toISOString().split('T')[0],
    remark: '',
    tracking_no: '',
  })
  const [editNode, setEditNode] = useState<LogisticsNodeItem | null>(null)

  const sortedNodes = [...(nodes || [])].sort(
    (a, b) => new Date(a.node_date).getTime() - new Date(b.node_date).getTime()
  )

  const refresh = () =>
    queryClient.invalidateQueries({
      queryKey: [`/projects/${projectId}/logistics`],
    })

  const handleAdd = async () => {
    await postNode.mutateAsync({
      node_type: newNode.node_type,
      node_date: newNode.node_date,
      remark: newNode.remark,
      tracking_no: newNode.node_type === 'in_transit' ? newNode.tracking_no : undefined,
    })
    setShowAddForm(false)
    setNewNode({
      node_type: 'ordered',
      node_date: new Date().toISOString().split('T')[0],
      remark: '',
      tracking_no: '',
    })
    refresh()
  }

  const handleUpdate = async () => {
    if (editNode) {
      await apiFetch<LogisticsNodeItem>(
        `/projects/${projectId}/logistics/${editNode.id}`,
        {
          method: 'PATCH',
          body: {
            node_type: editNode.node_type,
            node_date: editNode.node_date,
            remark: editNode.remark,
            tracking_no:
              editNode.node_type === 'in_transit' ? editNode.tracking_no : undefined,
          },
        }
      )
      setEditingId(null)
      setEditNode(null)
      refresh()
    }
  }

  const handleDelete = (id: number) => {
    if (confirm('确定删除该物流节点?')) {
      deleteNode.mutate(id.toString())
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>物流时间线</CardTitle>
        <Button size="sm" onClick={() => setShowAddForm(!showAddForm)}>
          <Plus className="h-4 w-4" />
          添加节点
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-muted-foreground text-sm">加载中...</p>
        ) : (
          <>
            {showAddForm && (
              <div className="mb-6 rounded-lg border p-4 space-y-3 bg-muted/30">
                <h3 className="text-sm font-medium">添加物流节点</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs text-muted-foreground">节点类型</label>
                    <select
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      value={newNode.node_type}
                      onChange={(e) => setNewNode({ ...newNode, node_type: e.target.value })}
                    >
                      {nodeTypes.map((t) => (
                        <option key={t} value={t}>
                          {nodeTypeConfig[t].label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs text-muted-foreground">日期</label>
                    <Input
                      type="date"
                      value={newNode.node_date}
                      onChange={(e) => setNewNode({ ...newNode, node_date: e.target.value })}
                    />
                  </div>
                  {newNode.node_type === 'in_transit' && (
                    <div className="space-y-1">
                      <label className="text-xs text-muted-foreground">物流单号</label>
                      <Input
                        placeholder="请输入物流单号"
                        value={newNode.tracking_no}
                        onChange={(e) => setNewNode({ ...newNode, tracking_no: e.target.value })}
                      />
                    </div>
                  )}
                  <div className="space-y-1 md:col-span-2">
                    <label className="text-xs text-muted-foreground">备注</label>
                    <Input
                      placeholder="备注信息"
                      value={newNode.remark}
                      onChange={(e) => setNewNode({ ...newNode, remark: e.target.value })}
                    />
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="outline" size="sm" onClick={() => setShowAddForm(false)}>
                    取消
                  </Button>
                  <Button size="sm" onClick={handleAdd} disabled={postNode.isPending}>
                    <Save className="h-3 w-3" />
                    添加
                  </Button>
                </div>
              </div>
            )}

            {sortedNodes.length === 0 ? (
              <div className="py-8 text-center text-muted-foreground">
                <p className="text-sm">暂无物流节点,点击"添加节点"开始跟踪</p>
              </div>
            ) : (
              <div className="relative">
                <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border" />
                <div className="space-y-4">
                  {sortedNodes.map((node) => {
                    const config = nodeTypeConfig[node.node_type]
                    const isEditing = editingId === node.id

                    return (
                      <div key={node.id} className="relative pl-10">
                        <div
                          className={cn(
                            'absolute left-2.5 top-1 w-3 h-3 rounded-full border-2 border-background',
                            config?.color || 'bg-gray-500'
                          )}
                        />
                        <div className="rounded-lg border p-4">
                          {isEditing ? (
                            <div className="space-y-3">
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                <div className="space-y-1">
                                  <label className="text-xs text-muted-foreground">节点类型</label>
                                  <select
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                    value={editNode?.node_type}
                                    onChange={(e) =>
                                      setEditNode(editNode ? { ...editNode, node_type: e.target.value } : null)
                                    }
                                  >
                                    {nodeTypes.map((t) => (
                                      <option key={t} value={t}>
                                        {nodeTypeConfig[t].label}
                                      </option>
                                    ))}
                                  </select>
                                </div>
                                <div className="space-y-1">
                                  <label className="text-xs text-muted-foreground">日期</label>
                                  <Input
                                    type="date"
                                    value={editNode?.node_date || ''}
                                    onChange={(e) =>
                                      setEditNode(editNode ? { ...editNode, node_date: e.target.value } : null)
                                    }
                                  />
                                </div>
                                {editNode?.node_type === 'in_transit' && (
                                  <div className="space-y-1">
                                    <label className="text-xs text-muted-foreground">物流单号</label>
                                    <Input
                                      value={editNode?.tracking_no || ''}
                                      onChange={(e) =>
                                        setEditNode(
                                          editNode ? { ...editNode, tracking_no: e.target.value } : null
                                        )
                                      }
                                    />
                                  </div>
                                )}
                                <div className="space-y-1 md:col-span-2">
                                  <label className="text-xs text-muted-foreground">备注</label>
                                  <Input
                                    value={editNode?.remark || ''}
                                    onChange={(e) =>
                                      setEditNode(editNode ? { ...editNode, remark: e.target.value } : null)
                                    }
                                  />
                                </div>
                              </div>
                              <div className="flex justify-end gap-2">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => {
                                    setEditingId(null)
                                    setEditNode(null)
                                  }}
                                >
                                  取消
                                </Button>
                                <Button size="sm" onClick={handleUpdate}>
                                  保存
                                </Button>
                              </div>
                            </div>
                          ) : (
                            <div>
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <span
                                    className={cn(
                                      'inline-flex items-center justify-center w-6 h-6 rounded-full text-white',
                                      config?.color || 'bg-gray-500'
                                    )}
                                  >
                                    {config?.icon}
                                  </span>
                                  <span className="font-medium text-sm">{config?.label || node.node_type}</span>
                                </div>
                                <div className="flex items-center gap-1">
                                  <button
                                    className="p-1 rounded hover:bg-muted"
                                    onClick={() => {
                                      setEditingId(node.id)
                                      setEditNode(node)
                                    }}
                                  >
                                    <Edit2 className="h-3 w-3 text-muted-foreground" />
                                  </button>
                                  <button
                                    className="p-1 rounded hover:bg-muted"
                                    onClick={() => handleDelete(node.id)}
                                  >
                                    <Trash2 className="h-3 w-3 text-destructive" />
                                  </button>
                                </div>
                              </div>
                              <div className="mt-2 space-y-1 text-sm text-muted-foreground">
                                <p>日期: {formatDate(node.node_date)}</p>
                                {node.tracking_no && (
                                  <p>物流单号: <span className="font-medium text-foreground">{node.tracking_no}</span></p>
                                )}
                                {node.remark && <p>备注: {node.remark}</p>}
                                {node.attachment_key && (
                                  <p className="text-xs text-muted-foreground/80">已上传附件</p>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
