import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Save, Sparkles, FileText, Trash2, Check, Loader2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { toast } from '@/components/ui/Toast'
import apiClient from '@/lib/api'
import TextPaster from '@/components/quick-save/TextPaster'
import ImageUploader from '@/components/quick-save/ImageUploader'
import { stripMarkdown } from '@/lib/utils'

type QuickSaveTab = 'text' | 'image'

interface QuickSaveResponse {
  id: number
  content_type: 'text' | 'image'
  content_text?: string | null
  file_key?: string | null
  recognized_text?: string | null
  status: string
  created_at: string
}

export default function QuickSavePage() {
  const [activeTab, setActiveTab] = useState<QuickSaveTab>('text')
  const [currentResult, setCurrentResult] = useState<QuickSaveResponse | null>(null)
  const [isRecognizing, setIsRecognizing] = useState(false)
  const queryClient = useQueryClient()

  const { data: pendingSaves = [], isLoading: pendingLoading } = useQuery<QuickSaveResponse[]>({
    queryKey: ['/quick-saves', { status: 'pending' }],
    queryFn: async () => {
      const response = await apiClient.get<QuickSaveResponse[]>('/quick-saves', {
        params: { status: 'pending' },
      })
      return response.data
    },
  })

  const handleTextSubmit = async (text: string) => {
    setIsRecognizing(true)
    setCurrentResult(null)
    try {
      const response = await apiClient.post<QuickSaveResponse>('/quick-saves/text', null, {
        params: { text },
      })
      setCurrentResult(response.data)
      if (!response.data.recognized_text) {
        toast.warning({ title: '已保存', description: 'AI 暂时无法识别，已保存原文', duration: 4000 })
      } else {
        toast.success({ title: '已保存', description: 'AI 识别完成', duration: 4000 })
      }
      queryClient.invalidateQueries({ queryKey: ['/quick-saves'] })
    } catch {
      toast.error({ title: '保存失败', description: '请检查网络或登录状态后重试', duration: 4000 })
    } finally {
      setIsRecognizing(false)
    }
  }

  const handleImageSubmit = async (file: File) => {
    setIsRecognizing(true)
    setCurrentResult(null)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await apiClient.post<QuickSaveResponse>('/quick-saves/image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setCurrentResult(response.data)
      if (!response.data.recognized_text) {
        toast.warning({ title: '已保存', description: '图片暂不支持 AI 文字识别，已保存原图', duration: 4000 })
      } else {
        toast.success({ title: '已保存', description: '图片识别完成', duration: 4000 })
      }
      queryClient.invalidateQueries({ queryKey: ['/quick-saves'] })
    } catch {
      toast.error({ title: '上传失败', description: '请检查网络或登录状态后重试', duration: 4000 })
    } finally {
      setIsRecognizing(false)
    }
  }

  const deleteSave = async (saveId: number) => {
    await apiClient.patch(`/quick-saves/${saveId}`, { status: 'deleted' })
    toast.success({ title: '已删除', duration: 4000 })
    if (currentResult?.id === saveId) setCurrentResult(null)
    queryClient.invalidateQueries({ queryKey: ['/quick-saves'] })
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Save className="h-8 w-8 text-primary" />
          随手存
        </h1>
        <p className="text-muted-foreground mt-1">快速保存微信截图或文字,AI 智能识别提取信息</p>
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
                上传截图（支持多选）
              </button>
            </div>

            {activeTab === 'text' ? (
              <TextPaster onRecognize={handleTextSubmit} />
            ) : (
              <ImageUploader onRecognize={handleImageSubmit} />
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
            ) : !currentResult ? (
              <div className="py-16 text-center text-muted-foreground">
                <FileText className="mx-auto h-10 w-10 opacity-50 mb-3" />
                <p className="text-sm">请在左侧输入内容并点击"识别"</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="rounded-lg bg-primary/5 p-4 space-y-2">
                  <p className="text-sm font-medium">AI 识别摘要</p>
                  {currentResult.recognized_text ? (
                    <p className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
                      {stripMarkdown(currentResult.recognized_text)}
                    </p>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      未能自动识别文字。已保存为待处理记录。
                    </p>
                  )}
                </div>
                <div className="flex justify-end pt-2 border-t">
                  <Button variant="destructive" size="sm" onClick={() => deleteSave(currentResult.id)}>
                    <Trash2 className="h-4 w-4 mr-1" />
                    删除
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>待处理随手存</CardTitle>
        </CardHeader>
        <CardContent>
          {pendingLoading ? (
            <div className="py-10 text-center text-muted-foreground flex items-center justify-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              加载中...
            </div>
          ) : pendingSaves.length === 0 ? (
            <div className="py-10 text-center text-muted-foreground">
              <p className="text-sm">暂无待处理的随手存</p>
            </div>
          ) : (
            <div className="space-y-3">
              {pendingSaves.map((save) => (
                <PendingItem key={save.id} save={save} onDelete={deleteSave} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

interface PendingItemProps {
  save: QuickSaveResponse
  onDelete: (id: number) => Promise<void>
}

function PendingItem({ save, onDelete }: PendingItemProps) {
  return (
    <div className="rounded-lg border p-4 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
              save.content_type === 'text'
                ? 'bg-blue-100 text-blue-700'
                : 'bg-purple-100 text-purple-700'
            }`}>
              {save.content_type === 'text' ? '文字' : '图片'}
            </span>
            <span className="text-xs text-muted-foreground">
              {new Date(save.created_at).toLocaleString()}
            </span>
          </div>
          <p className="text-sm whitespace-pre-wrap">
            {save.recognized_text || save.content_text || '(无识别内容)'}
          </p>
        </div>
        <Button variant="destructive" size="sm" onClick={() => onDelete(save.id)}>
          <Trash2 className="h-4 w-4" />
          删除
        </Button>
      </div>
    </div>
  )
}
