import { useMemo } from 'react'

// 极简、零依赖的 Markdown 渲染器。
// 关键点：先转义 HTML 实体，再施加 markdown 变换，因此即使原文夹带 HTML 也只会被当作纯文本，避免 XSS。
function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function renderInline(text: string): string {
  let s = escapeHtml(text)
  // 链接 [文本](http(s)://...) —— 仅允许 http/https
  s = s.replace(
    /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
    (_m, t: string, u: string) =>
      `<a href="${u}" target="_blank" rel="noopener noreferrer" class="text-primary underline underline-offset-2 hover:opacity-80">${t}</a>`
  )
  // 加粗 **文本**
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  // 行内代码 `代码`
  s = s.replace(/`([^`]+)`/g, '<code class="rounded bg-muted px-1 py-0.5 text-xs font-mono">$1</code>')
  return s
}

function renderMarkdown(md: string): string {
  if (!md) return ''
  const lines = md.replace(/\r\n/g, '\n').split('\n')
  const html: string[] = []
  let i = 0
  let listType: 'ul' | 'ol' | null = null

  const closeList = () => {
    if (listType) {
      html.push(`</${listType}>`)
      listType = null
    }
  }

  while (i < lines.length) {
    const line = lines[i]

    if (!line.trim()) {
      closeList()
      i++
      continue
    }

    const h = line.match(/^(#{1,3})\s+(.*)$/)
    if (h) {
      closeList()
      const level = h[1].length
      const content = renderInline(h[2])
      const cls =
        level === 1
          ? 'text-lg font-bold mt-3 mb-1'
          : level === 2
            ? 'text-base font-semibold mt-2 mb-1'
            : 'text-sm font-semibold mt-2 mb-1'
      html.push(`<h${level} class="${cls}">${content}</h${level}>`)
      i++
      continue
    }

    const ul = line.match(/^[-*]\s+(.*)$/)
    if (ul) {
      if (listType !== 'ul') {
        closeList()
        html.push('<ul class="list-disc pl-5 space-y-1 my-1">')
        listType = 'ul'
      }
      html.push(`<li>${renderInline(ul[1])}</li>`)
      i++
      continue
    }

    const ol = line.match(/^\d+\.\s+(.*)$/)
    if (ol) {
      if (listType !== 'ol') {
        closeList()
        html.push('<ol class="list-decimal pl-5 space-y-1 my-1">')
        listType = 'ol'
      }
      html.push(`<li>${renderInline(ol[1])}</li>`)
      i++
      continue
    }

    closeList()
    const paraLines: string[] = []
    while (
      i < lines.length &&
      lines[i].trim() &&
      !/^(#{1,3})\s+/.test(lines[i]) &&
      !/^[-*]\s+/.test(lines[i]) &&
      !/^\d+\.\s+/.test(lines[i])
    ) {
      paraLines.push(renderInline(lines[i]))
      i++
    }
    html.push(`<p class="leading-relaxed my-1">${paraLines.join('<br/>')}</p>`)
  }
  closeList()
  return html.join('\n')
}

interface MarkdownViewProps {
  content: string
  className?: string
}

export default function MarkdownView({ content, className = '' }: MarkdownViewProps) {
  const html = useMemo(() => renderMarkdown(content || ''), [content])
  return (
    <div
      className={`text-sm text-foreground ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}
