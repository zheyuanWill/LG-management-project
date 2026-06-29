import { useState } from 'react'
import { Card, Modal, Select, App } from 'antd'
import { useApiQuery } from '@lg/react-hooks'
import { workflowApi } from '@lg/api-client'
import { WorkflowTracker } from './WorkflowTracker'
import type { WorkflowTemplate, PageResponse } from '@lg/api-client'

interface Props {
  orderId: number
  title?: string
}

export function WorkflowSection({ orderId, title = '工作流追踪' }: Props) {
  const [createOpen, setCreateOpen] = useState(false)
  const [selectedTemplateId, setSelectedTemplateId] = useState<number | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const { message } = App.useApp()

  const { data: templatesData } = useApiQuery<PageResponse<WorkflowTemplate>>(
    ['workflow', 'templates', 'active'],
    `/workflows/templates`,
    { is_active: true, size: 50 },
  )

  const handleCreate = async () => {
    if (!selectedTemplateId) {
      message.warning('请选择一个工作流模板')
      return
    }
    try {
      await workflowApi.createInstance({
        template_id: selectedTemplateId,
        order_id: orderId,
      })
      message.success('工作流实例已创建')
      setCreateOpen(false)
      setSelectedTemplateId(null)
      setRefreshKey((k) => k + 1)
    } catch (err) {
      message.error(err instanceof Error ? err.message : '创建失败')
    }
  }

  return (
    <Card title={title} style={{ marginTop: 16 }}>
      <WorkflowTracker
        key={refreshKey}
        orderId={orderId}
        onCreateInstance={() => setCreateOpen(true)}
      />
      <Modal
        title="创建工作流实例"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={handleCreate}
      >
        <Select
          placeholder="选择工作流模板"
          style={{ width: '100%' }}
          value={selectedTemplateId}
          onChange={setSelectedTemplateId}
          options={(templatesData?.items ?? []).map((t) => ({
            value: t.id,
            label: `${t.name}${t.project_type ? ` (${t.project_type})` : ''}`,
          }))}
        />
      </Modal>
    </Card>
  )
}
