import { useState } from 'react'
import { ArrowRight, CheckCircle, Info } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'
import { useApiGet, useApiPatch } from '@/hooks/useApi'
import { cn } from '@/lib/utils'

interface HandoverData {
  handed_over: boolean
  handed_over_at?: string
}

interface RepairHandoverProps {
  projectId: string
}

export default function RepairHandover({ projectId }: RepairHandoverProps) {
  const { data: handover, isLoading } = useApiGet<HandoverData>(
    `/projects/${projectId}/handover`
  )
  const patchHandover = useApiPatch<HandoverData>(`/projects/${projectId}/handover`)

  const [showConfirm, setShowConfirm] = useState(false)
  const [isToggling, setIsToggling] = useState(false)

  const isHandedOver = handover?.handed_over || false

  const handleToggle = async () => {
    if (!isHandedOver) {
      setShowConfirm(true)
    } else {
      setShowConfirm(true)
    }
  }

  const handleConfirm = async () => {
    setIsToggling(true)
    try {
      await patchHandover.mutateAsync({
        handed_over: !isHandedOver,
        handed_over_at: !isHandedOver ? new Date().toISOString() : undefined,
      })
      setShowConfirm(false)
    } finally {
      setIsToggling(false)
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
                      ? `移交时间: ${handover?.handed_over_at ? new Date(handover.handed_over_at).toLocaleString() : '-'}`
                      : '点击右侧按钮进行移交操作'}
                  </p>
                </div>
              </div>
              <Button
                onClick={handleToggle}
                variant={isHandedOver ? 'secondary' : 'default'}
                disabled={isToggling}
              >
                {isHandedOver ? '撤回移交' : '移交监修'}
              </Button>
            </div>

            <div className="flex items-start gap-3 rounded-lg bg-muted p-4">
              <Info className="h-5 w-5 text-muted-foreground shrink-0 mt-0.5" />
              <div className="text-sm text-muted-foreground">
                <p className="font-medium text-foreground mb-1">移交说明</p>
                <ul className="space-y-1 list-disc list-inside">
                  <li>移交后项目编号不变,自动在监修模块可见</li>
                  <li>船东、船舶信息等数据将同步至监修模块</li>
                  <li>移交后无法修改项目基本信息</li>
                </ul>
              </div>
            </div>
          </>
        )}

        <Dialog
          open={showConfirm}
          onOpenChange={setShowConfirm}
          title={isHandedOver ? '撤回移交' : '确认移交'}
          description={
            isHandedOver
              ? '撤回后项目将不再在监修模块可见,确定要撤回吗?'
              : '移交后项目编号不变,自动在监修模块可见。确定要移交吗?'
          }
        >
          <div className="flex justify-end gap-2 mt-6">
            <Button variant="outline" onClick={() => setShowConfirm(false)}>
              取消
            </Button>
            <Button onClick={handleConfirm} disabled={isToggling}>
              {isToggling ? '处理中...' : isHandedOver ? '确认撤回' : '确认移交'}
            </Button>
          </div>
        </Dialog>
      </CardContent>
    </Card>
  )
}