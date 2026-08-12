import { useState, useRef } from 'react'
import { Upload, X, Image as ImageIcon } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { useApiPost } from '@/hooks/useApi'
import { formatDate } from '@/lib/utils'

interface PhotoResponse {
  id: number
  project_id: number
  photo_type: string
  storage_key: string
  created_at: string
}

interface UploadedPhoto {
  id: number
  url: string
  photo_type: 'logo' | 'loading'
  storage_key: string
  created_at: string
}

interface SparePhotosProps {
  projectId: string
}

const photoTypeLabels: Record<string, string> = {
  logo: 'LOGO 包装照',
  loading: '装车照',
}

export default function SparePhotos({ projectId }: SparePhotosProps) {
  const uploadLogo = useApiPost<PhotoResponse>(
    `/spare-parts/projects/${projectId}/spare-photos?photo_type=logo`
  )
  const uploadLoading = useApiPost<PhotoResponse>(
    `/spare-parts/projects/${projectId}/spare-photos?photo_type=loading`
  )

  const [photos, setPhotos] = useState<UploadedPhoto[]>([])
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [uploadingType, setUploadingType] = useState<string | null>(null)
  const logoInputRef = useRef<HTMLInputElement>(null)
  const loadingInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = async (
    e: React.ChangeEvent<HTMLInputElement>,
    type: 'logo' | 'loading'
  ) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    setUploadingType(type)
    try {
      const mutation = type === 'logo' ? uploadLogo : uploadLoading
      for (const file of Array.from(files)) {
        const formData = new FormData()
        formData.append('file', file)
        const res = await mutation.mutateAsync(formData as unknown as Record<string, unknown>)
        const objectUrl = URL.createObjectURL(file)
        setPhotos((prev) => [
          ...prev,
          {
            id: res.id,
            url: objectUrl,
            photo_type: type,
            storage_key: res.storage_key,
            created_at: res.created_at,
          },
        ])
      }
    } finally {
      setUploadingType(null)
      e.target.value = ''
    }
  }

  const renderPhotoSection = (type: 'logo' | 'loading', required: boolean) => {
    const typePhotos = photos.filter((p) => p.photo_type === type)

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-medium">{photoTypeLabels[type]}</h3>
            {required && (
              <span className="text-xs text-destructive bg-destructive/10 px-2 py-0.5 rounded">
                必填
              </span>
            )}
          </div>
          <input
            type="file"
            accept="image/*"
            multiple
            className="hidden"
            ref={type === 'logo' ? logoInputRef : loadingInputRef}
            onChange={(e) => handleFileSelect(e, type)}
            disabled={uploadingType !== null}
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() => (type === 'logo' ? logoInputRef : loadingInputRef).current?.click()}
          >
            <Upload className="h-3 w-3" />
            {uploadingType === type ? '上传中...' : '上传'}
          </Button>
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
                  src={photo.url}
                  alt={photoTypeLabels[type]}
                  className="w-full aspect-square object-cover cursor-pointer"
                  onClick={() => setPreviewUrl(photo.url)}
                />
                <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-[10px] px-1 py-0.5 truncate">
                  {formatDate(photo.created_at)}
                </div>
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
        {renderPhotoSection('logo', true)}
        {renderPhotoSection('loading', true)}
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
