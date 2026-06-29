import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { Result, Button } from 'antd'

export const Route = createFileRoute('/notFound')({
  component: NotFoundPage,
})

function NotFoundPage() {
  const navigate = useNavigate()
  return (
    <Result
      status="404"
      title="404"
      subTitle="抱歉，您访问的页面不存在"
      extra={
        <Button type="primary" onClick={() => navigate({ to: '/dashboard' })}>
          返回首页
        </Button>
      }
    />
  )
}
