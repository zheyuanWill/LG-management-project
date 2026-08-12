import { useState, useRef } from 'react'
import { Upload, Wand2, Loader2, X, Image as ImageIcon } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { cn } from '@/lib/utils'

interface ImageUploaderProps {
  onRecognize: (file: File) => Promise<void>
  onRecognizeMultiple?: (files: File[]) => Promise<void>
}

export default function ImageUploader({ onRecognize }: ImageUploaderProps) {
  const [previews, setPreviews] = useState<{ file: File; url: string }[]>([])
  const [isRecognizing, setIsRecognizing] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    const newItems: { file: File; url: string }[] = []
    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      if (file.type.startsWith('image/')) {
        const url = URL.createObjectURL(file)
        newItems.push({ file, url })
      }
    }
    setPreviews((prev) => [...prev, ...newItems])
  }

  const handleRemove = (index: number) => {
    setPreviews((prev) => {
      const item = prev[index]
      if (item) URL.revokeObjectURL(item.url)
      return prev.filter((_, i) => i !== index)
    })
  }

  const handleClearAll = () => {
    previews.forEach((p) => URL.revokeObjectURL(p.url))
    setPreviews([])
    if (inputRef.current) inputRef.current.value = ''
  }

  const handleRecognize = async () => {
    if (previews.length === 0) return
    setIsRecognizing(true)
    try {
      // Recognize each image sequentially
      for (const { file } of previews) {
        await onRecognize(file)
      }
      // Clear after all done
      handleClearAll()
    } catch {
      // error toast handled by parent
    } finally {
      setIsRecognizing(false)
    }
  }

  const triggerFileSelect = () => {
    inputRef.current?.click()
  }

  return (
    <div className="space-y-4">
      <div
        className={cn(
          'relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 transition-colors cursor-pointer',
          previews.length > 0 ? 'border-solid' : 'border-border hover:border-primary/50'
        )}
        onClick={triggerFileSelect}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          multiple
          className="hidden"
          onChange={handleFileSelect}
        />

        {previews.length === 0 ? (
          <>
            <ImageIcon className="h-10 w-10 text-muted-foreground opacity-50 mb-2" />
            <p className="text-sm text-muted-foreground mb-4">
              点击选择图片（支持多选）
            </p>
            <Button type="button" onClick={(e) => { e.stopPropagation(); triggerFileSelect() }}>
              <Upload className="h-4 w-4 mr-2" />
              选择图片
            </Button>
          </>
        ) : (
          <div className="w-full">
            <div className="grid grid-cols-2 gap-2 mb-3">
              {previews.map(({ file, url }, index) => (
                <div key={index} className="relative group">
                  <img
                    src={url}
                    alt={`预览 ${index + 1}`}
                    className="w-full h-24 object-cover rounded-md border"
                  />
                  <button
                    className="absolute -top-1.5 -right-1.5 p-0.5 rounded-full bg-destructive text-white opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => { e.stopPropagation(); handleRemove(index) }}
                  >
                    <X className="h-3 w-3" />
                  </button>
                  <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-[10px] px-1 py-0.5 truncate rounded-b-md">
                    {file.name.slice(0, 15)}{file.name.length > 15 ? '...' : ''}
                  </div>
                </div>
              ))}
            </div>
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>已选 {previews.length} 张图片</span>
              <button
                className="hover:text-destructive"
                onClick={(e) => { e.stopPropagation(); handleClearAll() }}
              >
                清除全部
              </button>
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="mt-2 w-full"
              onClick={(e) => { e.stopPropagation(); triggerFileSelect() }}
            >
              <Upload className="h-3 w-3 mr-1" />
              继续添加
            </Button>
          </div>
        )}
      </div>

      {previews.length > 0 && (
        <div className="flex justify-end">
          <Button onClick={handleRecognize} disabled={isRecognizing}>
            {isRecognizing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Wand2 className="h-4 w-4" />
            )}
            {isRecognizing ? `识别中 (${previews.length}张)` : `识别全部 (${previews.length}张)`}
          </Button>
        </div>
      )}
    </div>
  )
}
