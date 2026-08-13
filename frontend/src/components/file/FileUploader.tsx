import { useState } from 'react'
import { Upload, X, FileText, Loader2, CheckCircle } from 'lucide-react'
import { Dialog } from '@/components/ui/Dialog'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'
import { useApiGet, useApiPost } from '@/hooks/useApi'

interface FileUploaderProps {
  onClose: () => void
}

const typeLabels: Record<string, string> = {
  contract: '合同',
  receipt: '签收单',
  wechat_screenshot: '微信截图',
  survey: '调研报告',
  certificate: '证书',
  other: '其他',
}

export default function FileUploader({ onClose }: FileUploaderProps) {
  const { data: projects } = useApiGet<{ id: string; project_no: string }[]>('/projects')
  const uploadMutation = useApiPost<{ id: string }>('/files')

  const [selectedProject, setSelectedProject] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({})

  const projectOptions = [
    { value: '', label: '请选择项目...' },
    ...(projects || []).map((p) => ({
      value: p.id,
      label: p.project_no,
    })),
  ]

  const detectFileType = (file: File): string => {
    const name = file.name.toLowerCase()
    if (name.match(/contract|合同|moa/)) return 'contract'
    if (name.match(/receipt|签收|signed/)) return 'receipt'
    if (name.match(/wechat|微信|screenshot|截图/)) return 'wechat_screenshot'
    if (name.match(/survey|调研|investigation/)) return 'survey'
    if (name.match(/certificate|cert|证书|资质/)) return 'certificate'
    return 'other'
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files
    if (!selected) return
    setFiles(Array.from(selected))
  }

  const handleRemove = (index: number) => {
    setFiles(files.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    if (files.length === 0 || !selectedProject) return
    setUploading(true)

    const newProgress: Record<string, number> = {}
    files.forEach((f) => {
      newProgress[f.name] = 0
    })
    setUploadProgress(newProgress)

    for (const file of files) {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('project_id', selectedProject)
      formData.append('file_type', detectFileType(file))

      setUploadProgress((prev) => ({ ...prev, [file.name]: 100 }))
      await uploadMutation.mutateAsync(formData as unknown as Record<string, unknown>)
    }

    setUploading(false)
    setFiles([])
    setUploadProgress({})
    onClose()
  }

  return (
    <Dialog open={true} onOpenChange={(open) => !open && onClose()} title="上传文件">
      <div className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">所属项目 *</label>
          <Select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            options={projectOptions}
          />
        </div>

        <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-border p-6 transition-colors hover:border-primary/50 cursor-pointer">
          <Upload className="h-10 w-10 text-muted-foreground opacity-50 mb-3" />
          <p className="font-medium mb-1">选择文件</p>
          <p className="text-sm text-muted-foreground mb-4">支持多文件上传,自动识别类型</p>
          <label className="cursor-pointer">
            <input type="file" multiple className="hidden" onChange={handleFileSelect} />
            <Button variant="outline" asChild>
              <span className="flex items-center gap-2">
                <Upload className="h-4 w-4" />
                选择文件
              </span>
            </Button>
          </label>
        </div>

        {files.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium">已选文件 ({files.length})</p>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {files.map((file, index) => {
                const detectedType = detectFileType(file)
                return (
                  <div
                    key={index}
                    className="flex items-center gap-2 rounded-md border p-2 text-sm"
                  >
                    <FileText className="h-4 w-4 text-primary shrink-0" />
                    <span className="flex-1 truncate">{file.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {typeLabels[detectedType] || '其他'}
                    </span>
                    {uploadProgress[file.name] !== undefined ? (
                      uploadProgress[file.name] === 100 ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                      )
                    ) : (
                      <button
                        className="p-1 rounded hover:bg-muted"
                        onClick={() => handleRemove(index)}
                      >
                        <X className="h-3 w-3 text-muted-foreground" />
                      </button>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}

        <div className="flex justify-end gap-2 mt-4">
          <Button variant="outline" onClick={onClose} disabled={uploading}>
            取消
          </Button>
          <Button
            onClick={handleUpload}
            disabled={uploading || files.length === 0 || !selectedProject}
          >
            {uploading ? '上传中...' : `上传${files.length > 0 ? ` (${files.length})` : ''}`}
          </Button>
        </div>
      </div>
    </Dialog>
  )
}