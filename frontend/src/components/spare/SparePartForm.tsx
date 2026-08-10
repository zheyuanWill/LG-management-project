import { useState, useEffect } from 'react'
import { Save, Loader2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select, type SelectOption } from '@/components/ui/Select'
import { useApiGet, useApiPatch } from '@/hooks/useApi'

const customerOptions: SelectOption[] = [
  { value: '', label: '请选择船东...' },
  { value: 'customer_1', label: '中远海运' },
  { value: 'customer_2', label: '马士基' },
  { value: 'customer_3', label: '地中海航运' },
  { value: 'customer_4', label: '长荣海运' },
]

interface SparePartData {
  name: string
  part_no: string
  quantity: number
  unit: string
  customer_id: string
}

interface SparePartFormProps {
  projectId: string
}

export default function SparePartForm({ projectId }: SparePartFormProps) {
  const { data: sparePart, isLoading } = useApiGet<SparePartData>(
    `/projects/${projectId}/spare-part`
  )
  const patchSparePart = useApiPatch<SparePartData>(`/projects/${projectId}/spare-part`)

  const [name, setName] = useState('')
  const [partNo, setPartNo] = useState('')
  const [quantity, setQuantity] = useState('')
  const [unit, setUnit] = useState('件')
  const [customerId, setCustomerId] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (sparePart) {
      setName(sparePart.name || '')
      setPartNo(sparePart.part_no || '')
      setQuantity(sparePart.quantity?.toString() || '')
      setUnit(sparePart.unit || '件')
      setCustomerId(sparePart.customer_id || '')
    }
  }, [sparePart])

  const handleSave = async () => {
    setIsSaving(true)
    try {
      await patchSparePart.mutateAsync({
        name,
        part_no: partNo,
        quantity: quantity ? parseFloat(quantity) : 0,
        unit,
        customer_id: customerId,
      })
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
                <label className="text-sm font-medium">品名</label>
                <Input
                  placeholder="如:主机连杆"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">型号或图号</label>
                <Input
                  placeholder="如:MC-700-001"
                  value={partNo}
                  onChange={(e) => setPartNo(e.target.value)}
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
              <div className="space-y-2">
                <label className="text-sm font-medium">单位</label>
                <Input
                  placeholder="件/套/个"
                  value={unit}
                  onChange={(e) => setUnit(e.target.value)}
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <label className="text-sm font-medium">船东</label>
                <Select
                  value={customerId}
                  onChange={(e) => setCustomerId(e.target.value)}
                  options={customerOptions}
                />
              </div>
            </div>
            <div className="flex justify-end">
              <Button onClick={handleSave} disabled={isSaving}>
                {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                保存
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}