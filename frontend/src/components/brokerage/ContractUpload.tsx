import { useState, useRef } from 'react'
import { Upload, FileText, CheckCircle2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { useApiGet, useApiPost } from '@/hooks/useApi'
import { formatDate } from '@/lib/utils'

interface ContractData {
  id: number
  project_id: number
  moa_file_key: string
  created_at: string
}

interface ContractUploadProps {
  projectId: string
}

export default function ContractUpload({ projectId }: ContractUploadProps) {
  const { data: contract, isLoading, isError, error } = useApiGet<ContractData>(
    `/brokerage/projects/${projectId}/contracts`,
    { retry: false }
  )
  const uploadMutation = useApiPost<ContractData>(`/brokerage/projects/${projectId}/contracts`)

  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const notFound = isError && (error as { response?: { status?: number } })?.response?.status === 404

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    setIsUploading(true)
    try {
      const file = files[0]
      const formData = new FormData()
      formData.append('file', file)
      await uploadMutation.mutateAsync(formData as unknown as Record<string, unknown>)
    } finally {
      setIsUploading(false)
      e.target.value = ''
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>MOA 合同</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-4">
          <input
            type="file"
            accept="image/*,.pdf,.doc,.docx"
            className="hidden"
            ref={fileInputRef}
            onChange={handleFileSelect}
            disabled={isUploading || !!contract}
          />
          <Button variant="outline" onClick={() => fileInputRef.current?.click()}>
            <Upload className="h-4 w-4" />
            {isUploading ? '上传中...' : contract ? '已上传' : '上传合同扫描件'}
          </Button>
        </div>

        {isLoading ? (
          <p className="text-muted-foreground text-sm">加载中...</p>
        ) : contract ? (
          <div className="rounded-lg border border-border p-4 space-y-3">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              <span className="font-medium text-sm">MOA 合同已上传</span>
            </div>
            <div className="text-xs text-muted-foreground space-y-1">
              <p>
                存储键:{' '}
                <span className="font-mono break-all">{contract.moa_file_key}</span>
              </p>
              <p>上传时间: {formatDate(contract.created_at)}</p>
            </div>
          </div>
        ) : notFound ? (
          <div className="py-8 text-center text-muted-foreground">
            <FileText className="mx-auto h-10 w-10 opacity-50 mb-2" />
            <p className="text-sm">暂无合同文件,请上传 MOA 合同扫描件</p>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}
