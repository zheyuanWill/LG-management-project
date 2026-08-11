import { useState } from 'react'
import { Plus, Search, Loader2 } from 'lucide-react'
import { Table, TableBody, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Dialog, DialogFooter } from '@/components/ui/Dialog'
import { Select } from '@/components/ui/Select'
import type { Task } from '@/types'
import { useApiPost } from '@/hooks/useApi'
import { toast } from '@/components/ui/Toast'
import TaskItem from './TaskItem'

interface TaskListProps {
  projectId: string
  tasks: Task[]
  onTasksChange?: () => void
}

const TASK_STATUS_OPTIONS = [
  { value: 'not_started', label: '未开始' },
  { value: 'in_progress', label: '进行中' },
  { value: 'completed', label: '完成' },
  { value: 'paused', label: '暂停' },
]

const PRIORITY_OPTIONS = [
  { value: 'low', label: '低' },
  { value: 'medium', label: '中' },
  { value: 'high', label: '高' },
]

export default function TaskList({ projectId, tasks, onTasksChange }: TaskListProps) {
  const [showNewDialog, setShowNewDialog] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newStatus, setNewStatus] = useState<string>('not_started')
  const [newPriority, setNewPriority] = useState<string>('medium')
  const [newDueDate, setNewDueDate] = useState('')
  const [newDescription, setNewDescription] = useState('')
  const [search, setSearch] = useState('')

  const createMutation = useApiPost<Task>(`/projects/${projectId}/tasks`)

  const filteredTasks = tasks.filter((task) =>
    task.title.toLowerCase().includes(search.toLowerCase())
  )

  const handleCreate = async () => {
    if (!newTitle.trim()) {
      toast.warning({ title: '请输入任务名称' })
      return
    }
    try {
      await createMutation.mutateAsync({
        title: newTitle.trim(),
        status: newStatus,
        priority: newPriority,
        due_date: newDueDate || undefined,
        description: newDescription || undefined,
      })
      toast.success({ title: '任务创建成功' })
      setNewTitle('')
      setNewStatus('not_started')
      setNewPriority('medium')
      setNewDueDate('')
      setNewDescription('')
      setShowNewDialog(false)
      onTasksChange?.()
    } catch {
      toast.error({ title: '创建失败', description: '请稍后重试' })
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="relative w-64">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="搜索任务..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button onClick={() => setShowNewDialog(true)}>
          <Plus className="h-4 w-4" />
          新增任务
        </Button>
      </div>

      {filteredTasks.length === 0 ? (
        <div className="py-12 text-center text-muted-foreground">
          <p>暂无任务数据</p>
        </div>
      ) : (
        <div className="rounded-lg border border-border overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-1/3">任务名称</TableHead>
                <TableHead className="w-28">计划结束</TableHead>
                <TableHead className="w-32">状态</TableHead>
                <TableHead className="w-24">优先级</TableHead>
                <TableHead className="w-28">创建时间</TableHead>
                <TableHead className="w-40">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredTasks.map((task) => (
                <TaskItem
                  key={task.id}
                  task={task}
                  onUpdate={onTasksChange}
                  onDelete={onTasksChange}
                />
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <Dialog
        open={showNewDialog}
        onOpenChange={setShowNewDialog}
        title="新增任务"
      >
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">任务名称</label>
            <Input
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="输入任务名称"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">状态</label>
              <Select
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
                options={TASK_STATUS_OPTIONS}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">优先级</label>
              <Select
                value={newPriority}
                onChange={(e) => setNewPriority(e.target.value)}
                options={PRIORITY_OPTIONS}
              />
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">计划结束日期</label>
            <Input
              type="date"
              value={newDueDate}
              onChange={(e) => setNewDueDate(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">描述</label>
            <textarea
              value={newDescription}
              onChange={(e) => setNewDescription(e.target.value)}
              rows={3}
              placeholder="任务描述（可选）"
              className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-none"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNewDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCreate} disabled={createMutation.isPending}>
              {createMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  创建中
                </>
              ) : (
                '创建'
              )}
            </Button>
          </DialogFooter>
        </div>
      </Dialog>
    </div>
  )
}