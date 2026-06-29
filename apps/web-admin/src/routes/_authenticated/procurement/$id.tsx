import { createFileRoute, useNavigate } from '@tanstack/react-router'
import {
  Descriptions, Card, Table, Button, Space, Spin, Row, Col, App,
} from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import { useApiQuery } from '@lg/react-hooks'
import { PageHeader, StatusBadge } from '@/components/common'
import { WorkflowSection } from '@/components/workflow/WorkflowSection'
import { procurementStatusColors } from '@/constants'
import { useFormat } from '@/hooks/useFormat'
import { procurementStatusLabels } from '@lg/core'

interface ProcurementDetail {
  id: number
  procurement_no: string
  supplier_id: number
  supplier_name?: string
  order_id?: number
  order_no?: string
  status: string
  total_amount: number
  currency: string
  expected_date?: string
  notes?: string
  created_by: number
  creator_name?: string
  approved_by?: number
  approver_name?: string
  approved_at?: string
  created_at: string
  updated_at: string
  line_items: ProcLineItem[]
}

interface ProcLineItem {
  id: number
  product_name: string
  specification?: string
  unit?: string
  quantity: number
  unit_price: number
  amount: number
  received_quantity: number
  notes?: string
}

export const Route = createFileRoute('/_authenticated/procurement/$id')({
  component: ProcurementDetailPage,
})

function ProcurementDetailPage() {
  const { id } = Route.useParams()
  const navigate = useNavigate()
  const { fmtDate, fmtMoney, fmtStatus } = useFormat()

  const { data: procurement, isLoading } = useApiQuery<ProcurementDetail>(
    ['procurements', id], `/procurements/${id}`,
  )

  if (isLoading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />
  if (!procurement) return <div>采购单不存在</div>

  const lineItemColumns = [
    { title: '产品', dataIndex: 'product_name', key: 'product_name' },
    { title: '规格', dataIndex: 'specification', key: 'specification' },
    { title: '单位', dataIndex: 'unit', key: 'unit', width: 60 },
    { title: '数量', dataIndex: 'quantity', key: 'quantity', width: 80, align: 'right' as const },
    { title: '单价', dataIndex: 'unit_price', key: 'unit_price', width: 100, align: 'right' as const, render: (v: number) => fmtMoney(v, procurement.currency) },
    { title: '金额', dataIndex: 'amount', key: 'amount', width: 120, align: 'right' as const, render: (v: number) => fmtMoney(v, procurement.currency) },
    { title: '已收货', dataIndex: 'received_quantity', key: 'received_quantity', width: 80, align: 'right' as const },
    { title: '备注', dataIndex: 'notes', key: 'notes' },
  ]

  return (
    <div>
      <PageHeader
        title={`采购详情 - ${procurement.procurement_no}`}
        extra={
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate({ to: '/procurement' })}>
            返回列表
          </Button>
        }
      />

      <Row gutter={16}>
        <Col xs={24} lg={16}>
          <Card>
            <Descriptions bordered column={{ xs: 1, sm: 2, lg: 3 }}>
              <Descriptions.Item label="采购编号">{procurement.procurement_no}</Descriptions.Item>
              <Descriptions.Item label="供应商">{procurement.supplier_name ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="关联订单">{procurement.order_no ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <StatusBadge label={fmtStatus(procurement.status, 'procurement')} colorMap={procurementStatusColors} status={procurement.status} />
              </Descriptions.Item>
              <Descriptions.Item label="币种">{procurement.currency}</Descriptions.Item>
              <Descriptions.Item label="总金额">{fmtMoney(procurement.total_amount, procurement.currency)}</Descriptions.Item>
              <Descriptions.Item label="期望交付">{fmtDate(procurement.expected_date)}</Descriptions.Item>
              <Descriptions.Item label="创建人">{procurement.creator_name ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="审批人">{procurement.approver_name ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{fmtDate(procurement.created_at)}</Descriptions.Item>
              <Descriptions.Item label="更新时间">{fmtDate(procurement.updated_at)}</Descriptions.Item>
              <Descriptions.Item label="备注" span={3}>{procurement.notes ?? '-'}</Descriptions.Item>
            </Descriptions>
          </Card>

          {procurement.line_items && procurement.line_items.length > 0 && (
            <Card title="采购明细" style={{ marginTop: 16 }}>
              <Table<ProcLineItem>
                rowKey="id"
                columns={lineItemColumns}
                dataSource={procurement.line_items}
                pagination={false}
                summary={(data) => {
                  const total = data.reduce((sum, item) => sum + item.amount, 0)
                  return (
                    <Table.Summary.Row>
                      <Table.Summary.Cell index={0} colSpan={5} align="right"><strong>合计</strong></Table.Summary.Cell>
                      <Table.Summary.Cell index={5} align="right"><strong>{fmtMoney(total, procurement.currency)}</strong></Table.Summary.Cell>
                      <Table.Summary.Cell index={6} />
                      <Table.Summary.Cell index={7} />
                    </Table.Summary.Row>
                  )
                }}
              />
            </Card>
          )}

          {procurement.status !== 'DRAFT' && procurement.order_id && (
            <WorkflowSection orderId={procurement.order_id} />
          )}
        </Col>

        <Col xs={24} lg={8}>
          <Card title="快捷操作">
            <Space direction="vertical" style={{ width: '100%' }}>
              {procurement.order_id && (
                <Button block onClick={() => navigate({ to: `/orders/${procurement.order_id}` as any })}>
                  查看关联订单
                </Button>
              )}
              <Button block onClick={() => navigate({ to: '/procurement' })}>
                返回采购列表
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
