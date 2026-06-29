import { createFileRoute } from '@tanstack/react-router'
import { List, Button, Tag, Badge, Space, message, Tabs } from 'antd'
import { CheckOutlined, DeleteOutlined } from '@ant-design/icons'
import { useApiQuery } from '@lg/react-hooks'
import { PageHeader } from '@/components/common'
import { useFormat } from '@/hooks/useFormat'
import { http } from '@lg/api-client'
import type { Notification, PageResponse } from '@lg/api-client'
import { useQueryClient } from '@tanstack/react-query'

export const Route = createFileRoute('/_authenticated/messages')({
  component: MessagesPage,
})

const typeColors: Record<string, string> = {
  APPROVAL: 'orange', OVERDUE: 'red', PAYMENT: 'green', SYSTEM: 'blue', INFO: 'default',
}
const typeLabels: Record<string, string> = {
  APPROVAL: '审批', OVERDUE: '逾期', PAYMENT: '付款', SYSTEM: '系统', INFO: '通知',
}

function MessagesPage() {
  const { fmtDate } = useFormat()
  const queryClient = useQueryClient()

  const { data, isLoading } = useApiQuery<PageResponse<Notification>>(
    ['notifications'], '/notifications', { size: 50 }
  )
  const { data: unread } = useApiQuery<{ count: number }>(
    ['notifications', 'unread'], '/notifications/unread-count'
  )

  const handleRead = async (id: number) => {
    await http.put(`/notifications/${id}/read`)
    queryClient.invalidateQueries({ queryKey: ['notifications'] })
  }
  const handleReadAll = async () => {
    await http.put('/notifications/read-all')
    message.success('全部已读')
    queryClient.invalidateQueries({ queryKey: ['notifications'] })
  }
  const handleDelete = async (id: number) => {
    await http.delete(`/notifications/${id}`)
    queryClient.invalidateQueries({ queryKey: ['notifications'] })
  }

  return (
    <div>
      <PageHeader
        title="消息中心"
        subtitle={unread?.count ? `${unread.count} 条未读` : undefined}
        extra={<Button onClick={handleReadAll} icon={<CheckOutlined />}>全部已读</Button>}
      />
      <List
        loading={isLoading}
        dataSource={data?.items ?? []}
        renderItem={(item: Notification) => (
          <List.Item
            actions={[
              !item.is_read && <Button type="link" size="small" onClick={() => handleRead(item.id)}>标记已读</Button>,
              <Button type="link" size="small" danger onClick={() => handleDelete(item.id)} icon={<DeleteOutlined />} />,
            ].filter(Boolean)}
          >
            <List.Item.Meta
              title={
                <Space>
                  {!item.is_read && <Badge status="processing" />}
                  <Tag color={typeColors[item.type]}>{typeLabels[item.type] ?? item.type}</Tag>
                  {item.title}
                </Space>
              }
              description={
                <div>
                  <div>{item.content}</div>
                  <span style={{ fontSize: 12, color: '#999' }}>{fmtDate(item.created_at)}</span>
                </div>
              }
            />
          </List.Item>
        )}
      />
    </div>
  )
}
