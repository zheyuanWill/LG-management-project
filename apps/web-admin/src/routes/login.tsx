import { useState } from 'react'
import { createFileRoute, useNavigate, useSearch } from '@tanstack/react-router'
import { Form, Input, Button, message, Typography, Space, Card } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useAuthStore } from '@lg/react-hooks'

export const Route = createFileRoute('/login')({
  component: LoginPage,
})

const quickAccounts = [
  { username: 'owner', password: '123456', label: '老板' },
  { username: 'pm', password: '123456', label: '项目经理' },
  { username: 'proc', password: '123456', label: '采购' },
  { username: 'fin', password: '123456', label: '财务' },
  { username: 'ops', password: '123456', label: '仓库' },
]

function LoginPage() {
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()
  const navigate = useNavigate()
  const login = useAuthStore((s) => s.login)
  const search = useSearch({ strict: false }) as { redirect?: string }
  const isDev = import.meta.env.DEV

  const handleLogin = async (values: { username: string; password: string }) => {
    try {
      setLoading(true)
      await login(values.username, values.password)
      message.success('登录成功')
      navigate({ to: search.redirect || '/dashboard' })
    } catch (err) {
      message.error(err instanceof Error ? err.message : '登录失败')
    } finally {
      setLoading(false)
    }
  }

  const quickLogin = (account: { username: string; password: string }) => {
    form.setFieldsValue(account)
    form.submit()
  }

  return (
    <div style={{
      display: 'flex',
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    }}>
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#fff',
        padding: 48,
      }}>
        <div>
          <Typography.Title level={1} style={{ color: '#fff', marginBottom: 12 }}>
            LG Management
          </Typography.Title>
          <Typography.Paragraph style={{ color: 'rgba(255,255,255,0.85)', fontSize: 18 }}>
            修船项目以销定采的一体化项目管理 & 供应链系统
          </Typography.Paragraph>
        </div>
      </div>

      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 48,
        minWidth: 420,
        background: 'rgba(255,255,255,0.95)',
        borderRadius: '24px 0 0 24px',
      }}>
        <Card bordered={false} style={{ width: 360, boxShadow: 'none' }}>
          <Typography.Title level={3} style={{ textAlign: 'center', marginBottom: 32 }}>
            欢迎登录
          </Typography.Title>

          <Form form={form} onFinish={handleLogin} size="large" layout="vertical">
            <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
              <Input prefix={<UserOutlined />} placeholder="用户名" />
            </Form.Item>
            <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
              <Input.Password prefix={<LockOutlined />} placeholder="密码" />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block>
                登录
              </Button>
            </Form.Item>
          </Form>

          {isDev && (
            <div style={{ textAlign: 'center' }}>
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                快速登录（演示账号，仅开发环境）
              </Typography.Text>
              <Space wrap style={{ marginTop: 8, justifyContent: 'center', width: '100%' }}>
                {quickAccounts.map((acc) => (
                  <Button key={acc.username} size="small" onClick={() => quickLogin(acc)}>
                    {acc.label}
                  </Button>
                ))}
              </Space>
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
