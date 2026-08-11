import { Eye, Download, Trash2, FileText } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { useApiDelete } from '@/hooks/useApi'
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

  const handleDelete = (id: string) => {
    if (confirm('确定删除该文件?')) {
      deleteMutation.mutate(id)
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
                  <span className="font-medium truncate max-w-[200px]">{file.name}</span>
                </div>
              </TableCell>
              <TableCell>
                <FileTypeBadge type={file.type} />
              </TableCell>
              <TableCell>
                <span className="text-sm text-muted-foreground">{file.project_id || '-'}</span>
              </TableCell>
              <TableCell>{formatDateTime(file.created_at)}</TableCell>
              <TableCell className="text-right">
                <div className="flex items-center justify-end gap-1">
                  <Button variant="ghost" size="sm" onClick={() => onPreview(file)}>
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="sm" asChild>
                    <a href={file.url} download>
                      <Download className="h-4 w-4" />
                    </a>
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(file.id)}
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