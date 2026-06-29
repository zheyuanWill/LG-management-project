import React from 'react'

const pulseKeyframes = `
@keyframes skeletonPulse {
  0% { opacity: 1; }
  50% { opacity: 0.4; }
  100% { opacity: 1; }
}
`

const lineStyle: React.CSSProperties = {
  height: 14,
  background: '#f0f2f5',
  borderRadius: 4,
  animation: 'skeletonPulse 1.5s ease-in-out infinite',
}

export function SkeletonCard() {
  return (
    <>
      <style>{pulseKeyframes}</style>
      <div style={{ background: '#fff', borderRadius: 12, padding: 20, boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: '#f0f2f5', flexShrink: 0, ...{ animation: 'skeletonPulse 1.5s ease-in-out infinite' } }} />
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ ...lineStyle, width: '40%' }} />
            <div style={{ ...lineStyle, width: '60%', height: 10 }} />
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ ...lineStyle, width: '100%' }} />
          <div style={{ ...lineStyle, width: '80%' }} />
          <div style={{ ...lineStyle, width: '60%' }} />
        </div>
      </div>
    </>
  )
}
