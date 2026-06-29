import { useMemo } from 'react';
import { Typography } from 'antd';

const { Paragraph, Text, Title } = Typography;

interface Props {
  content: string;
  isStreaming?: boolean;
}

export function StreamingText({ content, isStreaming }: Props) {
  const rendered = useMemo(() => {
    if (!content) return null;
    return renderMarkdown(content);
  }, [content]);

  return (
    <div style={{ lineHeight: 1.7 }}>
      {rendered}
      {isStreaming && <span className="streaming-cursor">▊</span>}
      <style>{`
        .streaming-cursor {
          animation: blink 0.8s infinite;
          color: #1677ff;
          font-weight: bold;
        }
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
      `}</style>
    </div>
  );
}

function renderMarkdown(text: string) {
  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];
  let listItems: string[] = [];
  let inCodeBlock = false;
  let codeContent = '';
  let codeKey = 0;

  const flushList = () => {
    if (listItems.length > 0) {
      elements.push(
        <ul key={`list-${elements.length}`} style={{ margin: '4px 0', paddingLeft: 20 }}>
          {listItems.map((item, i) => (
            <li key={i}><Text>{item}</Text></li>
          ))}
        </ul>
      );
      listItems = [];
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (line.startsWith('```')) {
      if (inCodeBlock) {
        elements.push(
          <pre key={`code-${codeKey++}`} style={{
            background: '#f5f5f5', padding: 12, borderRadius: 6,
            fontSize: 13, overflow: 'auto', margin: '8px 0',
          }}>
            <code>{codeContent}</code>
          </pre>
        );
        codeContent = '';
        inCodeBlock = false;
      } else {
        flushList();
        inCodeBlock = true;
      }
      continue;
    }

    if (inCodeBlock) {
      codeContent += (codeContent ? '\n' : '') + line;
      continue;
    }

    if (line.startsWith('# ')) {
      flushList();
      elements.push(<Title key={i} level={4} style={{ margin: '8px 0 4px' }}>{line.slice(2)}</Title>);
    } else if (line.startsWith('## ')) {
      flushList();
      elements.push(<Title key={i} level={5} style={{ margin: '8px 0 4px' }}>{line.slice(3)}</Title>);
    } else if (line.startsWith('- ') || line.startsWith('* ')) {
      listItems.push(line.slice(2));
    } else if (/^\d+\.\s/.test(line)) {
      listItems.push(line.replace(/^\d+\.\s/, ''));
    } else if (line.startsWith('**') && line.endsWith('**')) {
      flushList();
      elements.push(<Text key={i} strong style={{ display: 'block', margin: '4px 0' }}>{line.slice(2, -2)}</Text>);
    } else if (line.trim() === '') {
      flushList();
    } else {
      flushList();
      const rendered = renderInline(line);
      elements.push(<Paragraph key={i} style={{ margin: '2px 0' }}>{rendered}</Paragraph>);
    }
  }

  flushList();
  return elements;
}

function renderInline(text: string): React.ReactNode {
  const parts: React.ReactNode[] = [];
  const regex = /\*\*(.+?)\*\*|`(.+?)`/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    if (match[1]) {
      parts.push(<Text key={match.index} strong>{match[1]}</Text>);
    } else if (match[2]) {
      parts.push(<Text key={match.index} code>{match[2]}</Text>);
    }
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts.length === 1 ? parts[0] : <>{parts}</>;
}
