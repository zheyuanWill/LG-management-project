import { createFileRoute } from '@tanstack/react-router'
import { AIChatPanel } from '@/components/ai-chat'

export const Route = createFileRoute('/_authenticated/ai-assistant')({
  component: AIAssistantPage,
})

function AIAssistantPage() {
  return (
    <div style={{
      height: 'calc(100vh - 100px)',
      display: 'flex',
      flexDirection: 'column',
      borderRadius: 12,
      overflow: 'hidden',
      boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
    }}>
      <AIChatPanel baseUrl="" style={{ flex: 1 }} />
    </div>
  )
}
