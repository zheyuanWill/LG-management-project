import { useState, useEffect } from 'react'
import { Download, ExternalLink, FileText, Loader2 } from 'lucide-react'
import { Dialog } from '@/components/ui/Dialog'
import { Button } from '@/components/ui/Button'
import apiClient from '@/lib/api'
import type { FileItem } from '@/types'

interface FilePreviewProps {
  file: FileItem
  onClose: () => void
}

const imageMimeTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp']

export default function FilePreview({ file, onClose }: FilePreviewProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    // If the file item already has a usable URL, use it directly
    if (file.url || file.download_url) {
      setPreviewUrl(file.url || file.download_url!)
      setLoading(false)
      return
    }

    // Otherwise fetch a presigned URL from the backend
    const fetchUrl = async () => {
      try {
        if (file.id) {
          const resp = await apiClient.get(`/files/${file.id}/preview`)
          if (!cancelled) {
            setPreviewUrl(resp.data.preview_url)
            setLoading(false)
          }
        } else if (file.storage_key) {
          const resp = await apiClient.get('/files/url', {
            params: { storage_key: file.storage_key },
          })
          if (!cancelled) {
            setPreviewUrl(resp.data.preview_url || resp.data.download_url)
            setLoading(false)
          }
        } else {
          if (!cancelled) {
            setError('无法获取文件预览地址')
            setLoading(false)
          }
        }
      } catch {
        if (!cancelled) {
          setError('文件加载失败，可能已失效')
          setLoading(false)
        }
      }
    }

    fetchUrl()
    return () => {
      cancelled = true
    }
  }, [file])

  const displayName = file.file_name || file.name || '未命名文件'
  const fileSizeKB = ((file.file_size || file.size || 0) / 1024).toFixed(1)
  const isImage = imageMimeTypes.includes(file.mime_type || '')
  const isPdf = file.mime_type === 'application/pdf'

  return (
    <Dialog open={true} onOpenChange={(open) => !open && onClose()} title={displayName} className="max-w-4xl">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <FileText className="h-4 w-4" />
            <span>{fileSizeKB} KB</span>
            {file.mime_type && (
              <span className="text-xs">({file.mime_type})</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" asChild>
              <a href={previewUrl || '#'} target="_blank" rel="noreferrer" className={!previewUrl ? 'pointer-events-none opacity-50' : ''}>
                <ExternalLink className="h-4 w-4" />
                新窗口打开
              </a>
            </Button>
            <Button size="sm" asChild>
              <a href={previewUrl || '#'} download={displayName} className={!previewUrl ? 'pointer-events-none opacity-50' : ''}>
                <Download className="h-4 w-4" />
                下载
              </a>
            </Button>
          </div>
        </div>

        <div className="min-h-[400px] max-h-[600px] rounded-lg border bg-muted/30 overflow-auto flex items-center justify-center">
          {loading ? (
            <div className="flex flex-col items-center gap-3 py-16">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              <p className="text-sm text-muted-foreground">加载文件中...</p>
            </div>
          ) : error ? (
            <div className="py-16 text-center">
              <FileText className="mx-auto h-16 w-16 text-muted-foreground opacity-50 mb-4" />
              <p className="text-muted-foreground mb-4">{error}</p>
            </div>
          ) : isImage ? (
            <img
              src={previewUrl || ''}
              alt={displayName}
              className="max-w-full max-h-[600px] object-contain"
            />
          ) : isPdf ? (
            <iframe
              src={previewUrl || ''}
              title={displayName}
              className="w-full h-[600px] border-0"
            />
          ) : (
            <div className="py-16 text-center">
              <FileText className="mx-auto h-16 w-16 text-muted-foreground opacity-50 mb-4" />
              <p className="text-muted-foreground mb-4">
                此类型文件不支持在线预览
              </p>
              <Button asChild>
                <a href={previewUrl || '#'} download={displayName}>
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
