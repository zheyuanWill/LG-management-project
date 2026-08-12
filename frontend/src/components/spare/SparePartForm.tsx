import { useState, useEffect } from 'react'
import { Save, Loader2, Package } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useApiGet } from '@/hooks/useApi'
import { apiFetch } from '@/lib/api'
import { toast } from '@/components/ui/Toast'

interface SparePartData {
  id: number
  item_name: string
  model_or_drawing: string | null
  quantity: string | null
  created_at?: string
}

interface SparePartFormProps {
  projectId: string
  /** 选中的备件 id；不传则视为新建 */
  sparePartId?: string
}

export default function SparePartForm({ projectId, sparePartId }: SparePartFormProps) {
  const { data: list, isLoading } = useApiGet<SparePartData[]>(
    `/spare-parts/projects/${projectId}/spare-parts`,
    { retry: false }
  )

  const parts = Array.isArray(list) ? list : []
  const current = sparePartId
    ? parts.find((p) => String(p.id) === String(sparePartId))
    : parts[0]

  const [itemName, setItemName] = useState('')
  const [modelOrDrawing, setModelOrDrawing] = useState('')
  const [quantity, setQuantity] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (current) {
      setItemName(current.item_name || '')
      setModelOrDrawing(current.model_or_drawing || '')
      setQuantity(current.quantity || '')
    } else {
      setItemName('')
      setModelOrDrawing('')
      setQuantity('')
    }
  }, [current])

  const handleSave = async () => {
    if (!itemName.trim()) {
      toast.error({ title: '请输入品名' })
      return
    }
    setIsSaving(true)
    const payload = {
      item_name: itemName.trim(),
      model_or_drawing: modelOrDrawing.trim() || null,
      quantity: quantity.trim() || null,
    }
    try {
      if (current) {
        await apiFetch<SparePartData>(
          `/spare-parts/projects/${projectId}/spare-parts/${current.id}`,
          { method: 'PATCH', body: payload }
        )
        toast.success({ title: '已更新备件信息' })
      } else {
        await apiFetch<SparePartData>(`/spare-parts/projects/${projectId}/spare-parts`, {
          method: 'POST',
          body: payload,
        })
        toast.success({ title: '已创建备件' })
      }
    } catch {
      toast.error({ title: '保存失败' })
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Package className="h-4 w-4" />
          备件信息
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <p className="text-muted-foreground text-sm">加载中...</p>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">品名 *</label>
                <Input
                  placeholder="如:主机连杆"
                  value={itemName}
                  onChange={(e) => setItemName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">型号或图号</label>
                <Input
                  placeholder="如:MC-700-001"
                  value={modelOrDrawing}
                  onChange={(e) => setModelOrDrawing(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">数量</label>
                <Input
                  type="number"
                  placeholder="0"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                />
              </div>
            </div>
            {current?.created_at && (
              <p className="text-xs text-muted-foreground">
                已保存 · 创建时间: {new Date(current.created_at).toLocaleString()}
              </p>
            )}
            <div className="flex justify-end">
              <Button onClick={handleSave} disabled={isSaving}>
                {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                {current ? '更新' : '创建'}
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
