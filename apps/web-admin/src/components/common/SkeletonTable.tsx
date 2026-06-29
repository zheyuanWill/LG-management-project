import React from 'react'

const pulseKeyframes = `
@keyframes skeletonPulse {
  0% { opacity: 1; }
  50% { opacity: 0.4; }
  100% { opacity: 1; }
}
`

interface SkeletonTableProps {
  rows?: number
  columns?: number
}

const WIDTHS = ['15%', '25%', '20%', '12%', '15%', '13%']

export function SkeletonTable({ rows = 5, columns = 6 }: SkeletonTableProps) {
  const cellStyle = (isHeader: boolean): React.CSSProperties => ({
    height: isHeader ? 12 : 14,
    background: isHeader ? '#e8eaed' : '#f0f2f5',
    borderRadius: 4,
    flex: 1,
    animation: 'skeletonPulse 1.5s ease-in-out infinite',
  })

  return (
    <>
      <style>{pulseKeyframes}</style>
      <div style={{ background: '#fff', borderRadius: 12, padding: 16, boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
        <div style={{ display: 'flex', gap: 12, paddingBottom: 12, borderBottom: '2px solid #f0f2f5', marginBottom: 8 }}>
          {Array.from({ length: columns }, (_, i) => (
            <div key={`h${i}`} style={{ ...cellStyle(true), maxWidth: WIDTHS[i % WIDTHS.length] }} />
          ))}
        </div>
        {Array.from({ length: rows }, (_, r) => (
          <div key={`r${r}`} style={{ display: 'flex', gap: 12, padding: '12px 0', borderBottom: r < rows - 1 ? '1px solid #f5f7fa' : 'none' }}>
            {Array.from({ length: columns }, (_, c) => (
              <div key={`c${c}`} style={{ ...cellStyle(false), maxWidth: WIDTHS[c % WIDTHS.length] }} />
            ))}
          </div>
        ))}
      </div>
    </>
  )
}
