import { useState } from 'react';
import { Card, Tag, Typography, Space, Collapse } from 'antd';
import { LoadingOutlined, CheckCircleOutlined, ToolOutlined } from '@ant-design/icons';
import type { ToolCallInfo } from './types';

const { Text, Paragraph } = Typography;

const TOOL_LABELS: Record<string, string> = {
  search_orders: '搜索订单',
  get_project_detail: '获取项目详情',
  calculate_cost: '成本计算',
  generate_report: '生成报告',
};

interface Props {
  toolCall: ToolCallInfo;
}

export function ToolCallCard({ toolCall }: Props) {
  const [expanded, setExpanded] = useState(false);
  const label = TOOL_LABELS[toolCall.tool] || toolCall.tool;
  const isRunning = toolCall.status === 'running';

  return (
    <Card
      size="small"
      style={{
        marginBottom: 8,
        borderLeft: `3px solid ${isRunning ? '#1677ff' : '#52c41a'}`,
        background: '#fafafa',
      }}
    >
      <Space align="center" style={{ marginBottom: expanded ? 8 : 0 }}>
        {isRunning ? (
          <LoadingOutlined style={{ color: '#1677ff' }} />
        ) : (
          <CheckCircleOutlined style={{ color: '#52c41a' }} />
        )}
        <ToolOutlined />
        <Text strong>{label}</Text>
        <Tag color={isRunning ? 'processing' : 'success'}>
          {isRunning ? '执行中...' : '完成'}
        </Tag>
        {!isRunning && toolCall.output && (
          <Text
            type="secondary"
            style={{ cursor: 'pointer', fontSize: 12 }}
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? '收起' : '展开详情'}
          </Text>
        )}
      </Space>

      {expanded && toolCall.output && (
        <Collapse
          defaultActiveKey={['params', 'result']}
          size="small"
          items={[
            {
              key: 'params',
              label: '参数',
              children: (
                <pre style={{ fontSize: 12, margin: 0, whiteSpace: 'pre-wrap' }}>
                  {JSON.stringify(toolCall.input, null, 2)}
                </pre>
              ),
            },
            {
              key: 'result',
              label: '结果',
              children: (
                <pre style={{ fontSize: 12, margin: 0, whiteSpace: 'pre-wrap', maxHeight: 200, overflow: 'auto' }}>
                  {toolCall.output}
                </pre>
              ),
            },
          ]}
        />
      )}
    </Card>
  );
}
