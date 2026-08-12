import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import {
  Plus,
  Edit2,
  Trash2,
  Save,
  Truck,
  Package,
  CheckCircle,
  Upload,
  Paperclip,
  Loader2,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useApiGet, useApiPost, useApiDelete } from '@/hooks/useApi'
import apiClient, { apiFetch } from '@/lib/api'
import { cn } from '@/lib/utils'
import { formatDate } from '@/lib/utils'
import { toast } from '@/components/ui/Toast'

interface LogisticsNodeItem {
  id: number
  project_id: number
  spare_part_id?: number | null
  node_type: string
  node_date: string
  remark?: string
  tracking_no?: string
  attachment_key?: string
  created_at: string
}

interface LogisticsTimelineProps {
  projectId: string
  /** 选中某个备件后走「按备件」维度接口；不传则走项目级接口（兼容） */
  sparePartId?: string
}

// 必须与后端 LOGISTICS_NODE_ORDER 一致
const LOGISTICS_NODE_ORDER = [
  'ordered',
  'supplier_shipped',
  'in_transit',
  'arrived',
  'warehoused',
  'sent_to_owner',
  'hk_signed',
  'settled',
] as const

const nodeTypeConfig: Record<
  string,
  { label: string; icon: React.ReactNode; color: string; hint?: string }
> = {
  ordered: { label: '已下单', icon: <Package className="h-4 w-4" />, color: 'bg-blue-500' },
  supplier_shipped: {
    label: '供应商发货',
    icon: <Truck className="h-4 w-4" />,
    color: 'bg-purple-500',
    hint: '建议上传：供应商发货单',
  },
  in_transit: { label: '运输中', icon: <Truck className="h-4 w-4" />, color: 'bg-amber-500' },
  arrived: { label: '到港', icon: <Package className="h-4 w-4" />, color: 'bg-cyan-500' },
  warehoused: { label: '入库', icon: <Package className="h-4 w-4" />, color: 'bg-teal-500' },
  sent_to_owner: { label: '发给船东', icon: <Truck className="h-4 w-4" />, color: 'bg-indigo-500' },
  hk_signed: {
    label: '香港签收',
    icon: <CheckCircle className="h-4 w-4" />,
    color: 'bg-green-500',
    hint: '建议上传：香港签收单',
  },
  settled: {
    label: '结算完成',
    icon: <CheckCircle className="h-4 w-4" />,
    color: 'bg-emerald-500',
    hint: '建议上传：结算单 / 发票',
  },
}

export default function LogisticsTimeline({ projectId, sparePartId }: LogisticsTimelineProps) {
  const queryClient = useQueryClient()

  const listUrl = sparePartId
    ? `/spare-parts/projects/${projectId}/spare-parts/${sparePartId}/logistics`
    : `/spare-parts/projects/${projectId}/logistics`
  const postUrl = sparePartId
    ? `/spare-parts/projects/${projectId}/spare-parts/${sparePartId}/logistics`
    : `/spare-parts/projects/${projectId}/logistics`
  const deleteBase = sparePartId
    ? `/spare-parts/projects/${projectId}/spare-parts/${sparePartId}/logistics`
    : `/spare-parts/projects/${projectId}/logistics`

  const nodePatchUrl = (id: number) =>
    sparePartId
      ? `/spare-parts/projects/${projectId}/spare-parts/${sparePartId}/logistics/${id}`
      : `/spare-parts/projects/${projectId}/logistics/${id}`

  const { data: nodes, isLoading } = useApiGet<LogisticsNodeItem[]>(listUrl)
  const postNode = useApiPost<LogisticsNodeItem>(postUrl)
  const deleteNode = useApiDelete<void>(deleteBase)

  const [editingId, setEditingId] = useState<number | null>(null)
  const [editNode, setEditNode] = useState<LogisticsNodeItem | null>(null)
  const [addingType, setAddingType] = useState<string | null>(null)
  const [newNode, setNewNode] = useState({ node_date: '', remark: '', tracking_no: '', attachment_key: '' })
  const [uploadingId, setUploadingId] = useState<number | null>(null)

  // 已存在的节点按类型归并（同一类型可能多条）
  const byType: Record<string, LogisticsNodeItem[]> = {}
  ;(nodes || []).forEach((n) => {
    ;(byType[n.node_type] ||= []).push(n)
  })

  const refresh = () =>
    queryClient.invalidateQueries({ queryKey: [listUrl] })

  const handleAdd = async (nodeType: string) => {
    if (!newNode.node_date) {
      toast.error({ title: '请选择日期' })
      return
    }
    try {
      await postNode.mutateAsync({
        node_type: nodeType,
        node_date: newNode.node_date,
        remark: newNode.remark || undefined,
        tracking_no: nodeType === 'in_transit' ? newNode.tracking_no || undefined : undefined,
        attachment_key: newNode.attachment_key || undefined,
      })
      setAddingType(null)
      setNewNode({ node_date: '', remark: '', tracking_no: '', attachment_key: '' })
      refresh()
    } catch {
      toast.error({ title: '添加失败' })
    }
  }

  const handleUpdate = async () => {
    if (!editNode) return
    try {
      await apiFetch<LogisticsNodeItem>(nodePatchUrl(editNode.id), {
        method: 'PATCH',
        body: {
          node_type: editNode.node_type,
          node_date: editNode.node_date,
          remark: editNode.remark || undefined,
          tracking_no:
            editNode.node_type === 'in_transit' ? editNode.tracking_no || undefined : undefined,
          attachment_key: editNode.attachment_key || undefined,
        },
      })
      setEditingId(null)
      setEditNode(null)
      refresh()
    } catch {
      toast.error({ title: '保存失败' })
    }
  }

  const handleDelete = (id: number) => {
    if (confirm('确定删除该物流节点?')) {
      deleteNode.mutate(id.toString(), {
        onSuccess: refresh,
      })
    }
  }

  const handleUpload = async (node: LogisticsNodeItem, file: File) => {
    setUploadingId(node.id)
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('project_id', projectId)
      const res = await apiClient.post<{ storage_key: string }>('/files/upload', formData)
      await apiFetch<LogisticsNodeItem>(nodePatchUrl(node.id), {
        method: 'PATCH',
        body: { attachment_key: res.data.storage_key },
      })
      refresh()
      toast.success({ title: '附件已上传' })
    } catch {
      toast.error({ title: '上传失败' })
    } finally {
      setUploadingId(null)
    }
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>物流时间线</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">加载中...</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>物流时间线</CardTitle>
        {sparePartId && (
          <span className="text-xs text-muted-foreground">按备件维度跟踪</span>
        )}
      </CardHeader>
      <CardContent>
        <div className="relative">
          {/* 竖向主轴 */}
          <div className="absolute left-4 top-2 bottom-2 w-0.5 bg-border" />
          <div className="space-y-3">
            {LOGISTICS_NODE_ORDER.map((type) => {
              const items = byType[type] || []
              const config = nodeTypeConfig[type]
              const done = items.length > 0

              return (
                <div key={type} className="relative pl-10">
                  <div
                    className={cn(
                      'absolute left-2.5 top-1 w-3 h-3 rounded-full border-2 border-background',
                      done ? config.color : 'bg-gray-300'
                    )}
                  />
                  <div className="rounded-lg border p-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span
                          className={cn(
                            'inline-flex items-center justify-center w-6 h-6 rounded-full text-white',
                            done ? config.color : 'bg-gray-300'
                          )}
                        >
                          {config.icon}
                        </span>
                        <span className="font-medium text-sm">
                          {config.label}
                          {items.length > 1 && (
                            <span className="ml-1 text-xs text-muted-foreground">×{items.length}</span>
                          )}
                        </span>
                      </div>
                      {!done && addingType !== type && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setAddingType(type)
                            setNewNode({
                              node_date: new Date().toISOString().split('T')[0],
                              remark: '',
                              tracking_no: '',
                              attachment_key: '',
                            })
                          }}
                        >
                          <Plus className="h-3.5 w-3.5" />
                          记录
                        </Button>
                      )}
                    </div>

                    {config.hint && !done && (
                      <p className="mt-1 text-xs text-muted-foreground">{config.hint}</p>
                    )}

                    {/* 已存在节点 */}
                    {items.map((node) => {
                      const isEditing = editingId === node.id
                      const fileInputId = `node-file-${node.id}`
                      if (isEditing && editNode) {
                        return (
                          <div key={node.id} className="mt-3 space-y-2 rounded-md bg-muted/40 p-3">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                              <Input
                                type="date"
                                value={editNode.node_date}
                                onChange={(e) =>
                                  setEditNode({ ...editNode, node_date: e.target.value })
                                }
                              />
                              {editNode.node_type === 'in_transit' && (
                                <Input
                                  placeholder="物流单号"
                                  value={editNode.tracking_no || ''}
                                  onChange={(e) =>
                                    setEditNode({ ...editNode, tracking_no: e.target.value })
                                  }
                                />
                              )}
                              <div className="md:col-span-2">
                                <Input
                                  placeholder="备注"
                                  value={editNode.remark || ''}
                                  onChange={(e) =>
                                    setEditNode({ ...editNode, remark: e.target.value })
                                  }
                                />
                              </div>
                            </div>
                            <div className="flex justify-end gap-2">
                              <Button variant="outline" size="sm" onClick={() => {
                                setEditingId(null)
                                setEditNode(null)
                              }}>
                                取消
                              </Button>
                              <Button size="sm" onClick={handleUpdate} disabled={patchNode.isPending}>
                                <Save className="h-3.5 w-3.5" />
                                保存
                              </Button>
                            </div>
                          </div>
                        )
                      }
                      return (
                        <div key={node.id} className="mt-2 space-y-1 text-sm text-muted-foreground">
                          <p>日期: {formatDate(node.node_date)}</p>
                          {node.tracking_no && (
                            <p>
                              物流单号: <span className="font-medium text-foreground">{node.tracking_no}</span>
                            </p>
                          )}
                          {node.remark && <p>备注: {node.remark}</p>}
                          {node.attachment_key && (
                            <p className="flex items-center gap-1 text-xs text-primary">
                              <Paperclip className="h-3 w-3" />
                              已上传附件
                            </p>
                          )}
                          <div className="flex items-center gap-1 pt-1">
                            <label
                              htmlFor={fileInputId}
                              className="inline-flex items-center gap-1 cursor-pointer text-xs text-primary hover:opacity-80"
                            >
                              <Upload className="h-3.5 w-3.5" />
                              {uploadingId === node.id ? '上传中…' : '上传文件'}
                            </label>
                            <input
                              id={fileInputId}
                              type="file"
                              className="hidden"
                              onChange={(e) => {
                                const f = e.target.files?.[0]
                                if (f) handleUpload(node, f)
                                e.target.value = ''
                              }}
                            />
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
                      )
                    })}

                    {/* 新增该类型节点表单 */}
                    {addingType === type && (
                      <div className="mt-3 space-y-2 rounded-md bg-muted/40 p-3">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          <Input
                            type="date"
                            value={newNode.node_date}
                            onChange={(e) => setNewNode({ ...newNode, node_date: e.target.value })}
                          />
                          {type === 'in_transit' && (
                            <Input
                              placeholder="物流单号"
                              value={newNode.tracking_no}
                              onChange={(e) => setNewNode({ ...newNode, tracking_no: e.target.value })}
                            />
                          )}
                          <div className="md:col-span-2">
                            <Input
                              placeholder="备注"
                              value={newNode.remark}
                              onChange={(e) => setNewNode({ ...newNode, remark: e.target.value })}
                            />
                          </div>
                        </div>
                        <div className="flex justify-end gap-2">
                          <Button variant="outline" size="sm" onClick={() => setAddingType(null)}>
                            取消
                          </Button>
                          <Button size="sm" onClick={() => handleAdd(type)} disabled={postNode.isPending}>
                            {postNode.isPending ? (
                              <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            ) : (
                              <Save className="h-3.5 w-3.5" />
                            )}
                            添加
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
