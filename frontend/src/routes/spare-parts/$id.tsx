import { useState, useEffect } from 'react'
import { useParams } from '@tanstack/react-router'
import { ArrowLeft, Package, Plus, Loader2, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Input } from '@/components/ui/Input'
import { Tabs } from '@/components/ui/Tabs'
import { useApiGet, useApiDelete } from '@/hooks/useApi'
import { apiFetch } from '@/lib/api'
import { cn } from '@/lib/utils'
import { toast } from '@/components/ui/Toast'
import type { Project } from '@/types'
import SparePartForm from '@/components/spare/SparePartForm'
import LogisticsTimeline from '@/components/spare/LogisticsTimeline'

interface SparePartData {
  id: number
  item_name: string
  model_or_drawing: string | null
  quantity: string | null
}

export default function SparePartsDetail() {
  const { id } = useParams({ strict: false })
  const { data: project, isLoading } = useApiGet<Project>(`/projects/${id}`)

  const { data: parts } = useApiGet<SparePartData[]>(`/spare-parts/projects/${id}/spare-parts`, {
    retry: false,
  })
  const deletePart = useApiDelete<void>(`/spare-parts/projects/${id}/spare-parts`)

  const list = Array.isArray(parts) ? parts : []
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [adding, setAdding] = useState(false)
  const [newName, setNewName] = useState('')
  const [creating, setCreating] = useState(false)

  const effectiveId = selectedId ?? list[0]?.id?.toString() ?? undefined
  const selected = list.find((p) => String(p.id) === String(effectiveId))

  useEffect(() => {
    if (!selectedId && list.length > 0) {
      setSelectedId(list[0].id.toString())
    }
  }, [list, selectedId])

  if (isLoading) {
    return (
      <div className="py-16 text-center text-muted-foreground">
        <p>加载中...</p>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="py-16 text-center text-muted-foreground">
        <Package className="mx-auto h-12 w-12 opacity-50 mb-3" />
        <p className="text-lg">项目不存在</p>
      </div>
    )
  }

  const handleCreate = async () => {
    if (!newName.trim()) {
      toast.error({ title: '请输入备件品名' })
      return
    }
    setCreating(true)
    try {
      const created = await apiFetch<SparePartData>(`/spare-parts/projects/${id}/spare-parts`, {
        method: 'POST',
        body: {
          item_name: newName.trim(),
          model_or_drawing: null,
          quantity: null,
        },
      })
      setNewName('')
      setAdding(false)
      setSelectedId(created.id.toString())
      toast.success({ title: '备件已创建' })
    } catch {
      toast.error({ title: '创建失败' })
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = (partId: number) => {
    if (!confirm('确定删除该备件？其物流节点将一并删除。')) return
    deletePart.mutate(partId.toString(), {
      onSuccess: () => {
        if (String(partId) === selectedId) setSelectedId(null)
        toast.success({ title: '已删除' })
      },
    })
  }

  // 新布局：只有两个 tab —— 备件信息 + 物流时间线
  // 物流时间线已内置每节点文件上传（发货照→供应商发货、签收单→香港签收、发票→结算完成）
  const tabConfig = [
    {
      value: 'info',
      label: '备件信息',
      icon: <Package className="h-4 w-4" />,
      content: <SparePartForm projectId={String(project.id)} sparePartId={effectiveId} />,
    },
    {
      value: 'logistics',
      label: '物流时间线',
      icon: <Package className="h-4 w-4" />,
      content: <LogisticsTimeline projectId={String(project.id)} sparePartId={effectiveId} />,
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => window.history.back()}>
            <ArrowLeft className="h-4 w-4" />
            返回
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{project.ship_name}</h1>
            <p className="text-muted-foreground mt-1">项目编号: {project.project_no}</p>
          </div>
        </div>
        <Badge variant={project.status === 'active' ? 'default' : 'secondary'}>
          {project.status === 'active' ? '进行中' : '已完成'}
        </Badge>
      </div>

      {/* 备件选择器 */}
      <div className="rounded-lg border border-border p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">备件列表（一个项目可含多个备件）</span>
          <Button variant="outline" size="sm" onClick={() => setAdding((v) => !v)}>
            <Plus className="h-4 w-4" />
            新建备件
          </Button>
        </div>

        {adding && (
          <div className="flex items-center gap-2">
            <Input
              placeholder="备件品名，如:主机连杆"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
            />
            <Button size="sm" onClick={handleCreate} disabled={creating || !newName.trim()}>
              {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              创建
            </Button>
          </div>
        )}

        {list.length === 0 && !adding ? (
          <p className="text-sm text-muted-foreground">暂无备件，点击"新建备件"开始。</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {list.map((p) => (
              <div
                key={p.id}
                className={cn(
                  'group flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm cursor-pointer transition-colors',
                  String(p.id) === String(effectiveId)
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-border hover:border-primary/40'
                )}
                onClick={() => setSelectedId(p.id.toString())}
              >
                <Package className="h-3.5 w-3.5" />
                <span className="font-medium">{p.item_name}</span>
                {p.quantity ? <span className="text-xs opacity-70">×{p.quantity}</span> : null}
                <button
                  className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDelete(p.id)
                  }}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}

        {selected && (
          <p className="text-xs text-muted-foreground">
            当前选中：{selected.item_name}
            {selected.model_or_drawing ? ` · 型号 ${selected.model_or_drawing}` : ''}
          </p>
        )}
      </div>

      {/* 新布局：仅两个 tab */}
      <Tabs tabs={tabConfig} defaultValue="info" />
    </div>
  )
}
