import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { Card, Row, Col, Button, Select, Table, Typography, Empty } from 'antd'
import { DownloadOutlined, FileZipOutlined, FileTextOutlined } from '@ant-design/icons'
import { PageHeader } from '@/components/common'
import { useFormat } from '@/hooks/useFormat'

const { Title, Text } = Typography
const { Option } = Select

export const Route = createFileRoute('/_authenticated/ship-repair/iso-archive')({
  component: ISOArchivePage,
})

function ISOArchivePage() {
  const { fmtDate } = useFormat()
  const [selectedOrder, setSelectedOrder] = useState<string>()

  const archiveItems = [
    { name: '客户回访记录', type: 'document' },
    { name: '船东背调记录', type: 'document' },
    { name: '船厂询价记录', type: 'document' },
    { name: '船厂报价记录', type: 'document' },
    { name: '修船计划版本', type: 'document' },
    { name: 'AI拆解任务记录', type: 'document' },
    { name: '日报记录', type: 'document' },
    { name: '关键照片证据', type: 'image' },
    { name: '异常记录', type: 'document' },
    { name: 'NCR记录', type: 'document' },
    { name: '缺备件风险单', type: 'document' },
    { name: '供应商反馈记录', type: 'document' },
    { name: '采购单', type: 'document' },
    { name: '合同记录', type: 'document' },
    { name: '回款记录', type: 'document' },
    { name: '项目结项记录', type: 'document' },
    { name: '审批记录', type: 'document' },
    { name: '操作日志', type: 'document' },
    { name: '项目复盘记录', type: 'document' },
  ]

  return (
    <div>
      <PageHeader title="ISO归档包" />

      <div style={{ marginBottom: 24 }}>
        <Select
          placeholder="选择项目"
          style={{ width: 400 }}
          allowClear
          onChange={setSelectedOrder}
        >
          {/* 这里应该有项目列表 */}
        </Select>
        {selectedOrder && (
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            style={{ marginLeft: 16 }}
          >
            导出归档包
          </Button>
        )}
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title="归档内容清单">
            {selectedOrder ? (
              <Table
                rowKey="name"
                pagination={false}
                dataSource={archiveItems}
                columns={[
                  {
                    title: '文件类型',
                    dataIndex: 'type',
                    key: 'type',
                    width: 100,
                    render: (type: string) => (
                      type === 'image'
                        ? <FileTextOutlined style={{ color: '#1890ff' }} />
                        : <FileZipOutlined style={{ color: '#1890ff' }} />
                    ),
                  },
                  { title: '文件名', dataIndex: 'name', key: 'name' },
                  {
                    title: '操作',
                    key: 'actions',
                    width: 100,
                    render: () => (
                      <Button type="link" size="small" icon={<DownloadOutlined />}>
                        预览
                      </Button>
                    ),
                  },
                ]}
              />
            ) : (
              <Empty description="请先选择项目" />
            )}
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="ISO审核要点">
            <ul>
              <li><Text>过程受控</Text></li>
              <li><Text>记录可追溯</Text></li>
              <li><Text>问题闭环</Text></li>
              <li><Text>责任明确</Text></li>
              <li><Text>文件版本受控</Text></li>
              <li><Text>持续改进</Text></li>
            </ul>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
