import { useState } from 'react'
import { Upload, FileText, CheckCircle, Loader2, Download } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { useApiPatch, useApiPost } from '@/hooks/useApi'
import { toast } from '@/components/ui/Toast'
import apiClient from '@/lib/api'
import type { Project, ProjectCompletionFile } from '@/types'

interface ProjectCompletionProps {
  project: Project
  onStatusChange?: () => void
}

interface UploadedFile {
  id: number
  file_name: string
}

export default function ProjectCompletion({
  project,
  onStatusChange,
}: ProjectCompletionProps) {
  const [completionFiles, setCompletionFiles] = useState<ProjectCompletionFile[]>(
    () => project.completion_files ?? []
  )
  const [acceptanceFiles, setAcceptanceFiles] = useState<ProjectCompletionFile[]>(
    () => project.acceptance_files ?? []
  )
  const [isUploading, setIsUploading] = useState(false)

  const updateProject = useApiPatch<Project>(`/projects/${project.id}`)
  const uploadMutation = useApiPost<UploadedFile>('/files/upload')

  const persist = async (comp: ProjectCompletionFile[], acc: ProjectCompletionFile[]) => {
    try {
      await updateProject.mutateAsync({ completion_files: comp, acceptance_files: acc })
    } catch {
      toast.error({ title: '保存失败', description: '文件已上传但未能持久化，请刷新页面重试' })
    }
  }

  const handleFileUpload = async (
    e: React.ChangeEvent<HTMLInputElement>,
    type: 'completion' | 'acceptance'
  ) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    setIsUploading(true)
    try {
      const uploaded: ProjectCompletionFile[] = []
      for (const file of Array.from(files)) {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('project_id', String(project.id))
        const res = await uploadMutation.mutateAsync(
          formData as unknown as Record<string, unknown>
        )
        uploaded.push({
          id: String(res.id),
          type,
          name: res.file_name || file.name,
          url: '',
          uploaded_at: new Date().toISOString(),
        })
      }

      let nextComp = completionFiles
      let nextAcc = acceptanceFiles
      if (type === 'completion') {
        nextComp = [...completionFiles, ...uploaded]
        setCompletionFiles(nextComp)
      } else {
        nextAcc = [...acceptanceFiles, ...uploaded]
        setAcceptanceFiles(nextAcc)
      }
      await persist(nextComp, nextAcc)
      toast.success({ title: '文件上传成功' })
    } catch {
      toast.error({ title: '上传失败' })
    } finally {
      setIsUploading(false)
      e.target.value = ''
    }
  }

  const handleRemoveFile = (fileId: string, type: 'completion' | 'acceptance') => {
    if (type === 'completion') {
      const next = completionFiles.filter((f) => f.id !== fileId)
      setCompletionFiles(next)
      void persist(next, acceptanceFiles)
    } else {
      const next = acceptanceFiles.filter((f) => f.id !== fileId)
      setAcceptanceFiles(next)
      void persist(completionFiles, next)
    }
  }

  const handleDownload = async (fileId: string) => {
    try {
      const resp = await apiClient.get(`/files/${fileId}/download`)
      const url = resp.data?.download_url
      if (url) {
        window.open(url, '_blank')
      } else {
        toast.error({ title: '下载链接获取失败' })
      }
    } catch {
      toast.error({ title: '下载失败' })
    }
  }

  const handleMarkComplete = async () => {
    if (completionFiles.length === 0) {
      toast.warning({ title: '请先上传完工确认单' })
      return
    }
    if (!confirm('确定将项目状态变更为"已完成"吗？此操作不可撤销。')) return

    try {
      await updateProject.mutateAsync({ status: 'completed' })
      toast.success({ title: '项目已标记为完成' })
      onStatusChange?.()
    } catch {
      toast.error({ title: '操作失败', description: '请稍后重试' })
    }
  }

  const renderFileList = (files: ProjectCompletionFile[], type: 'completion' | 'acceptance') => (
    <div className="space-y-2">
      <h4 className="text-sm font-medium">已上传文件</h4>
      <div className="space-y-2">
        {files.map((file) => (
          <div
            key={file.id}
            className="flex items-center justify-between rounded-md border border-border px-3 py-2"
          >
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-primary" />
              <span className="text-sm">{file.name}</span>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => handleDownload(file.id)}
                className="inline-flex items-center gap-1 text-xs text-primary hover:underline transition-colors"
              >
                <Download className="h-3.5 w-3.5" />
                下载
              </button>
              <button
                onClick={() => handleRemoveFile(file.id, type)}
                className="text-xs text-muted-foreground hover:text-destructive transition-colors"
              >
                删除
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            完工确认单
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-lg border-2 border-dashed border-border p-6 text-center hover:border-primary/50 transition-colors">
            <input
              type="file"
              accept="application/pdf,image/*"
              multiple
              className="hidden"
              onChange={(e) => handleFileUpload(e, 'completion')}
              id="completion-upload"
              disabled={isUploading}
            />
            <label
              htmlFor="completion-upload"
              className="cursor-pointer inline-flex flex-col items-center gap-2 text-muted-foreground hover:text-primary transition-colors"
            >
              <Upload className="h-10 w-10" />
              <span className="text-sm">{isUploading ? '上传中...' : '点击上传完工确认单'}</span>
              <span className="text-xs text-muted-foreground">支持 PDF、图片格式</span>
            </label>
          </div>

          {completionFiles.length > 0 && renderFileList(completionFiles, 'completion')}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            验收单
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-lg border-2 border-dashed border-border p-6 text-center hover:border-primary/50 transition-colors">
            <input
              type="file"
              accept="application/pdf,image/*"
              multiple
              className="hidden"
              onChange={(e) => handleFileUpload(e, 'acceptance')}
              id="acceptance-upload"
              disabled={isUploading}
            />
            <label
              htmlFor="acceptance-upload"
              className="cursor-pointer inline-flex flex-col items-center gap-2 text-muted-foreground hover:text-primary transition-colors"
            >
              <Upload className="h-10 w-10" />
              <span className="text-sm">{isUploading ? '上传中...' : '点击上传验收单'}</span>
              <span className="text-xs text-muted-foreground">支持 PDF、图片格式</span>
            </label>
          </div>

          {acceptanceFiles.length > 0 && renderFileList(acceptanceFiles, 'acceptance')}
        </CardContent>
      </Card>

      {project.status !== 'completed' && (
        <Card className="border-primary/30 bg-primary/5">
          <CardContent className="p-6 flex items-center justify-between">
            <div className="space-y-1">
              <h4 className="font-semibold">完成项目</h4>
              <p className="text-sm text-muted-foreground">
                上传完工确认单后，可将项目状态变更为"已完成"
              </p>
            </div>
            <Button
              onClick={handleMarkComplete}
              disabled={completionFiles.length === 0 || updateProject.isPending}
              className="bg-secondary hover:bg-secondary/90"
            >
              {updateProject.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  处理中
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4" />
                  标记为已完成
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      )}

      {project.status === 'completed' && (
        <Card className="border-secondary/30 bg-secondary/5">
          <CardContent className="p-6 flex items-center gap-3">
            <CheckCircle className="h-6 w-6 text-secondary" />
            <div>
              <h4 className="font-semibold text-secondary">项目已完成</h4>
              <p className="text-sm text-muted-foreground">
                该监修项目已标记为完成状态
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
