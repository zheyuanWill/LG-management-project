import { useMemo, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { App, Button, Card, Form, InputNumber, Input, Select, Space, Upload } from 'antd'
import type { UploadFile } from 'antd'
import { UploadOutlined } from '@ant-design/icons'
import { http } from '@lg/api-client'
import type { FileAttachment, PageResponse, Quote } from '@lg/api-client'
import { useApiQuery } from '@lg/react-hooks'
import { PageHeader } from '@/components/common'

export const Route = createFileRoute('/_authenticated/quotes/excel')({
  component: QuoteExcelPage,
})

type FileState = UploadFile & { originFileObj?: File }

function pickFirstFile(list: UploadFile[]) {
  return list?.[0] as FileState | undefined
}

function QuoteExcelPage() {
  const { message } = App.useApp()
  const [form] = Form.useForm()
  const [result, setResult] = useState<FileAttachment | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const { data: quotesData, isLoading: quotesLoading } = useApiQuery<PageResponse<Quote>>(
    ['quotes', 'select'],
    '/quotes',
    { page: 1, size: 200 },
  )

  const quoteOptions = useMemo(
    () => (quotesData?.items ?? []).map((q) => ({
      value: q.id,
      label: `${q.quote_no}${q.customer_name ? ` - ${q.customer_name}` : ''}`,
    })),
    [quotesData?.items],
  )

  const beforeUpload = () => false

  const handleSubmit = async (values: any) => {
    const quoteId = Number(values.quote_id)
    if (!quoteId) {
      message.error('请选择报价')
      return
    }

    const template = pickFirstFile(values.template_file)
    const steel = pickFirstFile(values.steel_source_file)
    const wdr = pickFirstFile(values.mach_wdr_file)
    const tariff = pickFirstFile(values.mach_tariff_file)

    if (!template?.originFileObj || !steel?.originFileObj || !wdr?.originFileObj || !tariff?.originFileObj) {
      message.error('请上传完整的4个Excel文件')
      return
    }

    const fd = new FormData()
    fd.append('template_file', template.originFileObj)
    fd.append('steel_source_file', steel.originFileObj)
    fd.append('mach_wdr_file', wdr.originFileObj)
    fd.append('mach_tariff_file', tariff.originFileObj)

    fd.append('preserve_marker', values.preserve_marker ?? 'THE LIST IS UNTIL')
    fd.append('steel_sheet_keywords', values.steel_sheet_keywords ?? 'steel,procida')
    fd.append('steel_part_keyword', values.steel_part_keyword ?? 'PART1')
    fd.append('steel_style_row', String(values.steel_style_row ?? 30))
    fd.append('mach_sheet_keywords', values.mach_sheet_keywords ?? 'mach,procida')
    fd.append('mach_tariff_sheet_name', values.mach_tariff_sheet_name ?? 'Quote')
    fd.append('mach_tariff_row_start', String(values.mach_tariff_row_start ?? 616))
    fd.append('mach_tariff_row_end', String(values.mach_tariff_row_end ?? 632))
    if (values.notes) fd.append('notes', values.notes)

    setSubmitting(true)
    setResult(null)
    try {
      const res = await http.postFormData<FileAttachment>(`/quotes/${quoteId}/excel/generate`, fd)
      setResult(res)
      message.success('已生成并保存报价Excel')
    } catch (e) {
      message.error('生成失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <PageHeader title="报价Excel生成" />
      <Card>
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            preserve_marker: 'THE LIST IS UNTIL',
            steel_sheet_keywords: 'steel,procida',
            steel_part_keyword: 'PART1',
            steel_style_row: 30,
            mach_sheet_keywords: 'mach,procida',
            mach_tariff_sheet_name: 'Quote',
            mach_tariff_row_start: 616,
            mach_tariff_row_end: 632,
          }}
          onFinish={handleSubmit}
        >
          <Form.Item name="quote_id" label="选择报价" rules={[{ required: true, message: '请选择报价' }]}>
            <Select
              showSearch
              optionFilterProp="label"
              placeholder="选择报价"
              options={quoteOptions}
              loading={quotesLoading}
              allowClear
            />
          </Form.Item>

          <Form.Item name="template_file" label="目标模板Excel" valuePropName="fileList" getValueFromEvent={(e) => e?.fileList}>
            <Upload beforeUpload={beforeUpload} maxCount={1}>
              <Button icon={<UploadOutlined />}>上传</Button>
            </Upload>
          </Form.Item>

          <Form.Item name="steel_source_file" label="Steel来源Excel" valuePropName="fileList" getValueFromEvent={(e) => e?.fileList}>
            <Upload beforeUpload={beforeUpload} maxCount={1}>
              <Button icon={<UploadOutlined />}>上传</Button>
            </Upload>
          </Form.Item>

          <Form.Item name="mach_wdr_file" label="Mach WDR来源Excel" valuePropName="fileList" getValueFromEvent={(e) => e?.fileList}>
            <Upload beforeUpload={beforeUpload} maxCount={1}>
              <Button icon={<UploadOutlined />}>上传</Button>
            </Upload>
          </Form.Item>

          <Form.Item name="mach_tariff_file" label="Mach Tariff/Quote Excel" valuePropName="fileList" getValueFromEvent={(e) => e?.fileList}>
            <Upload beforeUpload={beforeUpload} maxCount={1}>
              <Button icon={<UploadOutlined />}>上传</Button>
            </Upload>
          </Form.Item>

          <Form.Item name="notes" label="备注（可选）">
            <Input.TextArea rows={2} />
          </Form.Item>

          <Card size="small" title="解析参数（默认按现有脚本）" style={{ marginBottom: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }} size={12}>
              <Form.Item name="preserve_marker" label="保留标记（preserve_marker）">
                <Input />
              </Form.Item>
              <Form.Item name="steel_sheet_keywords" label="Steel sheet关键词（逗号分隔）">
                <Input />
              </Form.Item>
              <Form.Item name="steel_part_keyword" label="Steel来源sheet包含关键字">
                <Input />
              </Form.Item>
              <Form.Item name="steel_style_row" label="Steel样式行号">
                <InputNumber min={1} style={{ width: 240 }} />
              </Form.Item>
              <Form.Item name="mach_sheet_keywords" label="Mach sheet关键词（逗号分隔）">
                <Input />
              </Form.Item>
              <Form.Item name="mach_tariff_sheet_name" label="Tariff sheet名称">
                <Input />
              </Form.Item>
              <Space>
                <Form.Item name="mach_tariff_row_start" label="Tariff起始行">
                  <InputNumber min={1} />
                </Form.Item>
                <Form.Item name="mach_tariff_row_end" label="Tariff结束行">
                  <InputNumber min={1} />
                </Form.Item>
              </Space>
            </Space>
          </Card>

          <Button type="primary" htmlType="submit" loading={submitting}>
            生成并保存
          </Button>
        </Form>

        {result && (
          <div style={{ marginTop: 16 }}>
            <Space>
              <span>已保存：{result.original_name}</span>
              {result.url && (
                <Button type="link" href={result.url} target="_blank" rel="noreferrer">
                  下载
                </Button>
              )}
            </Space>
          </div>
        )}
      </Card>
    </div>
  )
}
