import { useState, useEffect } from 'react'
import { Save, Loader2, Phone } from 'lucide-react'
import { Dialog } from '@/components/ui/Dialog'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useApiPost, useApiPatch } from '@/hooks/useApi'
import type { Customer } from '@/types'

const conclusionOptions: { value: string; label: string }[] = [
  { value: '', label: '请选择调研结论...' },
  { value: 'viable', label: '可承接' },
  { value: 'cautious', label: '谨慎承接' },
  { value: 'not_recommended', label: '暂不承接' },
]

interface CustomerFormProps {
  customer: Customer | null
  onClose: (customer?: Customer) => void
}

export default function CustomerForm({ customer, onClose }: CustomerFormProps) {
  const isEditing = !!customer
  const postCustomer = useApiPost<Customer>('/customers')
  const patchCustomer = useApiPatch<Customer>(`/customers/${customer?.id || ''}`)

  const [name, setName] = useState('')
  const [contactPerson, setContactPerson] = useState('')
  const [phone, setPhone] = useState('')
  const [conclusion, setConclusion] = useState('')
  const [remarks, setRemarks] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (customer) {
      setName(customer.name || '')
      setContactPerson(customer.contact_person || '')
      setPhone(customer.phone || '')
      setConclusion(customer.survey_conclusion || '')
      setRemarks(customer.remarks || '')
    }
  }, [customer])

  const handleSave = async () => {
    if (!name.trim()) {
      alert('请输入客户名称')
      return
    }

    setIsSaving(true)
    try {
      const payload: Record<string, unknown> = {
        name: name.trim(),
        contact_person: contactPerson.trim() || null,
        phone: phone.trim() || null,
        survey_conclusion: conclusion || null,
        remarks: remarks.trim() || null,
      }

      if (isEditing) {
        const updated = await patchCustomer.mutateAsync(payload)
        onClose(updated)
      } else {
        const created = await postCustomer.mutateAsync(payload)
        onClose(created)
      }
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Dialog
      open={true}
      onOpenChange={(open) => !open && onClose()}
      title={isEditing ? '编辑客户' : '新建客户'}
    >
      <div className="space-y-4">
        <div className="grid grid-cols-1 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">客户名称 *</label>
            <Input
              placeholder="请输入客户名称"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">联系人</label>
            <Input
              placeholder="请输入联系人姓名"
              value={contactPerson}
              onChange={(e) => setContactPerson(e.target.value)}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">电话</label>
              <Input
                placeholder="联系电话"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
              {phone && (
                <a
                  href={`tel:${phone}`}
                  className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                >
                  <Phone className="h-3 w-3" />
                  点击拨号 {phone}
                </a>
              )}
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">调研结论</label>
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={conclusion}
                onChange={(e) => setConclusion(e.target.value)}
              >
                {conclusionOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">备注</label>
            <textarea
              className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              placeholder="其他备注信息..."
              value={remarks}
              onChange={(e) => setRemarks(e.target.value)}
            />
          </div>
        </div>

        <div className="flex justify-end gap-2 mt-4">
          <Button variant="outline" onClick={onClose} disabled={isSaving}>
            取消
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            {isEditing ? '保存' : '创建'}
          </Button>
        </div>
      </div>
    </Dialog>
  )
}
