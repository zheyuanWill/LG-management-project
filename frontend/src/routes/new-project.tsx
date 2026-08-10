import { useState } from 'react'
import { useNavigate, useSearch } from '@tanstack/react-router'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { useApiPost, useApiGet } from '@/hooks/useApi'
import { toast } from '@/components/ui/Toast'
import type { Customer } from '@/types'

const typeLabels: Record<string, string> = {
  supervision: '监修项目',
  brokerage_sale: '买卖经纪',
  brokerage_repair: '修船经纪',
  spare_parts: '备件供应',
}

export default function NewProjectPage() {
  const navigate = useNavigate()
  const { type = 'supervision' } = useSearch({ from: '/projects/new' })

  const [shipName, setShipName] = useState('')
  const [imo, setImo] = useState('')
  const [ownerId, setOwnerId] = useState('')
  const [plannedDate, setPlannedDate] = useState('')

  const { data: customers } = useApiGet<Customer[]>('/customers')
  const createMutation = useApiPost('/projects')

  const customerOptions = [
    { value: '', label: '选择船东...' },
    ...(customers?.map((c) => ({ value: String(c.id), label: c.name })) || []),
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!shipName.trim()) {
      toast.error({ title: '请输入船名' })
      return
    }
    try {
      await createMutation.mutateAsync({
        ship_name: shipName.trim(),
        imo: imo || undefined,
        owner_id: ownerId ? Number(ownerId) : undefined,
        type,
        planned_completion_date: plannedDate || undefined,
      })
      toast.success({ title: '项目创建成功' })
      navigate({ to: `/${type.replace('_', '-')}` })
    } catch {
      toast.error({ title: '创建失败', description: '请稍后重试' })
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate({ to: -1 })}>
          <ArrowLeft className="h-4 w-4 mr-1" />
          返回
        </Button>
        <div>
          <h1 className="text-3xl font-bold">新建{typeLabels[type] || '项目'}</h1>
          <p className="text-muted-foreground mt-1">填写项目基本信息</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="max-w-xl space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">船名 *</label>
          <Input
            value={shipName}
            onChange={(e) => setShipName(e.target.value)}
            placeholder="输入船名"
            required
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">IMO 编号</label>
          <Input
            value={imo}
            onChange={(e) => setImo(e.target.value)}
            placeholder="输入 IMO 编号（可选）"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">船东</label>
          <Select
            value={ownerId}
            onChange={(e) => setOwnerId(e.target.value)}
            options={customerOptions}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">计划完成日期</label>
          <Input
            type="date"
            value={plannedDate}
            onChange={(e) => setPlannedDate(e.target.value)}
          />
        </div>

        <div className="flex gap-3 pt-4">
          <Button type="button" variant="outline" onClick={() => navigate({ to: -1 })}>
            取消
          </Button>
          <Button type="submit" disabled={createMutation.isPending}>
            {createMutation.isPending ? '创建中...' : '创建项目'}
          </Button>
        </div>
      </form>
    </div>
  )
}
