import { useState } from 'react'
import { Pencil, Trash2, Calendar, History } from 'lucide-react'
import type { Task, TaskStatus } from '@/types'
import { TASK_STATUS_LABELS } from '@/lib/constants'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'
import DailyUpdateForm from './DailyUpdateForm'
import DailyUpdateHistory from './DailyUpdateHistory'
import { useApiDelete, useApiPatch } from '@/hooks/useApi'
import { toast } from '@/components/ui/Toast'
import { formatDate } from '@/lib/utils'

interface TaskItemProps {
  task: Task
  onUpdate?: () => void
  onDelete?: () => void
}

const STATUS_BADGE_VARIANTS: Record<TaskStatus, 'default' | 'secondary' | 'accent' | 'destructive'> = {
  not_started: 'secondary',
  in_progress: 'default',
  completed: 'secondary',
  paused: 'accent',
}

export default function TaskItem({ task, onUpdate, onDelete }: TaskItemProps) {
  const [updateOpen, setUpdateOpen] = useState(false)
  const [historyOpen, setHistoryOpen] = useState(false)
  const [status, setStatus] = useState<TaskStatus>(task.status)

  const deleteMutation = useApiDelete<void>(`/tasks`)
  const statusMutation = useApiPatch<void>(`/tasks/${task.id}`)

  const handleStatusChange = async (newStatus: TaskStatus) => {
    setStatus(newStatus)
    try {
      await statusMutation.mutateAsync({ status: newStatus })
      toast.success({ title: '状态已更新' })
      onUpdate?.()
    } catch {
      setStatus(task.status)
      toast.error({ title: '状态更新失败' })
    }
  }

  const handleDelete = async () => {
    if (!confirm(`确定删除任务 "${task.name}" 吗？`)) return
    try {
      await deleteMutation.mutateAsync(task.id)
      toast.success({ title: '任务已删除' })
      onDelete?.()
    } catch {
      toast.error({ title: '删除失败' })
    }
  }

  const today = formatDate(new Date())

  return (
    <>
      <tr className="border-b border-border transition-colors hover:bg-muted/30">
        <td className="p-4">
          <div className="font-medium text-sm">{task.name}</div>
          {task.description && (
            <div className="text-xs text-muted-foreground mt-0.5 line-clamp-1">
              {task.description}
            </div>
          )}
        </td>
        <td className="p-4 text-sm text-muted-foreground">
          {task.due_date ? formatDate(task.due_date) : '-'}
        </td>
        <td className="p-4">
          <div className="flex items-center gap-2">
            <Select
              value={status}
              onChange={(e) => handleStatusChange(e.target.value as TaskStatus)}
              options={[
                { value: 'not_started', label: '未开始' },
                { value: 'in_progress', label: '进行中' },
                { value: 'completed', label: '完成' },
                { value: 'paused', label: '暂停' },
              ]}
              className="h-8 w-28 text-xs"
            />
          </div>
        </td>
        <td className="p-4">
          <Badge
            variant={STATUS_BADGE_VARIANTS[status]}
          >
            {TASK_STATUS_LABELS[status]}
          </Badge>
        </td>
        <td className="p-4 text-sm text-muted-foreground">
          {task.due_date ? (
            <span className="inline-flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {task.due_date}
            </span>
          ) : (
            '-'
          )}
        </td>
        <td className="p-4">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setUpdateOpen(true)}
              className="text-primary"
            >
              <Pencil className="h-4 w-4" />
              填写今日更新
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setHistoryOpen(true)}
              className="text-muted-foreground"
            >
              <History className="h-4 w-4" />
              历史记录
            </Button>
            <button
              onClick={handleDelete}
              className="rounded-md p-2 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
              title="删除任务"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </td>
      </tr>

      <DailyUpdateForm
        task={task}
        date={today}
        open={updateOpen}
        onOpenChange={setUpdateOpen}
        onSubmitted={onUpdate}
      />

      <DailyUpdateHistory
        task={task}
        open={historyOpen}
        onOpenChange={setHistoryOpen}
      />
    </>
  )
}