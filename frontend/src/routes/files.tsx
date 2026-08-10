import { useState, useMemo } from 'react'
import { FolderOpen, Upload, Search } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'
import { useApiGet } from '@/hooks/useApi'
import type { FileItem } from '@/types'
import FileUploader from '@/components/file/FileUploader'
import FileList from '@/components/file/FileList'
import FilePreview from '@/components/file/FilePreview'

const projectOptions = [
  { value: 'all', label: '全部项目' },
]

const typeOptions = [
  { value: 'all', label: '全部类型' },
  { value: 'contract', label: '合同' },
  { value: 'receipt', label: '签收单' },
  { value: 'wechat_screenshot', label: '微信截图' },
  { value: 'survey', label: '调研报告' },
  { value: 'certificate', label: '证书' },
  { value: 'other', label: '其他' },
]

export default function FilesPage() {
  const [projectFilter, setProjectFilter] = useState('all')
  const [typeFilter, setTypeFilter] = useState('all')
  const [showUploader, setShowUploader] = useState(false)
  const [previewFile, setPreviewFile] = useState<FileItem | null>(null)

  const { data: files, isLoading } = useApiGet<FileItem[]>('/files')
  const { data: projects } = useApiGet<{ id: string; project_no: string }[]>('/projects')

  const allProjectOptions = useMemo(() => {
    const dynamicOptions = (projects || []).map((p) => ({
      value: p.id,
      label: p.project_no,
    }))
    return [...projectOptions, ...dynamicOptions]
  }, [projects])

  const filteredFiles = useMemo(() => {
    if (!files) return []
    return files.filter((file) => {
      if (projectFilter !== 'all' && file.project_id !== projectFilter) return false
      if (typeFilter !== 'all' && file.type !== typeFilter) return false
      return true
    })
  }, [files, projectFilter, typeFilter])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <FolderOpen className="h-8 w-8 text-primary" />
            文件中心
          </h1>
          <p className="text-muted-foreground mt-1">集中管理项目相关文件</p>
        </div>
        <Button onClick={() => setShowUploader(true)} size="lg">
          <Upload className="h-5 w-5" />
          上传文件
        </Button>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">项目:</span>
              <Select
                value={projectFilter}
                onChange={(e) => setProjectFilter(e.target.value)}
                options={allProjectOptions}
                className="w-48"
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">类型:</span>
              <Select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                options={typeOptions}
                className="w-40"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <FileList
        files={filteredFiles}
        isLoading={isLoading}
        onPreview={(file) => setPreviewFile(file)}
      />

      {showUploader && (
        <FileUploader onClose={() => setShowUploader(false)} />
      )}

      {previewFile && (
        <FilePreview file={previewFile} onClose={() => setPreviewFile(null)} />
      )}
    </div>
  )
}