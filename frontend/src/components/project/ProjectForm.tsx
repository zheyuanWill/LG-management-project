import { useState, useEffect } from 'react'
import { Loader2 } from 'lucide-react'
import { Dialog, DialogFooter } from '@/components/ui/Dialog'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { DatePicker } from '@/components/ui/DatePicker'
import { useApiPost, useApiPatch } from '@/hooks/useApi'
import { useApiGet } from '@/hooks/useApi'
import { toast } from '@/components/ui/Toast'
import type { Project, Customer } from '@/types'

interface ProjectFormProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  project?: Project | null
  onSaved?: () => void
}

export default function ProjectForm({
  open,
  onOpenChange,
  project,
  onSaved,
}: ProjectFormProps) {
  const isEdit = !!project

  const [name, setName] = useState('')
  const [imo, setImo] = useState('')
  const [customerId, setCustomerId] = useState('')
  const [plannedEndDate, setPlannedEndDate] = useState('')
  const [description, setDescription] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})

  const { data: customers } = useApiGet<Customer[]>('/customers')

  const createMutation = useApiPost<Project>('/projects')
  const updateMutation = useApiPatch<Project>(
    project ? `/projects/${project.id}` : '/projects'
  )

  useEffect(() => {
    if (open) {
      setName(project?.vessel_name || project?.name || '')
      setImo(project?.imo || '')
      setCustomerId(project?.customer_id || '')
      setPlannedEndDate(project?.planned_end_date || '')
      setDescription(project?.description || '')
      setErrors({})
    }
  }, [open, project])

  const customerOptions = [
    { value: '', label: '选择船东...' },
    ...(customers?.map((c) => ({ value: c.id, label: c.name })) || []),
  ]

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}
    if (!name.trim()) {
      newErrors.name = '请输入船名'
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const onSubmit = async () => {
    if (!validate()) return

    try {
      const payload = {
        name: name.trim(),
        vessel_name: name.trim(),
        imo: imo || undefined,
        customer_id: customerId || undefined,
        planned_end_date: plannedEndDate || undefined,
        description: description || undefined,
      }

      if (isEdit && project) {
        await updateMutation.mutateAsync(payload)
        toast.success({ title: '项目更新成功' })
      } else {
        await createMutation.mutateAsync({
          ...payload,
          type: 'supervision',
          status: 'active',
          progress: 0,
        })
        toast.success({ title: '项目创建成功' })
      }
      onSaved?.()
      onOpenChange(false)
    } catch {
      toast.error({
        title: isEdit ? '更新失败' : '创建失败',
        description: '请稍后重试',
      })
    }
  }

  const isSubmitting = createMutation.isPending || updateMutation.isPending

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? '编辑监修项目' : '新建监修项目'}
      className="max-w-xl"
    >
      <form onSubmit={(e) => { e.preventDefault(); onSubmit() }} className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">船名 *</label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="输入船名"
          />
          {errors.name && (
            <p className="text-sm text-destructive">{errors.name}</p>
          )}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">IMO 编号</label>
          <Input
            value={imo}
            onChange={(e) => setImo(e.target.value)}
            placeholder="输入 IMO 编号"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">船东</label>
          <Select
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            options={customerOptions}
          />
        </div>

        <div className="space-y-2">
          <DatePicker
            label="计划出厂日期"
            value={plannedEndDate}
            onChange={(e) => setPlannedEndDate(e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">备注</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            placeholder="项目备注信息"
            className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-none"
          />
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            取消
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                {isEdit ? '保存中' : '创建中'}
              </>
            ) : (
              isEdit ? '保存' : '创建'
            )}
          </Button>
        </DialogFooter>
      </form>
    </Dialog>
  )
}