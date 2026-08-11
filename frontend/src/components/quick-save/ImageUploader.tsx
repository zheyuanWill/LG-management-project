import { useState, useRef } from 'react'
import { Upload, Wand2, Loader2, X, Image as ImageIcon } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { cn } from '@/lib/utils'

interface ImageUploaderProps {
  onRecognize: (file: string) => void
}

export default function ImageUploader({ onRecognize }: ImageUploaderProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [isRecognizing, setIsRecognizing] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    const file = files[0]
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
  }

  const handleClear = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
    }
    setPreviewUrl(null)
    if (inputRef.current) {
      inputRef.current.value = ''
    }
  }

  const handleRecognize = async () => {
    if (!previewUrl) {
      return
    }
    setIsRecognizing(true)
    try {
      await onRecognize(previewUrl)
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
          previewUrl ? 'border-solid' : 'border-border hover:border-primary/50'
        )}
        onClick={!previewUrl ? triggerFileSelect : undefined}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={handleFileSelect}
        />
        {previewUrl ? (
          <div className="relative">
            <img
              src={previewUrl}
              alt="预览"
              className="max-h-64 rounded-lg border"
            />
            <button
              className="absolute -top-2 -right-2 p-1 rounded-full bg-destructive text-white"
              onClick={(e) => { e.stopPropagation(); handleClear() }}
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <>
            <ImageIcon className="h-10 w-10 text-muted-foreground opacity-50 mb-2" />
            <p className="text-sm text-muted-foreground mb-4">
              点击此处选择微信截图
            </p>
            <Button type="button" onClick={(e) => { e.stopPropagation(); triggerFileSelect() }}>
              <Upload className="h-4 w-4 mr-2" />
              选择图片
            </Button>
          </>
        )}
      </div>

      <div className="flex justify-end">
        <Button onClick={handleRecognize} disabled={isRecognizing || !previewUrl}>
          {isRecognizing ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Wand2 className="h-4 w-4" />
          )}
          识别
        </Button>
      </div>
    </div>
  )
}