import { useRef } from 'react'
import { Upload, X, Image as ImageIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Photo } from '@/types'

interface PhotoUploaderProps {
  taskId: string
  date: string
  photos: Photo[]
  maxPhotos?: number
  onUpload: (files: File[]) => void
  onDelete: (photoId: string) => void
}

export default function PhotoUploader({
  photos,
  maxPhotos = 2,
  onUpload,
  onDelete,
}: PhotoUploaderProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const isFull = photos.length >= maxPhotos

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return
    const remaining = maxPhotos - photos.length
    const selected = Array.from(files).slice(0, remaining)
    onUpload(selected)
    e.target.value = ''
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">
          现场照片 <span className="text-muted-foreground font-normal">({photos.length}/{maxPhotos})</span>
        </span>
        {isFull && (
          <span className="text-xs text-destructive font-medium">今日已传满</span>
        )}
      </div>

      <div className="flex flex-wrap gap-3">
        {photos.map((photo) => (
          <div
            key={photo.id}
            className="group relative w-28 h-28 rounded-lg overflow-hidden border border-border"
          >
            <img
              src={photo.thumbnail_url || photo.url}
              alt={photo.caption || '现场照片'}
              className="w-full h-full object-cover"
            />
            <button
              onClick={() => onDelete(photo.id)}
              className="absolute top-1 right-1 rounded-full bg-black/60 p-1 text-white opacity-0 group-hover:opacity-100 transition-opacity hover:bg-destructive"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        ))}

        {!isFull && (
          <button
            onClick={() => fileInputRef.current?.click()}
            className={cn(
              'w-28 h-28 rounded-lg border-2 border-dashed border-border flex flex-col items-center justify-center gap-2 text-muted-foreground transition-colors hover:border-primary hover:text-primary'
            )}
          >
            <Upload className="h-6 w-6" />
            <span className="text-xs">上传照片</span>
          </button>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        multiple={false}
        className="hidden"
        onChange={handleFileSelect}
        disabled={isFull}
      />

      {isFull && (
        <p className="text-xs text-muted-foreground flex items-center gap-1">
          <ImageIcon className="h-3 w-3" />
          每个任务每天最多上传 {maxPhotos} 张照片
        </p>
      )}
    </div>
  )
}