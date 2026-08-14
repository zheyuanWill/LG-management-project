import { useState } from 'react'
import { Trash2, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Dialog, DialogFooter } from '@/components/ui/Dialog'
import { toast } from '@/components/ui/Toast'

interface DeleteConfirmProps {
  /** 资源显示名（用于确认文案），如「项目」「调研」 */
  resourceName?: string
  /** 确认提示，必填且要明确说明删除后果 */
  description: string
  /** 触发器（按钮/图标）。未传则渲染默认红色"删除"按钮 */
  trigger?: React.ReactNode
  /** 触发器样式：默认 'icon'（仅图标，悬浮卡片中用）；'button'（带文字） */
  triggerVariant?: 'icon' | 'button'
  /** 触发器位置——卡片/列表项中常用 icon；详情页头部常用 button */
  size?: 'sm' | 'default'
  /** 删除 mutation（接收 id 字符串） */
  mutation: {
    mutate: (id: string, opts?: { onSuccess?: () => void; onError?: () => void }) => void
    isPending?: boolean
  }
  /** 资源 id（字符串，与 useApiDelete 的 mutation key 一致） */
  id: string
  /** 删除成功后回调（提示 + 跳转/刷新） */
  onDeleted?: () => void
}

/**
 * 通用删除确认组件：弹出 Dialog → 确认 → 调 mutation → 提示。
 * 用于项目、调研、商务、风险、日报、周报、客户、文件等可删除资源的统一交互。
 */
export default function DeleteConfirm({
  resourceName = '该项',
  description,
  trigger,
  triggerVariant = 'icon',
  size = 'sm',
  mutation,
  id,
  onDeleted,
}: DeleteConfirmProps) {
  const [open, setOpen] = useState(false)

  const handleConfirm = () => {
    mutation.mutate(id, {
      onSuccess: () => {
        toast.success({ title: `${resourceName}已删除` })
        setOpen(false)
        onDeleted?.()
      },
      onError: () => {
        toast.error({ title: '删除失败', description: '请稍后重试' })
      },
    })
  }

  return (
    <>
      {trigger ? (
        <span
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            setOpen(true)
          }}
        >
          {trigger}
        </span>
      ) : triggerVariant === 'icon' ? (
        <button
          type="button"
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            setOpen(true)
          }}
          className="inline-flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
          aria-label={`删除${resourceName}`}
          title={`删除${resourceName}`}
        >
          <Trash2 className="h-4 w-4" />
        </button>
      ) : (
        <Button
          variant="outline"
          size={size}
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            setOpen(true)
          }}
          className="text-destructive hover:bg-destructive/10 hover:text-destructive"
        >
          <Trash2 className="h-4 w-4" />
          删除
        </Button>
      )}

      <Dialog
        open={open}
        onOpenChange={setOpen}
        title={`确认删除${resourceName}`}
        description={description}
      >
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)} disabled={mutation.isPending}>
            取消
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={mutation.isPending}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {mutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
            确认删除
          </Button>
        </DialogFooter>
      </Dialog>
    </>
  )
}