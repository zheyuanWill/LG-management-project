import { Loader2 } from 'lucide-react'
import type { Task, TaskStatus } from '@/types'
import { TASK_STATUS_LABELS } from '@/lib/constants'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Dialog, DialogFooter } from '@/components/ui/Dialog'
import { useApiGet } from '@/hooks/useApi'
import { formatDate } from '@/lib/utils'

interface DailyUpdateRecord {
  id: number
  task_id: number
  update_date: string
  status: TaskStatus | null
  remark: string | null
  audio_duration: number | null
  photos: { id: number }[]
  created_at: string
}

function TaskPhotoThumb({ photoId }: { photoId: number }) {
  const { data } = useApiGet<{ url: string }>(`/tasks/task-photos/${photoId}/url`)
  if (!data?.url) {
    return <div className="w-20 h-20 rounded-md bg-muted animate-pulse" />
  }
  return (
    <img
      src={data.url}
      alt="现场照片"
      className="w-20 h-20 rounded-md object-cover border border-border"
    />
  )
}

interface DailyUpdateHistoryProps {
  task: Task
  open: boolean
  onOpenChange: (open: boolean) => void
}

export default function DailyUpdateHistory({
  task,
  open,
  onOpenChange,
}: DailyUpdateHistoryProps) {
  const { data: updates, isLoading } = useApiGet<DailyUpdateRecord[]>(
    `/tasks/${task.id}/daily-updates`,
    { enabled: open }
  )

  return (
    <Dialog open={open} onOpenChange={onOpenChange} title={`历史更新记录 - ${task.name}`}>
      <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
        {isLoading && (
          <div className="flex items-center justify-center py-10 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="ml-2 text-sm">加载中…</span>
          </div>
        )}

        {!isLoading && (!updates || updates.length === 0) && (
          <div className="py-12 text-center text-muted-foreground">
            暂无历史更新记录
          </div>
        )}

        {updates?.map((u) => (
          <div
            key={u.id}
            className="rounded-lg border border-border p-3 space-y-2"
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">{formatDate(u.update_date)}</span>
              {u.status && (
                <Badge variant="secondary">{TASK_STATUS_LABELS[u.status]}</Badge>
              )}
            </div>
            {u.remark && (
              <p className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
                {u.remark}
              </p>
            )}
            {u.audio_duration ? (
              <p className="text-xs text-muted-foreground">
                语音备注时长: {u.audio_duration}s
              </p>
            ) : null}
            {u.photos && u.photos.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {u.photos.map((p) => (
                  <TaskPhotoThumb key={p.id} photoId={p.id} />
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={() => onOpenChange(false)}>
          关闭
        </Button>
      </DialogFooter>
    </Dialog>
  )
}
