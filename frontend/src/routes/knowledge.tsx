import { useState } from 'react'
import { BookOpen, Upload, FileText } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { useApiGet } from '@/hooks/useApi'
import DocUploader from '@/components/knowledge/DocUploader'
import QAChat from '@/components/knowledge/QAChat'
import { cn } from '@/lib/utils'

interface KnowledgeDoc {
  id: string
  title: string
  category: string
  file_name: string
  created_at: string
}

const categoryLabels: Record<string, { label: string; color: string }> = {
  QM: { label: 'QM', color: 'bg-blue-500' },
  SUP: { label: 'SUP', color: 'bg-green-500' },
  REP: { label: 'REP', color: 'bg-amber-500' },
  BRO: { label: 'BRO', color: 'bg-purple-500' },
  SPL: { label: 'SPL', color: 'bg-cyan-500' },
  SPEC: { label: 'SPEC', color: 'bg-rose-500' },
}

export default function KnowledgePage() {
  const { data: documents, isLoading } = useApiGet<KnowledgeDoc[]>('/knowledge/documents')
  const [showUploader, setShowUploader] = useState(false)
  const [activeCategory, setActiveCategory] = useState<string>('all')

  const filteredDocs = (documents || []).filter((doc) => {
    if (activeCategory === 'all') return true
    return doc.category === activeCategory
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <BookOpen className="h-8 w-8 text-primary" />
            RAG 知识库
          </h1>
          <p className="text-muted-foreground mt-1">基于文档的智能问答系统</p>
        </div>
        <Button onClick={() => setShowUploader(true)}>
          <Upload className="h-4 w-4" />
          上传文档
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1">
          <CardContent className="p-4 space-y-4">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">分类筛选:</span>
            </div>
            <div className="flex flex-wrap gap-1">
              <button
                onClick={() => setActiveCategory('all')}
                className={cn(
                  'px-2 py-1 text-xs rounded-md transition-colors',
                  activeCategory === 'all'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:text-foreground'
                )}
              >
                全部
              </button>
              {Object.entries(categoryLabels).map(([key, val]) => (
                <button
                  key={key}
                  onClick={() => setActiveCategory(key)}
                  className={cn(
                    'px-2 py-1 text-xs rounded-md transition-colors',
                    activeCategory === key
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-muted-foreground hover:text-foreground'
                  )}
                >
                  {val.label}
                </button>
              ))}
            </div>

            <div className="space-y-2">
              {isLoading ? (
                <p className="text-muted-foreground text-sm">加载中...</p>
              ) : filteredDocs.length === 0 ? (
                <div className="py-8 text-center text-muted-foreground">
                  <FileText className="mx-auto h-8 w-8 opacity-50 mb-2" />
                  <p className="text-sm">暂无文档</p>
                  <p className="text-xs mt-1">点击"上传文档"添加知识</p>
                </div>
              ) : (
                <div className="space-y-1">
                  {filteredDocs.map((doc) => {
                    const cat = categoryLabels[doc.category] || { label: doc.category, color: 'bg-gray-500' }
                    return (
                      <div
                        key={doc.id}
                        className="flex items-center gap-2 p-2 rounded-md hover:bg-muted cursor-pointer group"
                      >
                        <div className={cn('w-2 h-2 rounded-full shrink-0', cat.color)} />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{doc.title}</p>
                          <p className="text-xs text-muted-foreground truncate">{doc.file_name}</p>
                        </div>
                        <Badge variant="secondary" className="text-xs shrink-0">
                          {cat.label}
                        </Badge>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardContent className="p-0 h-[calc(100vh-200px)]">
            <QAChat />
          </CardContent>
        </Card>
      </div>

      {showUploader && (
        <DocUploader onClose={() => setShowUploader(false)} />
      )}
    </div>
  )
}