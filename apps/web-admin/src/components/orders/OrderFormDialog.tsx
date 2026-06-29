import { useState, useEffect } from 'react'
import { Modal, Form, Input, Select, DatePicker, Row, Col, App } from 'antd'
import { orderApi, customerApi } from '@lg/api-client'
import type { Customer, Vessel, Order } from '@lg/api-client'
import { useQueryClient } from '@tanstack/react-query'
import { projectTypeOptions, currencyOptions } from '@/constants'

interface Props {
  open: boolean
  onClose: () => void
  editOrder?: Order | null
}

export function OrderFormDialog({ open, onClose, editOrder }: Props) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [customers, setCustomers] = useState<Customer[]>([])
  const [vessels, setVessels] = useState<Vessel[]>([])
  const queryClient = useQueryClient()
  const { message } = App.useApp()

  useEffect(() => {
    if (open) {
      customerApi.list({ size: 500 }).then((res) => setCustomers(res.items)).catch(() => {})
      if (editOrder) {
        form.setFieldsValue({
          customer_id: editOrder.customer_id,
          vessel_id: editOrder.vessel_id,
          project_type: editOrder.project_type,
          currency: editOrder.currency,
          notes: editOrder.notes,
        })
        if (editOrder.customer_id) {
          customerApi.listVessels(editOrder.customer_id).then(setVessels).catch(() => {})
        }
      } else {
        form.resetFields()
        setVessels([])
      }
    }
  }, [open, editOrder, form])

  const handleCustomerChange = async (customerId: number) => {
    form.setFieldValue('vessel_id', undefined)
    if (customerId) {
      try {
        const v = await customerApi.listVessels(customerId)
        setVessels(v)
      } catch { setVessels([]) }
    } else {
      setVessels([])
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)
      const data = {
        customer_id: values.customer_id,
        vessel_id: values.vessel_id || undefined,
        project_type: values.project_type,
        currency: values.currency,
        delivery_date: values.delivery_date?.format('YYYY-MM-DD'),
        notes: values.notes || undefined,
      }
      if (editOrder) {
        await orderApi.update(editOrder.id, data)
        message.success('更新成功')
      } else {
        await orderApi.create(data)
        message.success('创建成功')
      }
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      onClose()
    } catch (e) {
      if (e instanceof Error) message.error(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={editOrder ? '编辑订单' : '新建订单'}
      open={open}
      onCancel={onClose}
      onOk={handleSubmit}
      confirmLoading={loading}
      width={720}
      destroyOnClose
    >
      <Form form={form} layout="vertical" initialValues={{ currency: 'CNY', project_type: 'SPARE_PARTS' }}>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="customer_id" label="客户" rules={[{ required: true, message: '请选择客户' }]}>
              <Select
                placeholder="选择客户"
                showSearch
                filterOption={(input, option) => (option?.label as string ?? '').toLowerCase().includes(input.toLowerCase())}
                options={customers.map((c) => ({ label: c.name, value: c.id }))}
                onChange={handleCustomerChange}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="vessel_id" label="船舶">
              <Select
                placeholder="选择船舶"
                allowClear
                options={vessels.map((v) => ({ label: v.name, value: v.id }))}
              />
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="project_type" label="项目类型" rules={[{ required: true }]}>
              <Select options={projectTypeOptions} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="currency" label="币种" rules={[{ required: true }]}>
              <Select options={currencyOptions} />
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="delivery_date" label="交货日期">
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="notes" label="备注">
          <Input.TextArea rows={3} />
        </Form.Item>
      </Form>
    </Modal>
  )
}
