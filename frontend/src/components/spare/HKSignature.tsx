import { useState, useEffect } from 'react'
import { Upload, Calendar, Save, Loader2, FileText, CheckCircle2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useApiGet, useApiPost, useApiPatch } from '@/hooks/useApi'
import { formatDate } from '@/lib/utils'
import apiClient from '@/lib/api'

interface SignatureData {
  id: number
  project_id: number
  signature_file_key: string | null
  signed_at: string | null
  created_at: string
}

interface HKSignatureProps {
  projectId: string
}

export default function HKSignature({ projectId }: HKSignatureProps) {
  const { data: signature, isLoading } = useApiGet<SignatureData>(
    `/projects/${projectId}/hk-signatures`,
    { retry: false }
  )
  const exists = !!signature
  const postMutation = useApiPost<SignatureData>(`/projects/${projectId}/hk-signatures`)
  const patchMutation = useApiPatch<SignatureData>(`/projects/${projectId}/hk-signatures`)

  const [signDate, setSignDate] = useState('')
  const [fileKey, setFileKey] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (signature) {
      setSignDate(signature.signed_at || '')
      setFileKey(signature.signature_file_key || null)
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
      formData.append('project_id', projectId)
      const res = await apiClient.post<{ storage_key: string }>('/files/upload', formData)
      setFileKey(res.data.storage_key)
    } finally {
      setIsUploading(false)
      e.target.value = ''
    }
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      const payload: { signature_file_key?: string; signed_at?: string } = {}
      if (fileKey) payload.signature_file_key = fileKey
      payload.signed_at = signDate || new Date().toISOString().split('T')[0]
      if (exists) {
        await patchMutation.mutateAsync(payload)
      } else {
        await postMutation.mutateAsync(payload)
      }
    } finally {
      setIsSaving(false)
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
                  <Button variant="outline">
                    <Upload className="h-4 w-4" />
                    {isUploading ? '上传中...' : '上传签收单'}
                  </Button>
                </label>
                {fileKey && (
                  <p className="text-xs text-muted-foreground break-all font-mono">
                    已选择文件: {fileKey}
                  </p>
                )}
              </div>
            </div>

            {signature?.signature_file_key && (
              <div className="rounded-lg border p-4 space-y-2">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <span className="font-medium text-sm">签收单已上传</span>
                </div>
                <p className="text-xs text-muted-foreground break-all font-mono">
                  存储键: {signature.signature_file_key}
                </p>
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
                {exists ? '更新' : '保存'}
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
