import { useState } from 'react'
import { ClipboardPaste, Wand2, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/Button'

interface TextPasterProps {
  onRecognize: (text: string) => void
}

export default function TextPaster({ onRecognize }: TextPasterProps) {
  const [text, setText] = useState('')
  const [isRecognizing, setIsRecognizing] = useState(false)

  const handlePaste = async () => {
    try {
      const clipboardText = await navigator.clipboard.readText()
      if (clipboardText) {
        setText(clipboardText)
      }
    } catch {
      alert('无法访问剪贴板,请手动粘贴')
    }
  }

  const handleRecognize = async () => {
    if (!text.trim()) {
      alert('请输入或粘贴内容')
      return
    }
    setIsRecognizing(true)
    try {
      await onRecognize(text)
    } finally {
      setIsRecognizing(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={handlePaste}>
          <ClipboardPaste className="h-4 w-4" />
          粘贴剪贴板
        </Button>
        {text && (
          <Button variant="ghost" size="sm" onClick={() => setText('')}>
            清空
          </Button>
        )}
      </div>

      <textarea
        className="flex min-h-[200px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        placeholder="在此粘贴或输入文字内容,如微信聊天记录、船东指示等..."
        value={text}
        onChange={(e) => setText(e.target.value)}
      />

      <div className="flex justify-end">
        <Button onClick={handleRecognize} disabled={isRecognizing || !text.trim()}>
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