import { useState } from 'react'
import { Upload, FileText, Trash2, Download, ExternalLink } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { useApiGet, useApiPost, useApiDelete } from '@/hooks/useApi'
import type { FileItem } from '@/types'

interface ContractUploadProps {
  projectId: string
}

export default function ContractUpload({ projectId }: ContractUploadProps) {
  const { data: contracts, isLoading } = useApiGet<FileItem[]>(
    `/projects/${projectId}/contracts`
  )
  const uploadMutation = useApiPost<FileItem>(`/projects/${projectId}/contracts`)
  const deleteMutation = useApiDelete<void>(`/projects/${projectId}/contracts`)

  const [isUploading, setIsUploading] = useState(false)

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    setIsUploading(true)
    try {
      for (const file of Array.from(files)) {
        const formData = new FormData()
        formData.append('file', file)
        await uploadMutation.mutateAsync(formData as unknown as Record<string, unknown>)
      }
    } finally {
      setIsUploading(false)
      e.target.value = ''
    }
  }

  const handleDelete = (id: string) => {
    if (confirm('确定删除该合同文件?')) {
      deleteMutation.mutate(id)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>MOA 合同</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="file"
              accept="image/*,.pdf,.doc,.docx"
              multiple
              className="hidden"
              onChange={handleFileSelect}
              disabled={isUploading}
            />
            <Button variant="outline" asChild>
              <span className="flex items-center gap-2">
                <Upload className="h-4 w-4" />
                {isUploading ? '上传中...' : '上传合同扫描件'}
              </span>
            </Button>
          </label>
        </div>

        {isLoading ? (
          <p className="text-muted-foreground text-sm">加载中...</p>
        ) : !contracts || contracts.length === 0 ? (
          <div className="py-8 text-center text-muted-foreground">
            <FileText className="mx-auto h-10 w-10 opacity-50 mb-2" />
            <p className="text-sm">暂无合同文件,请上传 MOA 合同扫描件</p>
          </div>
        ) : (
          <div className="space-y-2">
            {contracts.map((contract) => (
              <div
                key={contract.id}
                className="flex items-center justify-between rounded-lg border border-border p-3"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="rounded-lg bg-primary/10 p-2 shrink-0">
                    <FileText className="h-4 w-4 text-primary" />
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium truncate">{contract.name}</p>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
                      <Badge variant="secondary">{contract.type}</Badge>
                      <span>{new Date(contract.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <Button variant="ghost" size="sm" asChild>
                    <a href={contract.url} target="_blank" rel="noreferrer">
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </Button>
                  <Button variant="ghost" size="sm" asChild>
                    <a href={contract.url} download>
                      <Download className="h-4 w-4" />
                    </a>
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(contract.id)}
                    disabled={deleteMutation.isPending}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}