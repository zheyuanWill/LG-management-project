import { useState, useRef } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, FileText, CheckCircle2, Download, Eye, FileSpreadsheet } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { useApiGet, useApiPost } from '@/hooks/useApi'
import apiClient from '@/lib/api'
import { formatDate } from '@/lib/utils'
import DeleteConfirm from '@/components/common/DeleteConfirm'

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
  const queryClient = useQueryClient()
  const { data: contract, isLoading, isError, error, refetch } = useApiGet<ContractData>(
    `/brokerage/projects/${projectId}/contracts`,
    { retry: false }
  )
  const uploadMutation = useApiPost<ContractData>(`/brokerage/projects/${projectId}/contracts`)
  // 合同是「每项目单条」资源，后端 DELETE 仅以 project_id 定位，
  // 用自定义 mutation 删除精确 URL（不追加 id，避免双重 project_id）。
  const deleteMutation = useMutation<void, unknown, string | undefined>({
    mutationFn: () => apiClient.delete(`/brokerage/projects/${projectId}/contracts`),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: [`/brokerage/projects/${projectId}/contracts`] }),
  })

  const [isUploading, setIsUploading] = useState(false)
  const [fileUrl, setFileUrl] = useState<string>('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const notFound = isError && (error as { response?: { status?: number } })?.response?.status === 404

  const loadFileUrl = async (storageKey: string) => {
    try {
      const resp = await apiClient.post('/files/url', { storage_key: storageKey })
      setFileUrl(resp.data.download_url)
    } catch {
      setFileUrl('')
    }
  }

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    setIsUploading(true)
    try {
      const file = files[0]
      const formData = new FormData()
      formData.append('file', file)
      await uploadMutation.mutateAsync(formData as unknown as Record<string, unknown>)
      refetch()
    } finally {
      setIsUploading(false)
      e.target.value = ''
    }
  }

  const isImage = /\.(png|jpe?g|gif|bmp|webp)$/i.test(contract?.moa_file_key || '')
  const isPdf = /\.pdf$/i.test(contract?.moa_file_key || '')

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>MOA 合同</CardTitle>
        {contract && (
          <DeleteConfirm
            resourceName="合同"
            triggerVariant="button"
            description="将删除已上传的 MOA 合同文件，此操作不可撤销。"
            mutation={deleteMutation}
            id={String(projectId)}
            onDeleted={() => {
              queryClient.invalidateQueries({ queryKey: [`/brokerage/projects/${projectId}/contracts`] })
            }}
          />
        )}
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
            {isUploading ? '上传中...' : contract ? '重新上传' : '上传合同扫描件'}
          </Button>

          {contract && (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={async () => {
                  await loadFileUrl(contract.moa_file_key)
                  if (fileUrl) window.open(fileUrl, '_blank')
                }}
              >
                <Download className="h-4 w-4" />
                下载
              </Button>
              {isImage || isPdf ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={async () => {
                    await loadFileUrl(contract.moa_file_key)
                    if (fileUrl) window.open(fileUrl, '_blank')
                  }}
                >
                  <Eye className="h-4 w-4" />
                  预览
                </Button>
              ) : null}
            </div>
          )}
        </div>

        {isLoading ? (
          <p className="text-muted-foreground text-sm">加载中...</p>
        ) : contract ? (
          <div className="rounded-lg border border-border p-4 space-y-3">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              <span className="font-medium text-sm">MOA 合同已上传</span>
            </div>
            {isImage && fileUrl ? (
              <img
                src={fileUrl}
                alt="MOA 合同"
                className="max-h-64 rounded border object-contain"
              />
            ) : null}
            <div className="text-xs text-muted-foreground space-y-1">
              <p>
                文件名:{' '}
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
