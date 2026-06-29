import type { ReactNode } from 'react'
import { Form, Button, Space } from 'antd'
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons'

interface SearchFormProps {
  onSearch: (values: Record<string, unknown>) => void
  onReset?: () => void
  children: ReactNode
  loading?: boolean
}

export function SearchForm({ onSearch, onReset, children, loading }: SearchFormProps) {
  const [form] = Form.useForm()

  const handleReset = () => {
    form.resetFields()
    onReset?.()
  }

  return (
    <Form
      form={form}
      layout="inline"
      onFinish={onSearch}
      style={{ marginBottom: 16, flexWrap: 'wrap', gap: 8 }}
    >
      {children}
      <Form.Item>
        <Space>
          <Button type="primary" htmlType="submit" icon={<SearchOutlined />} loading={loading}>
            搜索
          </Button>
          <Button icon={<ReloadOutlined />} onClick={handleReset}>
            重置
          </Button>
        </Space>
      </Form.Item>
    </Form>
  )
}
