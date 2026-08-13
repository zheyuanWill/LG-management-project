import { useState } from 'react'
import { Eye, Download, Trash2, FileText, DownloadCloud } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { useApiDelete } from '@/hooks/useApi'
import apiClient from '@/lib/api'
import type { FileItem } from '@/types'
import FileTypeBadge from './FileTypeBadge'
import { formatDateTime } from '@/lib/utils'

interface FileListProps {
  files: FileItem[]
  isLoading: boolean
  projectFilter?: string
  typeFilter?: string
  onPreview: (file: FileItem) => void
}

export default function FileList({
  files,
  isLoading,
  onPreview,
}: FileListProps) {
  const deleteMutation = useApiDelete<void>('/files')
  const [batchDownloading, setBatchDownloading] = useState(false)

  const handleDelete = (id: string) => {
    if (confirm('确定删除该文件?')) {
      deleteMutation.mutate(id)
    }
  }

  const getDownloadUrl = async (file: FileItem): Promise<string> => {
    if (file.download_url) return file.download_url
    const resp = await apiClient.post('/files/url', { storage_key: file.storage_key })
    return resp.data.download_url
  }

  const handleDownload = async (file: FileItem) => {
    try {
      const url = await getDownloadUrl(file)
      const a = document.createElement('a')
      a.href = url
      a.download = file.name || file.file_name || 'download'
      a.click()
    } catch {
      alert('下载失败，文件可能已失效')
    }
  }

  const handleBatchDownload = async () => {
    setBatchDownloading(true)
    try {
      for (const file of files) {
        try {
          const url = await getDownloadUrl(file)
          const a = document.createElement('a')
          a.href = url
          a.download = file.name || file.file_name || `file_${file.id}`
          a.click()
          await new Promise((r) => setTimeout(r, 500)) // 避免浏览器拦截批量下载
        } catch {
          // 单个失败继续
        }
      }
    } finally {
      setBatchDownloading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="py-16 text-center text-muted-foreground">
        <p>加载中...</p>
      </div>
    )
  }

  if (!files || files.length === 0) {
    return (
      <Card>
        <div className="py-16 text-center text-muted-foreground">
          <FileText className="mx-auto h-12 w-12 opacity-50 mb-3" />
          <p className="text-lg">暂无文件</p>
          <p className="text-sm mt-1">点击"上传文件"添加文件</p>
        </div>
      </Card>
    )
  }

  return (
    <Card>
      <div className="flex justify-end p-3 border-b border-border">
        <Button
          variant="outline"
          size="sm"
          onClick={handleBatchDownload}
          disabled={batchDownloading}
        >
          <DownloadCloud className="h-4 w-4" />
          {batchDownloading ? '下载中...' : `批量下载 (${files.length})`}
        </Button>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>文件名</TableHead>
            <TableHead>类型</TableHead>
            <TableHead>所属项目</TableHead>
            <TableHead>上传时间</TableHead>
            <TableHead className="text-right">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {files.map((file) => (
            <TableRow key={file.id}>
              <TableCell>
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-primary shrink-0" />
                  <span className="font-medium truncate max-w-[200px]">
                    {file.name || file.file_name}
                  </span>
                </div>
              </TableCell>
              <TableCell>
                <FileTypeBadge type={file.type || file.file_type} />
              </TableCell>
              <TableCell>
                <span className="text-sm text-muted-foreground">
                  {file.project_ship_name || file.project_id || '-'}
                </span>
              </TableCell>
              <TableCell>{formatDateTime(file.created_at)}</TableCell>
              <TableCell className="text-right">
                <div className="flex items-center justify-end gap-1">
                  <Button variant="ghost" size="sm" onClick={() => onPreview(file)}>
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => handleDownload(file)}>
                    <Download className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(String(file.id))}
                    disabled={deleteMutation.isPending}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Card>
  )
}