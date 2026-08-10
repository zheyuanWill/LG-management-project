import { X, Download, ExternalLink, FileText } from 'lucide-react'
import { Dialog } from '@/components/ui/Dialog'
import { Button } from '@/components/ui/Button'
import type { FileItem } from '@/types'

interface FilePreviewProps {
  file: FileItem
  onClose: () => void
}

const imageMimeTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp']

export default function FilePreview({ file, onClose }: FilePreviewProps) {
  const isImage = imageMimeTypes.includes(file.mime_type)
  const isPdf = file.mime_type === 'application/pdf'

  return (
    <Dialog open={true} onOpenChange={(open) => !open && onClose()} title={file.name} className="max-w-4xl">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <FileText className="h-4 w-4" />
            <span>{(file.size / 1024).toFixed(1)} KB</span>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" asChild>
              <a href={file.url} target="_blank" rel="noreferrer">
                <ExternalLink className="h-4 w-4" />
                新窗口打开
              </a>
            </Button>
            <Button size="sm" asChild>
              <a href={file.url} download>
                <Download className="h-4 w-4" />
                下载
              </a>
            </Button>
          </div>
        </div>

        <div className="min-h-[400px] max-h-[600px] rounded-lg border bg-muted/30 overflow-auto flex items-center justify-center">
          {isImage ? (
            <img
              src={file.url}
              alt={file.name}
              className="max-w-full max-h-[600px] object-contain"
            />
          ) : isPdf ? (
            <iframe
              src={file.url}
              title={file.name}
              className="w-full h-[600px] border-0"
            />
          ) : (
            <div className="py-16 text-center">
              <FileText className="mx-auto h-16 w-16 text-muted-foreground opacity-50 mb-4" />
              <p className="text-muted-foreground mb-4">
                此类型文件不支持在线预览
              </p>
              <Button asChild>
                <a href={file.url} download>
                  <Download className="h-4 w-4" />
                  下载文件
                </a>
              </Button>
            </div>
          )}
        </div>

        <div className="flex justify-end">
          <Button variant="outline" onClick={onClose}>
            关闭
          </Button>
        </div>
      </div>
    </Dialog>
  )
}