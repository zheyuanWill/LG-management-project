import { useState, useRef } from 'react'
import { Upload, X, FileText, CheckCircle, Loader2 } from 'lucide-react'
import { Dialog } from '@/components/ui/Dialog'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'
import { useApiPost } from '@/hooks/useApi'

interface DocUploaderProps {
  onClose: () => void
}

const categoryOptions = [
  { value: 'QM', label: 'QM - 质量管理' },
  { value: 'SUP', label: 'SUP - 监修' },
  { value: 'REP', label: 'REP - 报告' },
  { value: 'BRO', label: 'BRO - 经纪' },
  { value: 'SPL', label: 'SPL - 备件' },
  { value: 'SPEC', label: 'SPEC - 规格书' },
]

export default function DocUploader({ onClose }: DocUploaderProps) {
  const uploadMutation = useApiPost<{ id: string }>('/knowledge/documents')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [files, setFiles] = useState<File[]>([])
  const [category, setCategory] = useState('QM')
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({})

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files
    if (!selected) return
    setFiles(Array.from(selected))
  }

  const handleRemove = (index: number) => {
    setFiles(files.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    if (files.length === 0) return
    setUploading(true)

    const newProgress: Record<string, number> = {}
    files.forEach((f) => {
      newProgress[f.name] = 0
    })
    setUploadProgress(newProgress)

    for (const file of files) {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('category', category)

      setUploadProgress((prev) => ({ ...prev, [file.name]: 100 }))
      await uploadMutation.mutateAsync(formData as unknown as Record<string, unknown>)
    }

    setUploading(false)
    setFiles([])
    setUploadProgress({})
    onClose()
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const dropped = e.dataTransfer.files
    if (dropped) {
      setFiles(Array.from(dropped))
    }
  }

  return (
    <Dialog open={true} onOpenChange={(open) => !open && onClose()} title="上传文档到知识库">
      <div className="space-y-4">
        <div
          className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-border p-8 transition-colors hover:border-primary/50 cursor-pointer"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
        >
          <Upload className="h-10 w-10 text-muted-foreground opacity-50 mb-3" />
          <p className="font-medium mb-1">拖拽文件到此处上传</p>
          <p className="text-sm text-muted-foreground mb-4">支持 PDF、Word 文档</p>
          <input
            type="file"
            accept=".pdf,.doc,.docx"
            multiple
            className="hidden"
            ref={fileInputRef}
            onChange={handleFileSelect}
          />
          <Button variant="outline" onClick={() => fileInputRef.current?.click()}>
            <span className="flex items-center gap-2">
              <Upload className="h-4 w-4" />
              选择文件
            </span>
          </Button>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">分类</label>
          <Select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            options={categoryOptions}
          />
        </div>

        {files.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium">已选文件 ({files.length})</p>
            <div className="space-y-1">
              {files.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center gap-2 rounded-md border p-2 text-sm"
                >
                  <FileText className="h-4 w-4 text-primary shrink-0" />
                  <span className="flex-1 truncate">{file.name}</span>
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
              ))}
            </div>
          </div>
        )}

        <div className="flex justify-end gap-2 mt-4">
          <Button variant="outline" onClick={onClose} disabled={uploading}>
            取消
          </Button>
          <Button onClick={handleUpload} disabled={uploading || files.length === 0}>
            {uploading ? '上传中...' : `上传 ${files.length > 0 ? `(${files.length})` : ''}`}
          </Button>
        </div>
      </div>
    </Dialog>
  )
}