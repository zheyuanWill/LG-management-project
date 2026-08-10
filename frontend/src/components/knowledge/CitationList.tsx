import { useState } from 'react'
import { FileText, ExternalLink, Copy, Check } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Citation {
  document_id: string
  document_title: string
  snippet: string
  score?: number
}

interface CitationListProps {
  citations: Citation[]
}

export default function CitationList({ citations }: CitationListProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const handleCopy = async (citation: Citation) => {
    try {
      await navigator.clipboard.writeText(citation.snippet)
      setCopiedId(citation.document_id)
      setTimeout(() => setCopiedId(null), 2000)
    } catch {
      // ignore
    }
  }

  const handleJump = (documentId: string) => {
    console.log('跳转到文档:', documentId)
  }

  return (
    <div className="space-y-2">
      {citations.map((citation) => (
        <div
          key={citation.document_id}
          className="rounded-md border bg-muted/30 p-3 text-sm"
        >
          <div className="flex items-center justify-between gap-2 mb-2">
            <div className="flex items-center gap-2 min-w-0">
              <FileText className="h-3 w-3 text-primary shrink-0" />
              <span className="font-medium truncate">{citation.document_title}</span>
            </div>
            <div className="flex items-center gap-1 shrink-0">
              <button
                className="p-1 rounded hover:bg-muted"
                onClick={() => handleCopy(citation)}
                title="复制片段"
              >
                {copiedId === citation.document_id ? (
                  <Check className="h-3 w-3 text-green-500" />
                ) : (
                  <Copy className="h-3 w-3 text-muted-foreground" />
                )}
              </button>
              <button
                className="p-1 rounded hover:bg-muted"
                onClick={() => handleJump(citation.document_id)}
                title="跳转到文档"
              >
                <ExternalLink className="h-3 w-3 text-muted-foreground" />
              </button>
            </div>
          </div>
          <p className={cn('text-muted-foreground text-xs leading-relaxed')}>
            {citation.snippet}
          </p>
          {citation.score !== undefined && (
            <div className="flex items-center gap-1 mt-2">
              <div className="flex-1 h-1 rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full bg-primary"
                  style={{ width: `${citation.score * 100}%` }}
                />
              </div>
              <span className="text-xs text-muted-foreground">
                {(citation.score * 100).toFixed(0)}%
              </span>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}