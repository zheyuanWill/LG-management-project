import { useState, useEffect, useMemo } from 'react'
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
  defaultType?: string
}

export default function ProjectForm({
  open,
  onOpenChange,
  project,
  onSaved,
  defaultType = 'supervision',
}: ProjectFormProps) {
  const isEdit = !!project

  const [shipName, setShipName] = useState('')
  const [imo, setImo] = useState('')
  const [ownerId, setOwnerId] = useState('')
  const [plannedDate, setPlannedDate] = useState('')
  const [remarks, setRemarks] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})

  // Inline customer creation
  const [showNewCustomer, setShowNewCustomer] = useState(false)
  const [newCustomerName, setNewCustomerName] = useState('')
  const [creatingCustomer, setCreatingCustomer] = useState(false)

  const { data: customers, refetch: refetchCustomers } = useApiGet<Customer[]>('/customers')
  const { data: allProjects } = useApiGet<Project[]>('/projects')

  // Extract unique ship names from existing projects
  const shipNameOptions = useMemo(() => {
    const names = new Set<string>()
    allProjects?.forEach((p) => {
      if (p.ship_name) names.add(p.ship_name)
    })
    return Array.from(names).sort()
  }, [allProjects])

  // Find IMO for selected ship name
  const selectedShipImo = useMemo(() => {
    if (!shipName) return ''
    const found = allProjects?.find((p) => p.ship_name === shipName)
    return found?.imo || ''
  }, [shipName, allProjects])

  const createMutation = useApiPost<Project>('/projects')
  const updateMutation = useApiPatch<Project>(
    project ? `/projects/${project.id}` : '/projects'
  )
  const createCustomerMutation = useApiPost<Customer>('/customers')

  useEffect(() => {
    if (open) {
      setShipName(project?.ship_name || '')
      setImo(project?.imo || '')
      setOwnerId(project?.owner_id ? String(project.owner_id) : '')
      setPlannedDate(project?.planned_completion_date || '')
      setRemarks(project?.remarks || '')
      setErrors({})
      setShowNewCustomer(false)
      setNewCustomerName('')
    }
  }, [open, project])

  const customerOptions = [
    { value: '', label: '选择船东...' },
    ...(customers?.map((c) => ({ value: String(c.id), label: c.name })) || []),
    { value: '__new__', label: '+ 新增船东...' },
  ]

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}
    if (!shipName.trim()) {
      newErrors.shipName = '请输入船名'
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleAddCustomer = async () => {
    if (!newCustomerName.trim()) {
      toast.error({ title: '请输入船东名称' })
      return
    }
    setCreatingCustomer(true)
    try {
      await createCustomerMutation.mutateAsync({ name: newCustomerName.trim() })
      toast.success({ title: '船东添加成功' })
      setNewCustomerName('')
      setShowNewCustomer(false)
      refetchCustomers()
    } catch {
      toast.error({ title: '添加船东失败' })
    } finally {
      setCreatingCustomer(false)
    }
  }

  const onSubmit = async () => {
    if (!validate()) return

    try {
      const payload = {
        ship_name: shipName.trim(),
        imo: imo || undefined,
        owner_id: ownerId && ownerId !== '__new__' ? Number(ownerId) : undefined,
        planned_completion_date: plannedDate || undefined,
        remarks: remarks || undefined,
      }

      if (isEdit && project) {
        await updateMutation.mutateAsync(payload)
        toast.success({ title: '项目更新成功' })
      } else {
        await createMutation.mutateAsync({
          ...payload,
          type: defaultType,
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
      title={isEdit ? '编辑项目' : '新建项目'}
      className="max-w-xl"
    >
      <form onSubmit={(e) => { e.preventDefault(); onSubmit() }} className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">船名 *</label>
          <div className="relative">
            <Input
              value={shipName}
              onChange={(e) => {
                setShipName(e.target.value)
                // Auto-fill IMO when selecting from history
                if (!imo && e.target.value) {
                  const found = allProjects?.find((p) => p.ship_name === e.target.value)
                  if (found?.imo) setImo(found.imo)
                }
              }}
              placeholder="输入或选择船名"
              list="ship-name-list"
            />
            <datalist id="ship-name-list">
              {shipNameOptions.map((name) => (
                <option key={name} value={name} />
              ))}
            </datalist>
          </div>
          {errors.shipName && (
            <p className="text-sm text-destructive">{errors.shipName}</p>
          )}
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
            onChange={(e) => {
              const val = e.target.value
              if (val === '__new__') {
                setShowNewCustomer(true)
              } else {
                setOwnerId(val)
                setShowNewCustomer(false)
              }
            }}
            options={customerOptions}
          />
          {showNewCustomer && (
            <div className="flex gap-2 mt-2">
              <Input
                value={newCustomerName}
                onChange={(e) => setNewCustomerName(e.target.value)}
                placeholder="输入船东名称"
                className="flex-1"
              />
              <Button
                type="button"
                size="sm"
                onClick={handleAddCustomer}
                disabled={creatingCustomer || !newCustomerName.trim()}
              >
                {creatingCustomer ? '添加中...' : '添加'}
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => { setShowNewCustomer(false); setNewCustomerName('') }}
              >
                取消
              </Button>
            </div>
          )}
        </div>

        <div className="space-y-2">
          <DatePicker
            label="计划完成日期"
            value={plannedDate}
            onChange={(e) => setPlannedDate(e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">备注</label>
          <textarea
            value={remarks}
            onChange={(e) => setRemarks(e.target.value)}
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