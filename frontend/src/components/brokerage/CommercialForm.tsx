import { useState, useEffect } from 'react'
import { Save, Loader2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select, type SelectOption } from '@/components/ui/Select'
import { useApiGet, useApiPatch } from '@/hooks/useApi'
import { formatCurrency } from '@/lib/utils'

const paymentStatusOptions: SelectOption[] = [
  { value: 'pending', label: '未到账' },
  { value: 'received', label: '已到账' },
]

interface CommercialData {
  quote_amount: number | null
  commission_amount: number | null
  payment_status: string
}

interface CommercialFormProps {
  projectId: string
}

export default function CommercialForm({ projectId }: CommercialFormProps) {
  const { data: commercial, isLoading } = useApiGet<CommercialData>(
    `/projects/${projectId}/commercial`
  )
  const patchCommercial = useApiPatch<CommercialData>(`/projects/${projectId}/commercial`)

  const [quoteAmount, setQuoteAmount] = useState('')
  const [commissionAmount, setCommissionAmount] = useState('')
  const [paymentStatus, setPaymentStatus] = useState('pending')
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (commercial) {
      setQuoteAmount(commercial.quote_amount?.toString() || '')
      setCommissionAmount(commercial.commission_amount?.toString() || '')
      setPaymentStatus(commercial.payment_status || 'pending')
    }
  }, [commercial])

  const handleSave = async () => {
    setIsSaving(true)
    try {
      await patchCommercial.mutateAsync({
        quote_amount: quoteAmount ? parseFloat(quoteAmount) : null,
        commission_amount: commissionAmount ? parseFloat(commissionAmount) : null,
        payment_status: paymentStatus,
      })
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>商务结果</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <p className="text-muted-foreground text-sm">加载中...</p>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">报价金额 (USD)</label>
                <Input
                  type="number"
                  placeholder="0.00"
                  value={quoteAmount}
                  onChange={(e) => setQuoteAmount(e.target.value)}
                />
                {quoteAmount && (
                  <p className="text-xs text-muted-foreground">
                    {formatCurrency(parseFloat(quoteAmount))}
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">佣金金额 (USD)</label>
                <Input
                  type="number"
                  placeholder="0.00"
                  value={commissionAmount}
                  onChange={(e) => setCommissionAmount(e.target.value)}
                />
                {commissionAmount && (
                  <p className="text-xs text-muted-foreground">
                    {formatCurrency(parseFloat(commissionAmount))}
                  </p>
                )}
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">到账状态</label>
              <Select
                value={paymentStatus}
                onChange={(e) => setPaymentStatus(e.target.value)}
                options={paymentStatusOptions}
              />
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