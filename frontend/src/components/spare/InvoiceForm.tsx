import { useState, useEffect } from 'react'
import { Save, Loader2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useApiGet, useApiPatch } from '@/hooks/useApi'

interface InvoiceData {
  title: string
  tax_no: string
  amount: number | null
  purpose: string
}

interface InvoiceFormProps {
  projectId: string
}

const purposeOptions = [
  { value: 'export_tax_refund', label: '用于出口退税' },
  { value: 'domestic', label: '国内结算' },
  { value: 'other', label: '其他' },
]

export default function InvoiceForm({ projectId }: InvoiceFormProps) {
  const { data: invoice, isLoading } = useApiGet<InvoiceData>(
    `/projects/${projectId}/invoice`
  )
  const patchInvoice = useApiPatch<InvoiceData>(`/projects/${projectId}/invoice`)

  const [title, setTitle] = useState('')
  const [taxNo, setTaxNo] = useState('')
  const [amount, setAmount] = useState('')
  const [purpose, setPurpose] = useState('export_tax_refund')
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (invoice) {
      setTitle(invoice.title || '')
      setTaxNo(invoice.tax_no || '')
      setAmount(invoice.amount?.toString() || '')
      setPurpose(invoice.purpose || 'export_tax_refund')
    }
  }, [invoice])

  const handleSave = async () => {
    setIsSaving(true)
    try {
      await patchInvoice.mutateAsync({
        title,
        tax_no: taxNo,
        amount: amount ? parseFloat(amount) : null,
        purpose,
      })
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>发票信息</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <p className="text-muted-foreground text-sm">加载中...</p>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2 md:col-span-2">
                <label className="text-sm font-medium">抬头</label>
                <Input
                  placeholder="发票抬头"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">税号</label>
                <Input
                  placeholder="纳税人识别号"
                  value={taxNo}
                  onChange={(e) => setTaxNo(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">金额</label>
                <Input
                  type="number"
                  placeholder="0.00"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <label className="text-sm font-medium">用途</label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={purpose}
                  onChange={(e) => setPurpose(e.target.value)}
                >
                  {purposeOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
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