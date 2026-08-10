import { useState, useEffect } from 'react'
import { Upload, Calendar, Save, Loader2, FileText, Trash2, ExternalLink } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useApiGet, useApiPost, useApiPatch, useApiDelete } from '@/hooks/useApi'
import { formatDate } from '@/lib/utils'

interface SignatureData {
  id?: string
  file_url?: string
  file_name?: string
  sign_date?: string
}

interface HKSignatureProps {
  projectId: string
}

export default function HKSignature({ projectId }: HKSignatureProps) {
  const { data: signature, isLoading } = useApiGet<SignatureData>(
    `/projects/${projectId}/hk-signature`
  )
  const uploadMutation = useApiPost<SignatureData>(`/projects/${projectId}/hk-signature`)
  const patchMutation = useApiPatch<SignatureData>(`/projects/${projectId}/hk-signature`)
  const deleteMutation = useApiDelete<void>(`/projects/${projectId}/hk-signature`)

  const [signDate, setSignDate] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (signature) {
      setSignDate(signature.sign_date || '')
    }
  }, [signature])

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    setIsUploading(true)
    try {
      const file = files[0]
      const formData = new FormData()
      formData.append('file', file)
      formData.append('sign_date', signDate || new Date().toISOString().split('T')[0])
      await uploadMutation.mutateAsync(formData as unknown as Record<string, unknown>)
    } finally {
      setIsUploading(false)
      e.target.value = ''
    }
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      await patchMutation.mutateAsync({ sign_date: signDate })
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = () => {
    if (confirm('确定删除签收单?')) {
      deleteMutation.mutate('')
      setSignDate('')
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>香港签收单</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <p className="text-muted-foreground text-sm">加载中...</p>
        ) : (
          <>
            <div className="rounded-lg border-2 border-dashed border-border p-6">
              <div className="text-center space-y-4">
                <FileText className="mx-auto h-10 w-10 text-muted-foreground opacity-50" />
                <div>
                  <p className="font-medium">签收单扫描件</p>
                  <p className="text-sm text-muted-foreground">上传香港签收单扫描件 (PDF/图片)</p>
                </div>
                <label className="inline-block cursor-pointer">
                  <input
                    type="file"
                    accept="image/*,.pdf"
                    className="hidden"
                    onChange={handleFileSelect}
                    disabled={isUploading}
                  />
                  <Button variant="outline" asChild>
                    <span className="flex items-center gap-2">
                      <Upload className="h-4 w-4" />
                      {isUploading ? '上传中...' : '上传签收单'}
                    </span>
                  </Button>
                </label>
              </div>
            </div>

            {signature?.file_url && (
              <div className="rounded-lg border p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-primary" />
                    <span className="font-medium text-sm">{signature.file_name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="ghost" size="sm" asChild>
                      <a href={signature.file_url} target="_blank" rel="noreferrer">
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    </Button>
                    <Button variant="ghost" size="sm" onClick={handleDelete} disabled={deleteMutation.isPending}>
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              </div>
            )}

            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                签收日期
              </label>
              <Input
                type="date"
                value={signDate}
                onChange={(e) => setSignDate(e.target.value)}
              />
              {signDate && (
                <p className="text-xs text-muted-foreground">
                  {formatDate(signDate)}
                </p>
              )}
            </div>

            <div className="flex justify-end">
              <Button onClick={handleSave} disabled={isSaving}>
                {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                保存签收日期
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}