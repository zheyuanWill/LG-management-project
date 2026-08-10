import { useState } from 'react'
import { Upload, X, Image as ImageIcon, Trash2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { useApiGet, useApiPost, useApiDelete } from '@/hooks/useApi'
import { cn } from '@/lib/utils'

interface Photo {
  id: string
  url: string
  thumbnail_url?: string
  type: 'logo_package' | 'loading'
  created_at: string
}

interface SparePhotosProps {
  projectId: string
}

const photoTypeLabels: Record<string, string> = {
  logo_package: 'LOGO 包装照',
  loading: '装车照',
}

export default function SparePhotos({ projectId }: SparePhotosProps) {
  const { data: photos, isLoading } = useApiGet<Photo[]>(
    `/projects/${projectId}/photos`
  )
  const uploadMutation = useApiPost<Photo>(`/projects/${projectId}/photos`)
  const deleteMutation = useApiDelete<void>(`/projects/${projectId}/photos`)

  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [uploadingType, setUploadingType] = useState<string | null>(null)

  const handleFileSelect = async (
    e: React.ChangeEvent<HTMLInputElement>,
    type: 'logo_package' | 'loading'
  ) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    setUploadingType(type)
    try {
      for (const file of Array.from(files)) {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('type', type)
        await uploadMutation.mutateAsync(formData as unknown as Record<string, unknown>)
      }
    } finally {
      setUploadingType(null)
      e.target.value = ''
    }
  }

  const handleDelete = (id: string) => {
    if (confirm('确定删除该照片?')) {
      deleteMutation.mutate(id)
    }
  }

  const renderPhotoSection = (type: 'logo_package' | 'loading', required: boolean) => {
    const typePhotos = (photos || []).filter((p) => p.type === type)

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-medium">{photoTypeLabels[type]}</h3>
            {required && (
              <Badge variant="destructive" className="text-xs">
                必填
              </Badge>
            )}
          </div>
          <label className="cursor-pointer">
            <input
              type="file"
              accept="image/*"
              multiple
              className="hidden"
              onChange={(e) => handleFileSelect(e, type)}
              disabled={uploadingType !== null}
            />
            <Button variant="outline" size="sm" asChild>
              <span className="flex items-center gap-2">
                <Upload className="h-3 w-3" />
                {uploadingType === type ? '上传中...' : '上传'}
              </span>
            </Button>
          </label>
        </div>

        {typePhotos.length === 0 ? (
          <div className="flex items-center justify-center rounded-lg border-2 border-dashed border-border p-8 text-muted-foreground">
            <div className="text-center">
              <ImageIcon className="mx-auto h-8 w-8 mb-2 opacity-50" />
              <p className="text-sm">暂无照片</p>
              <p className="text-xs mt-1">点击上方按钮上传照片</p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {typePhotos.map((photo) => (
              <div
                key={photo.id}
                className="group relative rounded-lg overflow-hidden border border-border"
              >
                <img
                  src={photo.thumbnail_url || photo.url}
                  alt={photoTypeLabels[type]}
                  className="w-full aspect-square object-cover cursor-pointer"
                  onClick={() => setPreviewUrl(photo.url)}
                />
                <button
                  className={cn(
                    'absolute top-1 right-1 p-1 rounded-full bg-black/60 text-white opacity-0 group-hover:opacity-100 transition-opacity'
                  )}
                  onClick={() => handleDelete(photo.id)}
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>发货照片</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {isLoading ? (
          <p className="text-muted-foreground text-sm">加载中...</p>
        ) : (
          <>
            {renderPhotoSection('logo_package', true)}
            {renderPhotoSection('loading', true)}
          </>
        )}
      </CardContent>

      {previewUrl && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
          onClick={() => setPreviewUrl(null)}
        >
          <button
            className="absolute top-4 right-4 p-2 rounded-full bg-white/10 text-white"
            onClick={() => setPreviewUrl(null)}
          >
            <X className="h-6 w-6" />
          </button>
          <img
            src={previewUrl}
            alt="预览"
            className="max-w-full max-h-full object-contain"
          />
        </div>
      )}
    </Card>
  )
}