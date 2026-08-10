import { useState } from 'react'
import { Save, X } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

interface ReportEditorProps {
  title?: string
  fields: {
    name: string
    label: string
    value: string
    placeholder?: string
  }[]
  onSave: (values: Record<string, string>) => void
  onConfirm?: () => void
  showConfirm?: boolean
}

export default function ReportEditor({
  title,
  fields,
  onSave,
  onConfirm,
  showConfirm = false,
}: ReportEditorProps) {
  const [values, setValues] = useState<Record<string, string>>(() => {
    const initial: Record<string, string> = {}
    fields.forEach((f) => {
      initial[f.name] = f.value
    })
    return initial
  })
  const [isEditing, setIsEditing] = useState(false)

  const handleChange = (name: string, value: string) => {
    setValues((prev) => ({ ...prev, [name]: value }))
  }

  const handleSave = () => {
    onSave(values)
    setIsEditing(false)
  }

  const handleCancel = () => {
    const initial: Record<string, string> = {}
    fields.forEach((f) => {
      initial[f.name] = f.value
    })
    setValues(initial)
    setIsEditing(false)
  }

  return (
    <div className="space-y-4">
      {title && <h4 className="text-sm font-semibold">{title}</h4>}

      {!isEditing ? (
        <div className="space-y-3">
          {fields.map((field) => (
            <div key={field.name} className="space-y-1">
              <label className="text-xs font-medium text-muted-foreground">
                {field.label}
              </label>
              <p className="text-sm whitespace-pre-wrap leading-relaxed">
                {values[field.name] || (
                  <span className="text-muted-foreground italic">暂无内容</span>
                )}
              </p>
            </div>
          ))}
          <div className="flex gap-2 pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsEditing(true)}
            >
              编辑
            </Button>
            {showConfirm && onConfirm && (
              <Button size="sm" onClick={onConfirm}>
                确认提交
              </Button>
            )}
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {fields.map((field) => (
            <div key={field.name} className="space-y-1">
              <label className="text-xs font-medium text-muted-foreground">
                {field.label}
              </label>
              <textarea
                value={values[field.name]}
                onChange={(e) => handleChange(field.name, e.target.value)}
                placeholder={field.placeholder}
                rows={3}
                className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-none"
              />
            </div>
          ))}
          <div className="flex gap-2 pt-2">
            <Button size="sm" onClick={handleSave}>
              <Save className="h-4 w-4" />
              保存
            </Button>
            <Button variant="ghost" size="sm" onClick={handleCancel}>
              <X className="h-4 w-4" />
              取消
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}