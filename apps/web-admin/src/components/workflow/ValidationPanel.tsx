import { Alert, List, Typography, Space, Tag } from 'antd'
import type { WorkflowValidationResult } from '@lg/api-client'

interface ValidationPanelProps {
  result: WorkflowValidationResult | null
  loading?: boolean
}

export function ValidationPanel({ result, loading }: ValidationPanelProps) {
  if (!result) return null

  return (
    <div style={{ marginTop: 12 }}>
      {result.valid ? (
        <Alert type="success" message="工作流定义验证通过" showIcon />
      ) : (
        <Alert type="error" message={`验证失败：${result.errors.length} 个错误`} showIcon />
      )}
      {result.errors.length > 0 && (
        <List
          size="small"
          style={{ marginTop: 8 }}
          dataSource={result.errors}
          renderItem={(item) => (
            <List.Item>
              <Space>
                <Tag color="error">错误</Tag>
                <Typography.Text>{item.message}</Typography.Text>
              </Space>
            </List.Item>
          )}
        />
      )}
      {result.warnings.length > 0 && (
        <List
          size="small"
          style={{ marginTop: 8 }}
          dataSource={result.warnings}
          renderItem={(item) => (
            <List.Item>
              <Space>
                <Tag color="warning">警告</Tag>
                <Typography.Text>{item.message}</Typography.Text>
              </Space>
            </List.Item>
          )}
        />
      )}
    </div>
  )
}
