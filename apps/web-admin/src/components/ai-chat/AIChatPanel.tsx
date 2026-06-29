import { useEffect, useRef, useMemo } from 'react';
import { Typography, Button, Empty, Spin } from 'antd';
import { ClearOutlined, RobotOutlined } from '@ant-design/icons';
import { useChatStream } from './useChatStream';
import { MessageBubble } from './MessageBubble';
import { MultiModalInput } from './MultiModalInput';

const { Text } = Typography;

interface Props {
  baseUrl: string;
  style?: React.CSSProperties;
}

export function AIChatPanel({ baseUrl, style }: Props) {
  const { messages, isStreaming, sendMessage, stopStream, clearMessages } = useChatStream(baseUrl);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const isEmpty = messages.length === 0;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: '#fff',
        borderRadius: 8,
        overflow: 'hidden',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        ...style,
      }}
    >
      {/* Header */}
      <div style={{
        padding: '10px 16px',
        borderBottom: '1px solid #f0f0f0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'linear-gradient(135deg, #1677ff 0%, #4096ff 100%)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <RobotOutlined style={{ fontSize: 18, color: '#fff' }} />
          <Text strong style={{ color: '#fff', fontSize: 15 }}>AI 助手</Text>
        </div>
        <Button
          type="text"
          size="small"
          icon={<ClearOutlined />}
          onClick={clearMessages}
          disabled={isStreaming || isEmpty}
          style={{ color: 'rgba(255,255,255,0.8)' }}
        >
          清空
        </Button>
      </div>

      {/* Messages */}
      <div style={{
        flex: 1,
        overflow: 'auto',
        padding: '16px 12px',
        background: '#fafbfc',
      }}>
        {isEmpty ? (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            gap: 16,
          }}>
            <RobotOutlined style={{ fontSize: 48, color: '#bfbfbf' }} />
            <Empty
              description={
                <div>
                  <Text type="secondary">你好！我是 LG-Management AI 助手</Text>
                  <br />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    可以帮你搜索订单、分析成本、生成报告等
                  </Text>
                </div>
              }
            />
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center' }}>
              {QUICK_PROMPTS.map((p) => (
                <Button
                  key={p}
                  size="small"
                  onClick={() => sendMessage(p)}
                  style={{ borderRadius: 16 }}
                >
                  {p}
                </Button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <MultiModalInput
        onSend={sendMessage}
        onStop={stopStream}
        isStreaming={isStreaming}
      />
    </div>
  );
}

const QUICK_PROMPTS = [
  '查看最近的订单',
  '帮我分析项目成本',
  '本月有哪些待处理项目？',
  '生成一份项目汇总报告',
];
