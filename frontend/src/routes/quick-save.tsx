import { useState } from 'react'
import { Save, Sparkles, FileText } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import TextPaster from '@/components/quick-save/TextPaster'
import ImageUploader from '@/components/quick-save/ImageUploader'
import SuggestionList, {
  type SuggestionItem,
  type QuickSaveResponse,
} from '@/components/quick-save/SuggestionList'
import apiClient from '@/lib/api'
import { toast } from '@/components/ui/Toast'

type QuickSaveTab = 'text' | 'image'

interface RecognizeResult {
  save: QuickSaveResponse
  suggestions: SuggestionItem[]
}

export default function QuickSavePage() {
  const [activeTab, setActiveTab] = useState<QuickSaveTab>('text')
  const [result, setResult] = useState<RecognizeResult | null>(null)
  const [isRecognizing, setIsRecognizing] = useState(false)

  const handleRecognizeText = async (text: string) => {
    setIsRecognizing(true)
    try {
      const res = await apiClient.post<RecognizeResult>('/quick-saves/text', null, {
        params: { text },
      })
      setResult(res.data)
    } catch {
      toast.error({ title: '识别失败', description: 'AI 服务暂不可用,请稍后重试' })
    } finally {
      setIsRecognizing(false)
    }
  }

  const handleRecognizeImage = async (file: File) => {
    setIsRecognizing(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await apiClient.post<RecognizeResult>('/quick-saves/image', formData)
      setResult(res.data)
      if (!res.data.suggestions || res.data.suggestions.length === 0) {
        toast.info({
          title: '图片已保存',
          description: '当前未启用图片文字识别,请手动选择关联项目',
        })
      }
    } catch {
      toast.error({ title: '保存失败', description: '请稍后重试' })
    } finally {
      setIsRecognizing(false)
    }
  }

  const handleConfirm = async (projectId: number) => {
    if (!result) return
    try {
      await apiClient.patch(`/quick-saves/${result.save.id}`, {
        confirmed_project_id: projectId,
      })
      toast.success({ title: '已关联项目', description: '随手存记录已确认' })
      setResult(null)
    } catch {
      toast.error({ title: '关联失败', description: '请稍后重试' })
    }
  }

  const handleDelete = async () => {
    if (!result) return
    try {
      await apiClient.patch(`/quick-saves/${result.save.id}`, { status: 'deleted' })
      toast.success({ title: '已删除随手存记录' })
      setResult(null)
    } catch {
      toast.error({ title: '删除失败', description: '请稍后重试' })
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Save className="h-8 w-8 text-primary" />
          随手存
        </h1>
        <p className="text-muted-foreground mt-1">
          快速保存微信截图或文字,AI 智能识别并关联项目
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>输入内容</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2 mb-4">
              <button
                onClick={() => setActiveTab('text')}
                className={`px-4 py-2 text-sm rounded-md transition-colors ${
                  activeTab === 'text'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:text-foreground'
                }`}
              >
                粘贴文字
              </button>
              <button
                onClick={() => setActiveTab('image')}
                className={`px-4 py-2 text-sm rounded-md transition-colors ${
                  activeTab === 'image'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:text-foreground'
                }`}
              >
                上传截图
              </button>
            </div>

            {activeTab === 'text' ? (
              <TextPaster onRecognize={handleRecognizeText} />
            ) : (
              <ImageUploader onRecognize={handleRecognizeImage} />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              AI 识别结果
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isRecognizing ? (
              <div className="py-16 text-center text-muted-foreground">
                <div className="animate-spin rounded-full h-8 w-8 border-4 border-primary border-t-transparent mx-auto mb-3" />
                <p>AI 正在识别中...</p>
              </div>
            ) : !result ? (
              <div className="py-16 text-center text-muted-foreground">
                <FileText className="mx-auto h-10 w-10 opacity-50 mb-3" />
                <p className="text-sm">请在左侧输入内容并点击“识别”</p>
              </div>
            ) : (
              <SuggestionList
                save={result.save}
                suggestions={result.suggestions ?? []}
                onConfirm={handleConfirm}
                onDelete={handleDelete}
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
