import { useState, useEffect } from 'react'
import { Save, Loader2 } from 'lucide-react'
import { Dialog } from '@/components/ui/Dialog'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useApiPost, useApiPatch } from '@/hooks/useApi'
import type { Customer } from '@/types'

interface CustomerFormProps {
  customer: Customer | null
  onClose: () => void
}

export default function CustomerForm({ customer, onClose }: CustomerFormProps) {
  const isEditing = !!customer
  const postCustomer = useApiPost<Customer>('/customers')
  const patchCustomer = useApiPatch<Customer>(`/customers/${customer?.id || ''}`)

  const [name, setName] = useState('')
  const [contactPerson, setContactPerson] = useState('')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [conclusion, setConclusion] = useState('')
  const [notes, setNotes] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (customer) {
      setName(customer.name || '')
      setContactPerson(customer.contact_person || '')
      setPhone(customer.phone || '')
      setEmail(customer.email || '')
      setNotes(customer.notes || '')
      if (customer.notes?.includes('可承接')) setConclusion('可承接')
      else if (customer.notes?.includes('谨慎')) setConclusion('谨慎承接')
      else if (customer.notes?.includes('暂不')) setConclusion('暂不承接')
      else setConclusion('')
    }
  }, [customer])

  const handleSave = async () => {
    if (!name.trim()) {
      alert('请输入客户名称')
      return
    }

    setIsSaving(true)
    try {
      const notesWithConclusion = conclusion
        ? `${conclusion}${notes ? ' | ' + notes : ''}`
        : notes

      const payload = {
        name: name.trim(),
        contact_person: contactPerson.trim(),
        phone: phone.trim(),
        email: email.trim(),
        notes: notesWithConclusion,
      }

      if (isEditing) {
        await patchCustomer.mutateAsync(payload)
      } else {
        await postCustomer.mutateAsync(payload)
      }
      onClose()
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
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">邮箱</label>
              <Input
                type="email"
                placeholder="邮箱地址"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">背景调研结论</label>
            <select
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={conclusion}
              onChange={(e) => setConclusion(e.target.value)}
            >
              <option value="">请选择调研结论...</option>
              <option value="可承接">可承接</option>
              <option value="谨慎承接">谨慎承接</option>
              <option value="暂不承接">暂不承接</option>
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">备注</label>
            <textarea
              className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              placeholder="其他备注信息..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
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