import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { ArrowRight, CheckCircle, Info } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'
import { useApiGet, useApiPost } from '@/hooks/useApi'
import { cn } from '@/lib/utils'
import { toast } from '@/components/ui/Toast'
import type { Project } from '@/types'

interface RepairHandoverProps {
  projectId: string
}

export default function RepairHandover({ projectId }: RepairHandoverProps) {
  const queryClient = useQueryClient()
  const { data: project, isLoading } = useApiGet<Project>(
    `/projects/${projectId}`
  )
  const handoverMutation = useApiPost<Project>(
    `/projects/${projectId}/handover-to-supervision`
  )

  const [showConfirm, setShowConfirm] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Handover is one-way: backend converts a brokerage_repair project to a
  // supervision project, so the handed-over state is derivable from type.
  const isHandedOver = project?.type === 'supervision'

  const handleConfirm = async () => {
    setIsSubmitting(true)
    try {
      await handoverMutation.mutateAsync({})
      setShowConfirm(false)
      await queryClient.invalidateQueries({
        queryKey: [`/projects/${projectId}`],
      })
      toast.success({ title: '已移交监修' })
    } catch {
      toast.error({ title: '移交失败', description: '请稍后重试' })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>移交监修</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {isLoading ? (
          <p className="text-muted-foreground text-sm">加载中...</p>
        ) : (
          <>
            <div className="flex items-center justify-between rounded-lg border p-6">
              <div className="flex items-center gap-4">
                <div
                  className={cn(
                    'rounded-full p-3 transition-colors',
                    isHandedOver
                      ? 'bg-green-100 dark:bg-green-900/30'
                      : 'bg-muted'
                  )}
                >
                  {isHandedOver ? (
                    <CheckCircle className="h-6 w-6 text-green-600" />
                  ) : (
                    <ArrowRight className="h-6 w-6 text-muted-foreground" />
                  )}
                </div>
                <div>
                  <p className="font-medium">
                    {isHandedOver ? '已移交监修' : '未移交'}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {isHandedOver
                      ? '项目已移交至监修模块,可在监修列表查看'
                      : '点击右侧按钮将修船经纪项目移交至监修模块'}
                  </p>
                </div>
              </div>
              {!isHandedOver && (
                <Button onClick={() => setShowConfirm(true)} disabled={isSubmitting}>
                  移交监修
                </Button>
              )}
            </div>

            <div className="flex items-start gap-3 rounded-lg bg-muted p-4">
              <Info className="h-5 w-5 text-muted-foreground shrink-0 mt-0.5" />
              <div className="text-sm text-muted-foreground">
                <p className="font-medium text-foreground mb-1">移交说明</p>
                <ul className="space-y-1 list-disc list-inside">
                  <li>移交后项目编号不变,自动在监修模块可见</li>
                  <li>船东、船舶信息等数据将同步至监修模块</li>
                  <li>移交后项目类型变更为监修,系统将自动创建监修任务</li>
                </ul>
              </div>
            </div>
          </>
        )}

        <Dialog
          open={showConfirm}
          onOpenChange={setShowConfirm}
          title="确认移交"
          description="移交后项目编号不变,自动在监修模块可见,且项目类型将变更为监修。确定要移交吗?"
        >
          <div className="flex justify-end gap-2 mt-6">
            <Button variant="outline" onClick={() => setShowConfirm(false)}>
              取消
            </Button>
            <Button onClick={handleConfirm} disabled={isSubmitting}>
              {isSubmitting ? '处理中...' : '确认移交'}
            </Button>
          </div>
        </Dialog>
      </CardContent>
    </Card>
  )
}
