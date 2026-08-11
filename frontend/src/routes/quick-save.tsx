import { useState } from 'react'
import { Save, Sparkles, FileText } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import TextPaster from '@/components/quick-save/TextPaster'
import ImageUploader from '@/components/quick-save/ImageUploader'
import SuggestionList from '@/components/quick-save/SuggestionList'

type QuickSaveTab = 'text' | 'image'

interface AISuggestion {
  summary: string
  projects: {
    id: string
    name: string
    project_no: string
    confidence: number
  }[]
}

export default function QuickSavePage() {
  const [activeTab, setActiveTab] = useState<QuickSaveTab>('text')
  const [suggestion, setSuggestion] = useState<AISuggestion | null>(null)
  const [isRecognizing, setIsRecognizing] = useState(false)

  const handleRecognize = async (_content: string, type: 'text' | 'image') => {
    setIsRecognizing(true)
    setSuggestion(null)
    try {
      await new Promise((resolve) => setTimeout(resolve, 1000))
      setSuggestion({
        summary: `AI 识别结果: 从${type === 'text' ? '文字' : '截图'}中提取到关键信息,匹配到相关项目。`,
        projects: [
          { id: '1', name: '远洋一号', project_no: 'BS-2024-001', confidence: 0.92 },
          { id: '2', name: '海运先锋', project_no: 'BS-2024-005', confidence: 0.78 },
          { id: '3', name: '东方之星', project_no: 'SP-2024-012', confidence: 0.65 },
        ],
      })
    } finally {
      setIsRecognizing(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Save className="h-8 w-8 text-primary" />
          随手存
        </h1>
        <p className="text-muted-foreground mt-1">快速保存微信截图或文字,AI 智能识别关联项目</p>
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
              <TextPaster onRecognize={(text) => handleRecognize(text, 'text')} />
            ) : (
              <ImageUploader onRecognize={(file) => handleRecognize(file, 'image')} />
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
            ) : !suggestion ? (
              <div className="py-16 text-center text-muted-foreground">
                <FileText className="mx-auto h-10 w-10 opacity-50 mb-3" />
                <p className="text-sm">请在左侧输入内容并点击"识别"</p>
              </div>
            ) : (
              <SuggestionList
                suggestion={suggestion}
                onConfirm={(projectId) => {
                  alert(`已关联到项目: ${projectId}`)
                  setSuggestion(null)
                }}
                onChangeProject={() => {
                  setSuggestion({ ...suggestion, projects: suggestion.projects.slice(1) })
                }}
                onDelete={() => {
                  setSuggestion(null)
                }}
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}