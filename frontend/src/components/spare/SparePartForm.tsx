import { useState, useEffect } from 'react'
import { Save, Loader2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useApiGet, useApiPost, useApiPatch } from '@/hooks/useApi'

interface SparePartData {
  id?: number
  item_name: string
  model_or_drawing: string | null
  quantity: string | null
  created_at?: string
}

interface SparePartFormProps {
  projectId: string
}

export default function SparePartForm({ projectId }: SparePartFormProps) {
  const { data: sparePart, isLoading } = useApiGet<SparePartData>(
    `/projects/${projectId}/spare-parts`,
    { retry: false }
  )
  const exists = !!sparePart
  const postSparePart = useApiPost<SparePartData>(`/projects/${projectId}/spare-parts`)
  const patchSparePart = useApiPatch<SparePartData>(`/projects/${projectId}/spare-parts`)

  const [itemName, setItemName] = useState('')
  const [modelOrDrawing, setModelOrDrawing] = useState('')
  const [quantity, setQuantity] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (sparePart) {
      setItemName(sparePart.item_name || '')
      setModelOrDrawing(sparePart.model_or_drawing || '')
      setQuantity(sparePart.quantity || '')
    }
  }, [sparePart])

  const handleSave = async () => {
    if (!itemName.trim()) {
      alert('请输入品名')
      return
    }
    setIsSaving(true)
    try {
      const payload = {
        item_name: itemName.trim(),
        model_or_drawing: modelOrDrawing.trim() || null,
        quantity: quantity.trim() || null,
      }
      if (exists) {
        await patchSparePart.mutateAsync(payload)
      } else {
        await postSparePart.mutateAsync(payload)
      }
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>备件信息</CardTitle>
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
            {exists && sparePart?.created_at && (
              <p className="text-xs text-muted-foreground">
                已保存 · 创建时间: {new Date(sparePart.created_at).toLocaleString()}
              </p>
            )}
            <div className="flex justify-end">
              <Button onClick={handleSave} disabled={isSaving}>
                {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                {exists ? '更新' : '创建'}
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
