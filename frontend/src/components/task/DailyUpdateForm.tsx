import { useState, useEffect } from 'react'
import { Mic, Square, Play, Pause, Send, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Task, TaskStatus, Photo } from '@/types'
import { useApiPost } from '@/hooks/useApi'
import { toast } from '@/components/ui/Toast'
import { Dialog, DialogFooter } from '@/components/ui/Dialog'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'
import { formatDate } from '@/lib/utils'
import PhotoUploader from './PhotoUploader'

interface DailyUpdateFormProps {
  task: Task
  date?: string
  open: boolean
  onOpenChange: (open: boolean) => void
  onSubmitted?: () => void
}

const STATUS_OPTIONS = [
  { value: 'not_started', label: '未开始' },
  { value: 'in_progress', label: '进行中' },
  { value: 'completed', label: '完成' },
  { value: 'paused', label: '暂停' },
]

export default function DailyUpdateForm({
  task,
  date,
  open,
  onOpenChange,
  onSubmitted,
}: DailyUpdateFormProps) {
  const today = date || formatDate(new Date())
  const [status, setStatus] = useState<TaskStatus>(task.status)
  const [remark, setRemark] = useState('')
  const [photos, setPhotos] = useState<Photo[]>([])
  const [recording, setRecording] = useState(false)
  const [recordSeconds, setRecordSeconds] = useState(0)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [audioPlaying, setAudioPlaying] = useState(false)

  const submitMutation = useApiPost<void>(`/tasks/tasks/${task.id}/daily-updates`)

  useEffect(() => {
    if (open) {
      setStatus(task.status)
      setRemark('')
      setPhotos([])
      setAudioUrl(null)
      setRecordSeconds(0)
      setRecording(false)
    }
  }, [open, task.id, task.status])

  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null
    if (recording) {
      interval = setInterval(() => {
        setRecordSeconds((s) => s + 1)
      }, 1000)
    }
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [recording])

  const handleFileUpload = async (files: File[]) => {
    const newPhotos: Photo[] = files.map((file, index) => ({
      id: `temp-${Date.now()}-${index}`,
      url: URL.createObjectURL(file),
      thumbnail_url: URL.createObjectURL(file),
      caption: '',
      created_at: new Date().toISOString(),
    }))
    setPhotos((prev) => [...prev, ...newPhotos])
  }

  const handlePhotoDelete = (photoId: string) => {
    setPhotos((prev) => prev.filter((p) => p.id !== photoId))
  }

  const toggleRecording = () => {
    setRecording((r) => !r)
    if (recording) {
      setRecordSeconds(0)
    }
  }

  const toggleAudioPlay = () => {
    if (!audioUrl) return
    if (audioPlaying) {
      setAudioPlaying(false)
    } else {
      setAudioPlaying(true)
    }
  }

  const handleSubmit = async () => {
    try {
      await submitMutation.mutateAsync({
        task_id: task.id,
        status,
        remark,
        date: today,
        photos: photos.map((p) => ({ id: p.id, url: p.url, caption: p.caption })),
        audio_duration: recordSeconds,
      })
      toast.success({ title: '提交成功' })
      onSubmitted?.()
      onOpenChange(false)
    } catch {
      toast.error({ title: '提交失败', description: '请稍后重试' })
    }
  }

  const formatDuration = (seconds: number) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange} title={`填写今日更新 - ${task.name || task.title}`}>
      <div className="space-y-5">
        <div className="text-sm text-muted-foreground">
          日期: {today}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">状态</label>
          <Select
            value={status}
            onChange={(e) => setStatus(e.target.value as TaskStatus)}
            options={STATUS_OPTIONS}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">备注</label>
          <textarea
            value={remark}
            onChange={(e) => setRemark(e.target.value)}
            rows={3}
            placeholder="填写今日工作进展、遇到的问题等..."
            className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-none"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">语音备注</label>
          <div className="flex items-center gap-3 rounded-md border border-border p-3">
            <button
              onClick={toggleRecording}
              className={cn(
                'flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-colors',
                recording
                  ? 'bg-destructive text-destructive-foreground hover:bg-destructive/90'
                  : 'bg-surface hover:bg-accent'
              )}
            >
              {recording ? (
                <>
                  <Square className="h-4 w-4" />
                  停止
                </>
              ) : (
                <>
                  <Mic className="h-4 w-4" />
                  开始录音
                </>
              )}
            </button>
            {recording && (
              <span className="text-sm font-mono text-destructive animate-pulse">
                {formatDuration(recordSeconds)}
              </span>
            )}
            {!recording && recordSeconds > 0 && (
              <button
                onClick={toggleAudioPlay}
                className="flex items-center gap-1 text-sm text-primary hover:underline"
              >
                {audioPlaying ? (
                  <>
                    <Pause className="h-4 w-4" />
                    暂停
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" />
                    播放 ({formatDuration(recordSeconds)})
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        <PhotoUploader
          taskId={task.id}
          date={today}
          photos={photos}
          maxPhotos={2}
          onUpload={handleFileUpload}
          onDelete={handlePhotoDelete}
        />

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={submitMutation.isPending}
          >
            {submitMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                提交中
              </>
            ) : (
              <>
                <Send className="h-4 w-4" />
                提交
              </>
            )}
          </Button>
        </DialogFooter>
      </div>
    </Dialog>
  )
}