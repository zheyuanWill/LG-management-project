import { Avatar, Space, Typography } from 'antd';
import { UserOutlined, RobotOutlined } from '@ant-design/icons';
import { StreamingText } from './StreamingText';
import { ToolCallCard } from './ToolCallCard';
import type { ChatMessage } from './types';

const { Text } = Typography;

interface Props {
  message: ChatMessage;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user';

  return (
    <div style={{
      display: 'flex',
      flexDirection: isUser ? 'row-reverse' : 'row',
      gap: 8,
      marginBottom: 16,
      alignItems: 'flex-start',
    }}>
      <Avatar
        size={32}
        icon={isUser ? <UserOutlined /> : <RobotOutlined />}
        style={{
          backgroundColor: isUser ? '#1677ff' : '#52c41a',
          flexShrink: 0,
        }}
      />
      <div style={{
        maxWidth: '80%',
        background: isUser ? '#1677ff' : '#f5f5f5',
        color: isUser ? '#fff' : '#333',
        padding: '8px 14px',
        borderRadius: isUser ? '12px 12px 4px 12px' : '12px 12px 12px 4px',
      }}>
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div style={{ marginBottom: 8 }}>
            {message.toolCalls.map((tc, idx) => (
              <ToolCallCard key={idx} toolCall={tc} />
            ))}
          </div>
        )}

        {message.content ? (
          isUser ? (
            <Text style={{ color: '#fff', whiteSpace: 'pre-wrap' }}>{message.content}</Text>
          ) : (
            <StreamingText content={message.content} isStreaming={message.isStreaming} />
          )
        ) : message.isStreaming ? (
          <StreamingText content="" isStreaming />
        ) : null}

        <div style={{ textAlign: 'right', marginTop: 4 }}>
          <Text type="secondary" style={{ fontSize: 11, color: isUser ? 'rgba(255,255,255,0.6)' : undefined }}>
            {new Date(message.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
          </Text>
        </div>
      </div>
    </div>
  );
}
