import { useEffect } from 'react'
import { Modal, Form, Input, Select, Divider, Typography } from 'antd'
import { useApiQuery } from '@lg/react-hooks'
import type { Node } from '@xyflow/react'
import type { PageResponse } from '@lg/api-client'
import { BUSINESS_NODE_TRIGGERS, BUSINESS_NODE_TYPES } from './types'

interface UserItem {
  id: number
  real_name: string
  role: string
}

interface NodeEditDialogProps {
  node: Node | null
  open: boolean
  onClose: () => void
  onSave: (nodeId: string, data: Record<string, unknown>) => void
}

const TRIGGER_ENTITIES = [
  { value: 'order', label: '订单' },
  { value: 'procurement', label: '采购单' },
  { value: 'contract', label: '合同' },
  { value: 'settlement', label: '结算单' },
]

const TRIGGER_STATUSES: Record<string, { value: string; label: string }[]> = {
  order: [
    { value: 'IN_PROGRESS', label: '进行中' },
    { value: 'COMPLETED', label: '已完成' },
    { value: 'CANCELLED', label: '已取消' },
  ],
  procurement: [
    { value: 'PENDING_APPROVAL', label: '待审批' },
    { value: 'APPROVED', label: '已审批' },
    { value: 'ORDERED', label: '已下单' },
    { value: 'RECEIVED', label: '已收货' },
  ],
  contract: [
    { value: 'EFFECTIVE', label: '已生效' },
    { value: 'EXECUTING', label: '执行中' },
    { value: 'COMPLETED', label: '已完成' },
  ],
  settlement: [
    { value: 'APPROVED', label: '已审批' },
    { value: 'REJECTED', label: '已驳回' },
  ],
}

export function NodeEditDialog({ node, open, onClose, onSave }: NodeEditDialogProps) {
  const [form] = Form.useForm()
  const triggerEntity = Form.useWatch(['config', 'trigger', 'entity'], form)

  const { data: usersData } = useApiQuery<PageResponse<UserItem>>(
    ['users', 'list'],
    '/users',
    { size: 100 },
  )

  useEffect(() => {
    if (node && open) {
      form.setFieldsValue({
        label: node.data.label,
        assignee: node.data.assignee,
        notes: node.data.notes,
        expression: node.data.expression,
        config: node.data.config ?? {},
      })
    }
  }, [node, open, form])

  const handleOk = () => {
    const values = form.getFieldsValue()
    if (node) {
      const config = values.config ?? {}
      if (config.trigger?.entity && config.trigger?.status) {
        // keep trigger
      } else {
        delete config.trigger
      }
      if (config.action?.type && config.action?.status) {
        // keep action
      } else {
        delete config.action
      }
      onSave(node.id, { ...values, config })
    }
    onClose()
  }

  const nodeType = (node?.data.nodeType as string) ?? 'custom'
  const users = usersData?.items ?? []
  const isBusiness = (BUSINESS_NODE_TYPES as readonly string[]).includes(nodeType)
  const defaultTrigger = BUSINESS_NODE_TRIGGERS[nodeType]

  return (
    <Modal title="编辑节点" open={open} onCancel={onClose} onOk={handleOk} destroyOnClose width={520}>
      <Form form={form} layout="vertical">
        <Form.Item name="label" label="节点名称" rules={[{ required: true }]}>
          <Input />
        </Form.Item>

        {isBusiness && defaultTrigger && (
          <div style={{ background: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: 6, padding: '8px 12px', marginBottom: 16, fontSize: 12 }}>
            <strong>自动触发：</strong>当 {TRIGGER_ENTITIES.find((e) => e.value === defaultTrigger.entity)?.label ?? defaultTrigger.entity} 状态变为 {TRIGGER_STATUSES[defaultTrigger.entity]?.find((s) => s.value === defaultTrigger.status)?.label ?? defaultTrigger.status} 时自动完成
          </div>
        )}

        {isBusiness && !defaultTrigger && (
          <div style={{ background: '#fffbe6', border: '1px solid #ffe58f', borderRadius: 6, padding: '8px 12px', marginBottom: 16, fontSize: 12 }}>
            <strong>手动节点：</strong>需要操作人员手动标记完成
          </div>
        )}

        {['approval', 'custom'].includes(nodeType) && (
          <Form.Item name="assignee" label="负责人">
            <Select
              placeholder="选择负责人"
              allowClear
              showSearch
              optionFilterProp="label"
              options={users.map((u) => ({
                value: u.real_name,
                label: `${u.real_name} (${u.role})`,
              }))}
            />
          </Form.Item>
        )}

        {nodeType === 'condition' && (
          <Form.Item name="expression" label="条件表达式">
            <Input.TextArea rows={3} placeholder="e.g. amount > 10000" />
          </Form.Item>
        )}

        <Form.Item name="notes" label="备注">
          <Input.TextArea rows={2} />
        </Form.Item>

        {['approval', 'custom'].includes(nodeType) && (
          <>
            <Divider />
            <Typography.Text type="secondary" style={{ fontSize: 12, marginBottom: 8, display: 'block' }}>
              业务联动配置（可选）
            </Typography.Text>

            <Form.Item label="自动完成触发条件" style={{ marginBottom: 8 }}>
              <Input.Group compact>
                <Form.Item name={['config', 'trigger', 'entity']} noStyle>
                  <Select placeholder="业务实体" style={{ width: '50%' }} allowClear options={TRIGGER_ENTITIES} />
                </Form.Item>
                <Form.Item name={['config', 'trigger', 'status']} noStyle>
                  <Select
                    placeholder="目标状态"
                    style={{ width: '50%' }}
                    allowClear
                    options={TRIGGER_STATUSES[triggerEntity] ?? []}
                  />
                </Form.Item>
              </Input.Group>
            </Form.Item>

            <Form.Item label="完成后触发动作" style={{ marginBottom: 8 }}>
              <Input.Group compact>
                <Form.Item name={['config', 'action', 'type']} noStyle initialValue="change_status">
                  <Select style={{ width: '35%' }} options={[{ value: 'change_status', label: '变更状态' }, { value: 'notify', label: '发送通知' }]} />
                </Form.Item>
                <Form.Item name={['config', 'action', 'entity']} noStyle>
                  <Select placeholder="实体" style={{ width: '30%' }} allowClear options={[{ value: 'order', label: '订单' }]} />
                </Form.Item>
                <Form.Item name={['config', 'action', 'status']} noStyle>
                  <Select
                    placeholder="状态"
                    style={{ width: '35%' }}
                    allowClear
                    options={[
                      { value: 'COMPLETED', label: '已完成' },
                      { value: 'CANCELLED', label: '已取消' },
                    ]}
                  />
                </Form.Item>
              </Input.Group>
            </Form.Item>
          </>
        )}
      </Form>
    </Modal>
  )
}
