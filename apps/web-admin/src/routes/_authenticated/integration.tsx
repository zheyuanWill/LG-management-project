import { createFileRoute } from '@tanstack/react-router'
import { useState, useEffect, useCallback, useMemo } from 'react'
import {
  Card, Button, Space, Table, Select, Tabs, message, Alert, Modal, Form,
  DatePicker, Empty, Tag, Typography, Statistic, Row, Col, Popconfirm, Input,
  Upload, InputNumber,
} from 'antd'
import type { UploadFile } from 'antd'
import {
  ReloadOutlined, AccountBookOutlined, FileTextOutlined,
  CheckCircleOutlined, CloseCircleOutlined, LoadingOutlined,
  SyncOutlined, DatabaseOutlined,
  PlusOutlined, DeleteOutlined, EyeOutlined,
  RollbackOutlined, UploadOutlined, LinkOutlined, DisconnectOutlined,
  SearchOutlined, PaperClipOutlined,
} from '@ant-design/icons'
import dayjs, { type Dayjs } from 'dayjs'
import { http } from '@lg/api-client'
import { useApiQuery } from '@lg/react-hooks'
import { PageHeader } from '@/components/common'

export const Route = createFileRoute('/_authenticated/integration')({
  component: IntegrationPage,
})

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type R = Record<string, any>

const ITEM_CLS_FIELD_MAP: Record<string, string> = {
  '客户': 'custNo',
  '供应商': 'suppNo',
  '部门': 'deptNo',
  '职员': 'empNo',
  '存货': 'inventoryNo',
  '项目': 'projectNo',
}

function AuxAccountingSelect({ value, onChange }: {
  value?: { clsName?: string; itemNumber?: string }
  onChange?: (v: { clsName?: string; itemNumber?: string } | undefined) => void
}) {
  const [classes, setClasses] = useState<{ id: number; name: string }[]>([])
  const [items, setItems] = useState<{ number: string; name: string; id: number }[]>([])
  const [itemsLoading, setItemsLoading] = useState(false)
  const selectedCls = value?.clsName

  useEffect(() => {
    http.get<{ list?: { id: number; name: string }[] }>('/integration/kingdee/itemclass')
      .then(r => setClasses(r.list || []))
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (!selectedCls) { setItems([]); return }
    setItemsLoading(true)
    http.get<{ list?: { number: string; name: string; id: number }[] }>('/integration/kingdee/items', { item_cls_name: selectedCls, page_size: 200 })
      .then(r => setItems(r.list || []))
      .catch(() => setItems([]))
      .finally(() => setItemsLoading(false))
  }, [selectedCls])

  return (
    <Space size={4} style={{ display: 'flex' }}>
      <Select
        size="small" style={{ width: 100 }} placeholder="核算类别"
        allowClear showSearch optionFilterProp="label"
        value={selectedCls}
        options={classes.map(c => ({ label: c.name, value: c.name }))}
        onChange={cls => onChange?.(cls ? { clsName: cls, itemNumber: undefined } : undefined)}
      />
      {selectedCls && (
        <Select
          size="small" style={{ width: 160 }} placeholder="选择核算项"
          allowClear showSearch optionFilterProp="label"
          loading={itemsLoading}
          value={value?.itemNumber}
          options={items.map(it => ({ label: `${it.number} ${it.name}`, value: it.number }))}
          onChange={num => onChange?.(num ? { ...value, itemNumber: num } : { clsName: selectedCls })}
        />
      )}
    </Space>
  )
}

const toInt = (d: Dayjs) => d.year() * 100 + d.month() + 1
const toDayjs = (v: number) => dayjs(`${String(v).slice(0, 4)}-${String(v).slice(4)}`, 'YYYY-MM')

const fmt = (v: unknown) => {
  if (v === null || v === undefined || v === '') return '—'
  const n = Number(v)
  if (!isNaN(n) && typeof v !== 'boolean' && String(v).match(/^-?\d+(\.\d+)?$/))
    return n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  return String(v)
}

// =====================================================================
// 凭证同步
// =====================================================================
function VoucherSyncTab() {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string>()
  const [typeFilter, setTypeFilter] = useState<string>()

  const params = useMemo(() => {
    const p: R = { page, page_size: 20 }
    if (statusFilter) p.status = statusFilter
    if (typeFilter) p.entity_type = typeFilter
    return p
  }, [page, statusFilter, typeFilter])

  const { data, isLoading, refetch } = useApiQuery<{ items: R[]; total: number; summary: R }>(['sync-logs', params], '/analytics/sync-logs', params)

  const summary = data?.summary || {}

  const handleRetry = useCallback(async (log: R) => {
    try {
      await http.post('/integration/sync/entity', { entity_type: log.entity_type, entity_id: log.entity_id })
      message.success('重试已提交')
      refetch()
    } catch {
      message.error('重试失败')
    }
  }, [refetch])

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card size="small">
            <Statistic title="成功" value={summary.success || 0} valueStyle={{ color: '#52c41a', fontSize: 20 }} prefix={<CheckCircleOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic title="失败" value={summary.failed || 0} valueStyle={{ color: '#ff4d4f', fontSize: 20 }} prefix={<CloseCircleOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic title="待处理" value={summary.pending || 0} valueStyle={{ color: '#1677ff', fontSize: 20 }} prefix={<SyncOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic title="跳过" value={summary.skipped || 0} valueStyle={{ color: '#999', fontSize: 20 }} />
          </Card>
        </Col>
      </Row>

      <Space style={{ marginBottom: 12 }} wrap>
        <Select
          size="small" style={{ width: 100 }} placeholder="状态" allowClear
          options={[
            { label: '成功', value: 'success' },
            { label: '失败', value: 'failed' },
            { label: '待处理', value: 'pending' },
            { label: '跳过', value: 'skipped' },
          ]}
          onChange={v => { setStatusFilter(v); setPage(1) }}
        />
        <Select
          size="small" style={{ width: 120 }} placeholder="实体类型" allowClear
          options={[
            { label: '订单', value: 'order' },
            { label: '采购', value: 'procurement' },
            { label: '付款', value: 'disbursement' },
            { label: '结算', value: 'settlement' },
            { label: '回款', value: 'payment' },
          ]}
          onChange={v => { setTypeFilter(v); setPage(1) }}
        />
        <Button size="small" icon={<ReloadOutlined />} onClick={() => refetch()}>刷新</Button>
      </Space>

      <Table<R>
        rowKey="id"
        dataSource={data?.items || []}
        loading={isLoading}
        size="small" bordered
        scroll={{ x: 900 }}
        pagination={{ current: page, pageSize: 20, total: data?.total || 0, size: 'small', onChange: setPage, showTotal: t => `共 ${t} 条` }}
        columns={[
          { title: '时间', dataIndex: 'created_at', width: 150, render: (v: string) => v ? dayjs(v).format('MM-DD HH:mm') : '—' },
          { title: '类型', dataIndex: 'entity_type', width: 70, render: (v: string) => {
            const m: R = { order: '订单', procurement: '采购', disbursement: '付款', settlement: '结算', payment: '回款' }
            return m[v] || v
          }},
          { title: '实体ID', dataIndex: 'entity_id', width: 70, align: 'center' },
          { title: '凭证类型', dataIndex: 'kingdee_doc_type', width: 80 },
          { title: '凭证号', dataIndex: 'kingdee_doc_no', width: 90 },
          { title: '状态', dataIndex: 'status', width: 70, render: (s: string) => {
            const c: R = { success: 'success', failed: 'error', pending: 'processing', skipped: 'default' }
            const l: R = { success: '成功', failed: '失败', pending: '待处理', skipped: '跳过' }
            return <Tag color={c[s]}>{l[s] || s}</Tag>
          }},
          { title: '错误信息', dataIndex: 'error_message', ellipsis: true },
          { title: '重试', dataIndex: 'retry_count', width: 50, align: 'center' },
          { title: '操作', width: 70, fixed: 'right', render: (_: unknown, r: R) => r.status === 'failed' ? (
            <Button type="link" size="small" onClick={() => handleRetry(r)}>重试</Button>
          ) : null },
        ]}
      />
    </div>
  )
}

// =====================================================================
// Tab 4: 金蝶原始数据
// =====================================================================
type KingdeeResp = { list?: R[]; count?: number; code?: number; msg?: string }
interface QS { data: R[]; loading: boolean; msg: string; count: number }
const emptyQS: QS = { data: [], loading: false, msg: '', count: 0 }

function KingdeeDataTab() {
  const now = new Date()
  const defaultPeriod = 202512
  const yearStart = 202501

  const queryKingdee = useCallback(async (
    url: string, params: R | undefined, setter: React.Dispatch<React.SetStateAction<QS>>,
  ) => {
    setter(s => ({ ...s, loading: true, msg: '' }))
    try {
      const res = await http.get<KingdeeResp>(url, params)
      if (res.code && res.code !== 0) {
        setter({ data: [], loading: false, msg: res.msg || `错误 ${res.code}`, count: 0 })
      } else {
        const items = res.list || []
        setter({ data: items, loading: false, msg: items.length === 0 ? (res.msg || '暂无数据') : '', count: res.count || items.length })
      }
    } catch { setter({ data: [], loading: false, msg: '请求失败', count: 0 }) }
  }, [])

  // ── Vouchers ──
  const [vchState, setVchState] = useState<QS>(emptyQS)
  const [vchPage, setVchPage] = useState(1)
  const [vchPageSize, setVchPageSize] = useState(20)
  const [vchFrom, setVchFrom] = useState(yearStart)
  const [vchTo, setVchTo] = useState(defaultPeriod)
  const fetchVouchers = useCallback(() => queryKingdee('/integration/kingdee/vouchers', { from_period: vchFrom, to_period: vchTo, page: vchPage, page_size: vchPageSize }, setVchState), [queryKingdee, vchFrom, vchTo, vchPage, vchPageSize])

  useEffect(() => { fetchVouchers() }, [fetchVouchers])

  // ── Voucher Summary ──
  const [sumState, setSumState] = useState<QS>(emptyQS)
  const [sumFrom, setSumFrom] = useState(yearStart)
  const [sumTo, setSumTo] = useState(defaultPeriod)
  const fetchSummary = useCallback(() => queryKingdee('/integration/kingdee/voucher-summary', { from_period: sumFrom, to_period: sumTo }, setSumState), [queryKingdee, sumFrom, sumTo])

  // ── Balance ──
  const [balState, setBal] = useState<QS>(emptyQS)
  const [balFrom, setBalFrom] = useState(yearStart)
  const [balTo, setBalTo] = useState(defaultPeriod)
  const fetchBalance = useCallback(() => queryKingdee('/integration/kingdee/account-balance', { from_period: balFrom, to_period: balTo }, setBal), [queryKingdee, balFrom, balTo])

  // ── Report ──
  const [rptState, setRpt] = useState<QS>(emptyQS)
  const [rptType, setRptType] = useState(2)
  const [rptFrom, setRptFrom] = useState(yearStart)
  const [rptTo, setRptTo] = useState(defaultPeriod)
  const fetchReport = useCallback(() => queryKingdee('/integration/kingdee/report', { report_type: rptType, start_period: rptFrom, end_period: rptTo }, setRpt), [queryKingdee, rptType, rptFrom, rptTo])

  // ── General Ledger (总账) ──
  const [glState, setGlState] = useState<QS>(emptyQS)
  const [glFrom, setGlFrom] = useState(yearStart)
  const [glTo, setGlTo] = useState(defaultPeriod)
  const [glFromAcct, setGlFromAcct] = useState('')
  const [glToAcct, setGlToAcct] = useState('')
  const [glIncludeItem, setGlIncludeItem] = useState(0)
  const [glBalance, setGlBalance] = useState(1)
  const [glHappen, setGlHappen] = useState(1)
  const fetchGeneralLedger = useCallback(() => {
    const params: R = { from_period: glFrom, to_period: glTo, include_item: glIncludeItem, balance: glBalance, happen: glHappen }
    if (glFromAcct) params.from_account = glFromAcct
    if (glToAcct) params.to_account = glToAcct
    queryKingdee('/integration/kingdee/general-ledger', params, setGlState)
  }, [queryKingdee, glFrom, glTo, glFromAcct, glToAcct, glIncludeItem, glBalance, glHappen])

  // ── Evidence (原始凭证) ──
  const [evidState, setEvidState] = useState<QS>(emptyQS)
  const [evidFrom, setEvidFrom] = useState(yearStart)
  const [evidTo, setEvidTo] = useState(defaultPeriod)
  const fetchEvidence = useCallback(async () => {
    setEvidState(s => ({ ...s, loading: true, msg: '' }))
    try {
      const res = await http.post<KingdeeResp>(`/integration/kingdee/evidence/list?begin_period=${evidFrom}&end_period=${evidTo}`)
      const items = res.list || []
      setEvidState({ data: items, loading: false, msg: items.length === 0 ? (res.msg || '暂无数据') : '', count: res.count || items.length })
    } catch { setEvidState({ data: [], loading: false, msg: '请求失败', count: 0 }) }
  }, [evidFrom, evidTo])

  // ── Attachments (附件) ──
  const [fileState, setFileState] = useState<QS>(emptyQS)
  const fetchAttachments = useCallback(async () => {
    setFileState(s => ({ ...s, loading: true, msg: '' }))
    try {
      const res = await http.post<KingdeeResp>(`/integration/kingdee/evidence/attachments?begin_period=${evidFrom}&end_period=${evidTo}`)
      const items = res.list || []
      setFileState({ data: items, loading: false, msg: items.length === 0 ? (res.msg || '暂无数据') : '', count: res.count || items.length })
    } catch { setFileState({ data: [], loading: false, msg: '请求失败', count: 0 }) }
  }, [evidFrom, evidTo])

  // ── Excel Import (基础表智能导入) ──
  const [importModalOpen, setImportModalOpen] = useState(false)
  const [importSheets, setImportSheets] = useState<import('@/utils/voucher-import').DetectedSheet[]>([])
  const [importSelected, setImportSelected] = useState<Set<string>>(new Set())
  const [importVouchers, setImportVouchers] = useState<import('@/utils/voucher-import').VoucherDraft[]>([])
  const [importWb, setImportWb] = useState<R | null>(null)
  const [importLoading, setImportLoading] = useState(false)
  const [importStep, setImportStep] = useState<'sheets' | 'preview'>('sheets')

  const handleExcelUpload = useCallback(async (file: File) => {
    const XLSX = await (import('xlsx') as Promise<typeof import('xlsx')>)
    const { detectSheets } = await import('@/utils/voucher-import')
    const buf = await file.arrayBuffer()
    const wb = XLSX.read(buf, { type: 'array' })

    const detected = detectSheets(wb.SheetNames)
    if (detected.length === 0) {
      message.warning('未识别到可导入的 sheet（取得发票、开具发票、银行）')
      return
    }

    for (const s of detected) {
      const ws = wb.Sheets[s.name]
      const rows = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '', blankrows: false }) as unknown[][]
      s.rowCount = Math.max(0, rows.length - 1)
    }

    setImportWb(wb)
    setImportSheets(detected)
    setImportSelected(new Set(detected.map(s => s.name)))
    setImportVouchers([])
    setImportStep('sheets')
    setImportModalOpen(true)
  }, [])

  const handleGenerateVouchers = useCallback(async () => {
    if (!importWb || importSelected.size === 0) return
    setImportLoading(true)
    const XLSX = await (import('xlsx') as Promise<typeof import('xlsx')>)
    const { processSheet } = await import('@/utils/voucher-import')

    const all: import('@/utils/voucher-import').VoucherDraft[] = []
    for (const s of importSheets) {
      if (!importSelected.has(s.name)) continue
      const ws = importWb.Sheets[s.name]
      const rows = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '', blankrows: false }) as unknown[][]
      const vouchers = processSheet(s.type, rows)
      all.push(...vouchers)
    }

    setImportVouchers(all)
    setImportStep('preview')
    setImportLoading(false)
    const allWarnings = all.flatMap(v => v.warnings || [])
    if (allWarnings.length > 0) message.warning(`${allWarnings.length} 条数据存在问题，请查看预览中的警告`)
    if (all.filter(v => v.entries.length > 0).length === 0) message.warning('未能生成凭证，请检查 Excel 数据')
  }, [importWb, importSheets, importSelected])

  const handleImportSubmit = useCallback(async () => {
    const submittable = importVouchers.filter(v => v.entries.length > 0)
    if (submittable.length === 0) return
    setImportLoading(true)
    const { toKingdeePayload } = await import('@/utils/voucher-import')
    const XLSX = await (import('xlsx') as Promise<typeof import('xlsx')>)
    let success = 0
    const failedItems: { draft: typeof importVouchers[number]; errMsg: string }[] = []

    for (const v of submittable) {
      try {
        const res = await http.post<R>('/integration/kingdee/voucher/save', toKingdeePayload(v))
        if (res.code === 0) success++
        else failedItems.push({ draft: v, errMsg: res.msg || '未知错误' })
      } catch { failedItems.push({ draft: v, errMsg: '请求失败' }) }
    }

    setImportLoading(false)

    if (failedItems.length > 0) {
      const rows: R[] = failedItems.map(({ draft, errMsg }) => {
        const debitEntries = draft.entries.filter(e => e.dc === 1)
        const creditEntries = draft.entries.filter(e => e.dc === -1)
        return {
          '错误信息': errMsg,
          '来源': draft.source,
          '日期': draft.date,
          '摘要': draft.explanation,
          '凭证字': draft.groupName,
          '分录数': draft.entries.length,
          '借方科目': debitEntries.map(e => e.accountNumber).join(', '),
          '借方金额': debitEntries.reduce((s, e) => s + e.amountFor, 0),
          '贷方科目': creditEntries.map(e => e.accountNumber).join(', '),
          '贷方金额': creditEntries.reduce((s, e) => s + e.amountFor, 0),
        }
      })

      const ws = XLSX.utils.json_to_sheet(rows)
      ws['!cols'] = [
        { wch: 55 }, { wch: 16 }, { wch: 12 }, { wch: 35 }, { wch: 6 },
        { wch: 8 }, { wch: 30 }, { wch: 14 }, { wch: 30 }, { wch: 14 },
      ]
      const wb = XLSX.utils.book_new()
      XLSX.utils.book_append_sheet(wb, ws, '导入失败凭证')
      XLSX.writeFile(wb, `凭证导入失败_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`)

      Modal.error({
        title: `导入完成：成功 ${success} 张，失败 ${failedItems.length} 张`,
        width: 560,
        content: (
          <div>
            <p>失败的 {failedItems.length} 张凭证已自动导出为 Excel 文件。</p>
            <div style={{ maxHeight: 300, overflow: 'auto' }}>
              {failedItems.slice(0, 20).map((f, i) => (
                <Alert key={i} type="error" message={`${f.draft.date} ${f.draft.explanation}: ${f.errMsg}`} showIcon style={{ marginBottom: 4 }} banner />
              ))}
              {failedItems.length > 20 && <p style={{ color: '#999', marginTop: 8 }}>...还有 {failedItems.length - 20} 条，请查看已下载的 Excel</p>}
            </div>
          </div>
        ),
      })
    } else {
      message.success(`导入完成：全部 ${success} 张凭证保存成功`)
    }
    if (success > 0) { setImportModalOpen(false); setImportVouchers([]); setImportWb(null); fetchVouchers() }
  }, [importVouchers, fetchVouchers])

  // ── Voucher detail modal ──
  const [detailVoucher, setDetailVoucher] = useState<R | null>(null)

  // ── Batch selection ──
  const [selectedVchIds, setSelectedVchIds] = useState<React.Key[]>([])
  const [batchDeleting, setBatchDeleting] = useState(false)

  // ── Error result modal ──
  const [errorResults, setErrorResults] = useState<{ vch_id: number; success: boolean; msg: string }[]>([])
  const [errorModalOpen, setErrorModalOpen] = useState(false)

  const handleBatchDelete = useCallback(async () => {
    if (selectedVchIds.length === 0) return
    setBatchDeleting(true)
    try {
      const res = await http.post<R>('/integration/kingdee/voucher/batch-delete', { vch_ids: selectedVchIds })
      const results = (res.results || []) as { vch_id: number; success: boolean; msg: string }[]
      const failures = results.filter(r => !r.success)

      if (failures.length > 0) {
        setErrorResults(results)
        setErrorModalOpen(true)
        message.warning(res.msg || `部分凭证删除失败`)
      } else {
        message.success(res.msg || '批量删除成功')
      }

      if ((res.success_count || 0) > 0) {
        setSelectedVchIds([])
        fetchVouchers()
      }
    } catch { message.error('批量删除请求失败') }
    finally { setBatchDeleting(false) }
  }, [selectedVchIds, fetchVouchers])

  // ── Voucher Actions ──
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [saveModalOpen, setSaveModalOpen] = useState(false)
  const [saveForm] = Form.useForm()

  const handleVoucherReverse = useCallback(async (vchId: string) => {
    setActionLoading(vchId + '_reverse')
    try {
      const res = await http.post<R>('/integration/kingdee/voucher/reverse', { vch_id: vchId })
      if (res.code === 0) { message.success('凭证冲销成功'); fetchVouchers() }
      else {
        const detail = res.data ? JSON.stringify(res.data, null, 2) : ''
        Modal.error({ title: '凭证冲销失败', content: <div><p>{res.msg || '冲销失败'}</p>{detail && <pre style={{ maxHeight: 200, overflow: 'auto', fontSize: 12, background: '#f5f5f5', padding: 8 }}>{detail}</pre>}</div>, width: 560 })
      }
    } catch { message.error('冲销请求失败') }
    finally { setActionLoading(null) }
  }, [fetchVouchers])

  const handleVoucherDelete = useCallback(async (vchId: string) => {
    setActionLoading(vchId + '_delete')
    try {
      const res = await http.post<R>('/integration/kingdee/voucher/delete', { vch_id: vchId })
      if (res.code === 0) { message.success('凭证删除成功'); fetchVouchers() }
      else {
        const detail = res.data ? JSON.stringify(res.data, null, 2) : ''
        Modal.error({ title: '凭证删除失败', content: <div><p>{res.msg || '删除失败'}</p>{detail && <pre style={{ maxHeight: 200, overflow: 'auto', fontSize: 12, background: '#f5f5f5', padding: 8 }}>{detail}</pre>}</div>, width: 560 })
      }
    } catch { message.error('删除请求失败') }
    finally { setActionLoading(null) }
  }, [fetchVouchers])

  const handleVoucherSave = useCallback(async (values: R) => {
    setActionLoading('save')
    try {
      const entries = (values.entries || []).map((e: R) => {
        const entry: R = {
          acctNo: e.accountNumber,
          exp: e.explanation || values.explanation,
          dc: e.dc,
          amount: e.amountFor,
          currency: e.cur || 'RMB',
          rate: e.rate || 1,
        }
        const aux = e.auxAccounting as { clsName?: string; itemNumber?: string } | undefined
        if (aux?.clsName && aux?.itemNumber) {
          const field = ITEM_CLS_FIELD_MAP[aux.clsName]
          if (field) {
            entry[field] = aux.itemNumber
          } else {
            entry.itemClsName = aux.clsName
            entry.itemNo = aux.itemNumber
          }
        }
        return entry
      })
      const res = await http.post<R>('/integration/kingdee/voucher/save', {
        date: values.date?.format('YYYY-MM-DD'),
        group_name: values.group_name || '记',
        explanation: values.explanation,
        attachments: values.attachments || 0,
        entries,
        link_id: values.link_id || undefined,
      })
      if (res.code === 0) { message.success('凭证保存成功'); setSaveModalOpen(false); saveForm.resetFields(); fetchVouchers() }
      else {
        const detail = res.data ? JSON.stringify(res.data, null, 2) : ''
        Modal.error({ title: '凭证保存失败', content: <div><p>{res.msg || '保存失败'}</p>{detail && <pre style={{ maxHeight: 200, overflow: 'auto', fontSize: 12, background: '#f5f5f5', padding: 8 }}>{detail}</pre>}</div>, width: 560 })
      }
    } catch { message.error('保存请求失败') }
    finally { setActionLoading(null) }
  }, [fetchVouchers, saveForm])

  // ── Evidence Actions ──
  const [uploadModalOpen, setUploadModalOpen] = useState(false)
  const [uploadForm] = Form.useForm()
  const [attachModalOpen, setAttachModalOpen] = useState(false)
  const [attachForm] = Form.useForm()
  const [unattachModalOpen, setUnattachModalOpen] = useState(false)
  const [unattachForm] = Form.useForm()

  const handleEvidenceUpload = useCallback(async (values: R) => {
    setActionLoading('upload')
    try {
      const file = values.file?.[0]?.originFileObj
      if (!file) { message.warning('请选择文件'); return }
      const reader = new FileReader()
      const base64 = await new Promise<string>((resolve) => {
        reader.onload = () => resolve((reader.result as string).split(',')[1])
        reader.readAsDataURL(file)
      })
      const res = await http.post<R>('/integration/kingdee/evidence/upload', {
        file_name: file.name,
        file_size: file.size,
        period: values.period,
        file_data: base64,
        content_type: file.type || 'application/octet-stream',
      })
      if (res.code === 0) { message.success('原始凭证上传成功'); setUploadModalOpen(false); uploadForm.resetFields(); fetchEvidence() }
      else message.error(res.msg || '上传失败')
    } catch { message.error('上传请求失败') }
    finally { setActionLoading(null) }
  }, [fetchEvidence, uploadForm])

  const handleEvidenceAttach = useCallback(async (values: R) => {
    setActionLoading('attach')
    try {
      const res = await http.post<R>('/integration/kingdee/evidence/attach', {
        voucher_id: values.voucher_id,
        evid_ids: values.evid_ids,
      })
      if (res.code === 0) { message.success('原始凭证绑定成功'); setAttachModalOpen(false); attachForm.resetFields(); fetchEvidence() }
      else message.error(res.msg || '绑定失败')
    } catch { message.error('绑定请求失败') }
    finally { setActionLoading(null) }
  }, [attachForm, fetchEvidence])

  const handleEvidenceUnattach = useCallback(async (values: R) => {
    setActionLoading('unattach')
    try {
      const res = await http.post<R>('/integration/kingdee/evidence/unattach', {
        evid_id: values.evid_id,
        file_id: values.file_id,
      })
      if (res.code === 0) { message.success('原始凭证解绑成功'); setUnattachModalOpen(false); unattachForm.resetFields() }
      else message.error(res.msg || '解绑失败')
    } catch { message.error('解绑请求失败') }
    finally { setActionLoading(null) }
  }, [unattachForm])

  // ── Report pivot ──
  const reportPivot = useMemo(() => {
    if (!rptState.data.length) return { rows: [] as R[], columns: [] as { title: string; dataIndex: string; width?: number; fixed?: 'left'; align?: 'left' | 'right' }[] }
    const periods = rptState.data.map(d => d.date as number).filter(Boolean).sort((a, b) => a - b)
    const nameSet = new Map<number, string>()
    rptState.data.forEach((period: R) => {
      (period.items as R[] || []).forEach((item: R) => { if (!nameSet.has(item.row)) nameSet.set(item.row, item.name) })
    })
    const rows = Array.from(nameSet.entries()).sort(([a], [b]) => a - b).map(([row, name]) => {
      const r: R = { _key: row, name }
      rptState.data.forEach((period: R) => {
        const item = (period.items as R[] || []).find((it: R) => it.row === row)
        r[`v_${period.date}`] = item?.value ?? ''
        r[`ytd_${period.date}`] = item?.ytdValue ?? ''
      })
      const last = periods[periods.length - 1]
      r._ytd = r[`ytd_${last}`] ?? ''
      return r
    })
    const cols: { title: string; dataIndex: string; width?: number; fixed?: 'left'; align?: 'left' | 'right' }[] = [
      { title: '项目', dataIndex: 'name', width: 260, fixed: 'left', align: 'left' },
    ]
    periods.forEach(p => {
      const label = `${String(p).slice(0, 4)}-${String(p).slice(4)}`
      cols.push({ title: `${label} 本期`, dataIndex: `v_${p}`, width: 130, align: 'right' })
    })
    cols.push({ title: '本年累计', dataIndex: '_ytd', width: 130, align: 'right' })
    return { rows, columns: cols }
  }, [rptState.data])

  const glFlat = useMemo(() => {
    const rows: R[] = []
    for (const acct of glState.data) {
      const details = acct.detail || []
      for (const d of details) {
        rows.push({ ...d, number: acct.number, name: acct.name, curRate: acct.curRate })
      }
    }
    return rows
  }, [glState.data])

  const REPORT_TYPES = [
    { label: '利润表', value: 2 },
    { label: '资产负债表', value: 1 },
    { label: '现金流量表', value: 3 },
  ]

  const periodBar = (from: number, setFrom: (v: number) => void, to: number, setTo: (v: number) => void, loading: boolean, onClick: () => void, label = '查询', extra?: React.ReactNode) => (
    <Space style={{ marginBottom: 12 }} wrap>
      <span style={{ color: '#666', fontSize: 13 }}>期间</span>
      <DatePicker picker="month" size="small" style={{ width: 120 }} value={toDayjs(from)} onChange={d => d && setFrom(toInt(d))} allowClear={false} />
      <span style={{ color: '#999' }}>~</span>
      <DatePicker picker="month" size="small" style={{ width: 120 }} value={toDayjs(to)} onChange={d => d && setTo(toInt(d))} allowClear={false} />
      <Button type="primary" size="small" icon={<ReloadOutlined />} loading={loading} onClick={onClick}>{label}</Button>
      {extra}
    </Space>
  )

  const renderEmpty = (s: QS, hint: string) => <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={s.loading ? '加载中...' : s.msg || hint} />

  const normFile = (e: { fileList: UploadFile[] }) => e?.fileList

  return (
    <>
      <Tabs size="small" items={[
        {
          key: 'vouchers',
          label: <span><FileTextOutlined /> 凭证</span>,
          children: (
            <div>
              {periodBar(vchFrom, v => { setVchFrom(v); setVchPage(1) }, vchTo, v => { setVchTo(v); setVchPage(1) }, vchState.loading, fetchVouchers, '查询',
                <Space>
                  <Button type="primary" size="small" icon={<PlusOutlined />} onClick={() => setSaveModalOpen(true)}>新增凭证</Button>
                  <Upload accept=".xlsx,.xls,.csv" showUploadList={false} beforeUpload={f => { handleExcelUpload(f); return false }}>
                    <Button size="small" icon={<UploadOutlined />}>Excel 导入</Button>
                  </Upload>
                  {selectedVchIds.length > 0 && (
                    <Popconfirm
                      title={`确认批量删除选中的 ${selectedVchIds.length} 条凭证？此操作不可撤销。`}
                      onConfirm={handleBatchDelete}
                      okButtonProps={{ danger: true }}
                    >
                      <Button danger size="small" icon={<DeleteOutlined />} loading={batchDeleting}>
                        批量删除 ({selectedVchIds.length})
                      </Button>
                    </Popconfirm>
                  )}
                </Space>
              )}
              {vchState.data.length > 0 ? (
                <Table<R>
                  rowKey={(r) => r.id ?? r.vchId}
                  dataSource={vchState.data} loading={vchState.loading}
                  size="small" bordered scroll={{ x: 1300 }}
                  rowSelection={{
                    selectedRowKeys: selectedVchIds,
                    onChange: (keys) => setSelectedVchIds(keys),
                  }}
                  pagination={{
                    current: vchPage, pageSize: vchPageSize, total: vchState.count,
                    showTotal: t => `共 ${t} 条`, size: 'small', showSizeChanger: true,
                    pageSizeOptions: ['20', '50', '100'],
                    onChange: (p, ps) => { if (ps !== vchPageSize) { setVchPageSize(ps); setVchPage(1) } else { setVchPage(p) } },
                  }}
                  columns={[
                    { title: '日期', dataIndex: 'date', width: 100 },
                    { title: '凭证号', width: 90, render: (_, r) => `${r.groupName || ''}${r.number ? '-' + r.number : ''}` },
                    { title: '期间', dataIndex: 'yearPeriod', width: 70 },
                    { title: '摘要', ellipsis: true, render: (_, r) => r.explanation || r.entries?.[0]?.explanation || '—' },
                    { title: '币种', width: 60, align: 'center', render: (_, r) => {
                      const currencies = new Set<string>((r.entries as R[] || []).map((e: R) => e.currency || 'RMB'))
                      return Array.from(currencies).join('/')
                    }},
                    { title: '原币金额', width: 110, align: 'right', render: (_, r) => {
                      const total = (r.entries as R[] || []).filter((e: R) => e.dc === 1).reduce((s: number, e: R) => s + (e.amountFor || e.amount || 0), 0)
                      return fmt(total)
                    }},
                    { title: '借方', width: 110, align: 'right', render: (_, r) => fmt(r.debitTotal) },
                    { title: '贷方', width: 110, align: 'right', render: (_, r) => fmt(r.creditTotal) },
                    { title: '审核', dataIndex: 'checked', width: 60, align: 'center', render: (v: boolean) => v ? <Tag color="success">已审</Tag> : <Tag>未审</Tag> },
                    { title: '操作', width: 180, fixed: 'right', render: (_, r) => (
                      <Space size={4}>
                        <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => setDetailVoucher(r)}>详情</Button>
                        <Popconfirm title="确认冲销此凭证？" onConfirm={() => handleVoucherReverse(r.id)}>
                          <Button type="link" size="small" icon={<RollbackOutlined />} loading={actionLoading === r.id + '_reverse'}>冲销</Button>
                        </Popconfirm>
                        <Popconfirm title="确认删除此凭证？此操作不可撤销。" onConfirm={() => handleVoucherDelete(r.id)}>
                          <Button type="link" size="small" danger icon={<DeleteOutlined />} loading={actionLoading === r.id + '_delete'}>删除</Button>
                        </Popconfirm>
                      </Space>
                    )},
                  ]}
                />
              ) : renderEmpty(vchState, '点击查询获取凭证')}
            </div>
          ),
        },
        {
          key: 'summary',
          label: <span><AccountBookOutlined /> 凭证汇总</span>,
          children: (
            <div>
              {periodBar(sumFrom, setSumFrom, sumTo, setSumTo, sumState.loading, fetchSummary, '查询汇总')}
              {sumState.data.length > 0 ? (
                <Table<R> rowKey={(_, i) => `s-${i}`} dataSource={sumState.data} loading={sumState.loading} size="small" bordered
                  scroll={{ x: 800 }} pagination={{ pageSize: 50, size: 'small', showTotal: t => `共 ${t} 条` }}
                  columns={[
                    { title: '科目编码', dataIndex: 'FNUMBER', width: 120, fixed: 'left' },
                    { title: '科目名称', dataIndex: 'name', width: 160, fixed: 'left' },
                    { title: '借方金额', dataIndex: 'damount', width: 130, align: 'right', render: v => fmt(v) },
                    { title: '贷方金额', dataIndex: 'camount', width: 130, align: 'right', render: v => fmt(v) },
                    { title: '原币金额', dataIndex: 'amountFor', width: 130, align: 'right', render: v => fmt(v) },
                  ]}
                />
              ) : renderEmpty(sumState, '点击查询获取凭证汇总表')}
            </div>
          ),
        },
        {
          key: 'evidence',
          label: <span><PaperClipOutlined /> 原始凭证</span>,
          children: (
            <div>
              <Space style={{ marginBottom: 12 }} wrap>
                <span style={{ color: '#666', fontSize: 13 }}>起始</span>
                <DatePicker picker="month" size="small" style={{ width: 120 }} value={toDayjs(evidFrom)} onChange={d => d && setEvidFrom(toInt(d))} allowClear={false} />
                <span style={{ color: '#666', fontSize: 13 }}>截止</span>
                <DatePicker picker="month" size="small" style={{ width: 120 }} value={toDayjs(evidTo)} onChange={d => d && setEvidTo(toInt(d))} allowClear={false} />
                <Button type="primary" size="small" icon={<SearchOutlined />} loading={evidState.loading} onClick={fetchEvidence}>查询凭证</Button>
                <Button size="small" icon={<SearchOutlined />} loading={fileState.loading} onClick={fetchAttachments}>查询附件</Button>
                <Button size="small" icon={<UploadOutlined />} onClick={() => setUploadModalOpen(true)}>上传凭证</Button>
                <Button size="small" icon={<LinkOutlined />} onClick={() => setAttachModalOpen(true)}>绑定凭证</Button>
                <Button size="small" icon={<DisconnectOutlined />} onClick={() => setUnattachModalOpen(true)}>解绑凭证</Button>
              </Space>
              {evidState.data.length > 0 ? (
                <Table<R> rowKey={(r, i) => `e-${r.evidId ?? r.id ?? i}`} dataSource={evidState.data} loading={evidState.loading}
                  size="small" bordered scroll={{ x: 1000 }}
                  pagination={{ pageSize: 20, size: 'small', showTotal: t => `共 ${t} 条` }}
                  columns={[
                    { title: '凭证ID', dataIndex: 'evidId', width: 130 },
                    { title: '凭证编号', dataIndex: 'evidNo', width: 180, ellipsis: true },
                    { title: '日期', dataIndex: 'date', width: 110 },
                    { title: '期间', dataIndex: 'yearPeriod', width: 80 },
                    { title: '币种', dataIndex: 'cur', width: 60 },
                    { title: '金额', dataIndex: 'amount', width: 100, align: 'right' as const },
                    { title: '关联凭证', dataIndex: 'voucherId', width: 100, render: (v: any) => v && v !== '0' && v !== 0 ? v : '—' },
                    { title: '附件', width: 80, render: (_: any, r: R) => (r.files as R[] || []).length || 0 },
                  ]}
                  expandable={{
                    expandedRowRender: (r: R) => {
                      const files = (r.files as R[]) || []
                      if (files.length === 0) return <span style={{ color: '#999' }}>无附件</span>
                      return (
                        <Table<R> rowKey={(f, i) => `ef-${f.id ?? i}`} dataSource={files} size="small" bordered pagination={false}
                          columns={[
                            { title: '文件名', dataIndex: 'fileName', width: 200, ellipsis: true },
                            { title: '大小', dataIndex: 'fileSize', width: 80 },
                            { title: '上传者', dataIndex: 'creator', width: 100 },
                            { title: '日期', dataIndex: 'fileDate', width: 110 },
                            { title: '操作', width: 80, render: (_: any, f: R) => f.filePath ? <a href={f.filePath as string} target="_blank" rel="noreferrer">查看</a> : '—' },
                          ]}
                        />
                      )
                    },
                    rowExpandable: (r: R) => ((r.files as R[]) || []).length > 0,
                  }}
                />
              ) : renderEmpty(evidState, '选择期间后点击查询获取原始凭证')}

              {fileState.data.length > 0 && (
                <Card size="small" title="附件列表" style={{ marginTop: 12 }}>
                  <Table<R> rowKey={(r, i) => `f-${r.id ?? i}`} dataSource={fileState.data} loading={fileState.loading}
                    size="small" bordered pagination={{ pageSize: 20, size: 'small', showTotal: t => `共 ${t} 条` }}
                    columns={[
                      { title: '文件ID', dataIndex: 'id', width: 120 },
                      { title: '文件名', dataIndex: 'fileName', width: 200, ellipsis: true },
                      { title: '大小', dataIndex: 'fileSize', width: 80 },
                      { title: '上传者', dataIndex: 'creator', width: 100 },
                      { title: '日期', dataIndex: 'fileDate', width: 110 },
                      { title: '来源ID', dataIndex: 'srcId', width: 130 },
                      { title: '操作', width: 80, render: (_: any, r: R) => r.filePath ? <a href={r.filePath as string} target="_blank" rel="noreferrer">查看</a> : '—' },
                    ]}
                  />
                </Card>
              )}
            </div>
          ),
        },
        {
          key: 'general-ledger',
          label: <span><AccountBookOutlined /> 总账</span>,
          children: (
            <div>
              <Space style={{ marginBottom: 12 }} wrap>
                <span style={{ color: '#666', fontSize: 13 }}>期间</span>
                <DatePicker picker="month" size="small" style={{ width: 120 }} value={toDayjs(glFrom)} onChange={d => d && setGlFrom(toInt(d))} allowClear={false} />
                <span style={{ color: '#999' }}>~</span>
                <DatePicker picker="month" size="small" style={{ width: 120 }} value={toDayjs(glTo)} onChange={d => d && setGlTo(toInt(d))} allowClear={false} />
                <span style={{ color: '#666', fontSize: 13 }}>科目</span>
                <Input size="small" style={{ width: 90 }} placeholder="起始" value={glFromAcct} onChange={e => setGlFromAcct(e.target.value)} />
                <span style={{ color: '#999' }}>~</span>
                <Input size="small" style={{ width: 90 }} placeholder="结束" value={glToAcct} onChange={e => setGlToAcct(e.target.value)} />
                <Select size="small" style={{ width: 120 }} value={glIncludeItem} onChange={setGlIncludeItem}
                  options={[{ label: '不含辅助核算', value: 0 }, { label: '含辅助核算', value: 1 }]} />
                <Select size="small" style={{ width: 110 }} value={glBalance} onChange={setGlBalance}
                  options={[{ label: '含零余额', value: 1 }, { label: '隐藏零余额', value: 0 }]} />
                <Select size="small" style={{ width: 130 }} value={glHappen} onChange={setGlHappen}
                  options={[{ label: '含无发生额', value: 1 }, { label: '隐藏无发生额', value: 0 }]} />
                <Button type="primary" size="small" icon={<ReloadOutlined />} loading={glState.loading} onClick={fetchGeneralLedger}>查询总账</Button>
              </Space>
              {glFlat.length > 0 ? (
                <Table<R>
                  rowKey={(_, i) => `gl-${i}`}
                  dataSource={glFlat} loading={glState.loading}
                  size="small" bordered scroll={{ x: 1100 }}
                  pagination={{ pageSize: 50, size: 'small', showTotal: t => `共 ${t} 条` }}
                  columns={[
                    { title: '科目编码', dataIndex: 'number', width: 100, fixed: 'left' as const },
                    { title: '科目名称', dataIndex: 'name', width: 140, fixed: 'left' as const, ellipsis: true },
                    { title: '期间', dataIndex: 'yearPeriod', width: 80 },
                    { title: '摘要', dataIndex: 'exp', width: 120, ellipsis: true },
                    { title: '方向', dataIndex: 'dcType', width: 50, align: 'center' as const },
                    { title: '借方金额', dataIndex: 'gdebit', width: 120, align: 'right' as const, render: (v: any) => fmt(v) },
                    { title: '贷方金额', dataIndex: 'gcredit', width: 120, align: 'right' as const, render: (v: any) => fmt(v) },
                    { title: '余额', dataIndex: 'gbalance', width: 120, align: 'right' as const, render: (v: any) => {
                      const s = fmt(v); const n = Number(v)
                      if (!isNaN(n) && n < 0) return <span style={{ color: '#ff4d4f' }}>{s}</span>
                      return s
                    }},
                    { title: '汇率', dataIndex: 'curRate', width: 80 },
                  ]}
                />
              ) : renderEmpty(glState, '设置期间和科目范围后点击查询')}
            </div>
          ),
        },
        {
          key: 'balance',
          label: '科目余额',
          children: (
            <div>
              {periodBar(balFrom, setBalFrom, balTo, setBalTo, balState.loading, fetchBalance, '查询余额')}
              {balState.data.length > 0 ? (
                <Table<R> rowKey={(_, i) => `b-${i}`} dataSource={balState.data} loading={balState.loading} size="small" bordered
                  scroll={{ x: 1100 }} pagination={{ pageSize: 50, size: 'small', showTotal: t => `共 ${t} 条` }}
                  columns={[
                    { title: '科目编码', dataIndex: 'number', width: 100, fixed: 'left' },
                    { title: '科目名称', dataIndex: 'accountname', width: 160, fixed: 'left', ellipsis: true },
                    { title: '期初借方', dataIndex: 'beginDebit', width: 110, align: 'right', render: v => fmt(v) },
                    { title: '期初贷方', dataIndex: 'beginCredit', width: 110, align: 'right', render: v => fmt(v) },
                    { title: '本期借方', dataIndex: 'debit', width: 110, align: 'right', render: v => fmt(v) },
                    { title: '本期贷方', dataIndex: 'credit', width: 110, align: 'right', render: v => fmt(v) },
                    { title: '期末借方', dataIndex: 'endDebit', width: 110, align: 'right', render: v => fmt(v) },
                    { title: '期末贷方', dataIndex: 'endCredit', width: 110, align: 'right', render: v => fmt(v) },
                  ]}
                />
              ) : renderEmpty(balState, '点击查询获取科目余额')}
            </div>
          ),
        },
        {
          key: 'report',
          label: '报表',
          children: (
            <div>
              <Space style={{ marginBottom: 12 }} wrap>
                <Select size="small" style={{ width: 120 }} options={REPORT_TYPES} value={rptType} onChange={setRptType} />
                <span style={{ color: '#666', fontSize: 13 }}>期间</span>
                <DatePicker picker="month" size="small" style={{ width: 120 }} value={toDayjs(rptFrom)} onChange={d => d && setRptFrom(toInt(d))} allowClear={false} />
                <span style={{ color: '#999' }}>~</span>
                <DatePicker picker="month" size="small" style={{ width: 120 }} value={toDayjs(rptTo)} onChange={d => d && setRptTo(toInt(d))} allowClear={false} />
                <Button type="primary" size="small" icon={<ReloadOutlined />} loading={rptState.loading} onClick={fetchReport}>查询报表</Button>
              </Space>
              {reportPivot.rows.length > 0 ? (
                <Table<R>
                  rowKey="_key" dataSource={reportPivot.rows} loading={rptState.loading}
                  size="small" bordered
                  scroll={{ x: reportPivot.columns.reduce((s, c) => s + (c.width || 130), 0) }}
                  pagination={false}
                  columns={reportPivot.columns.map(c => ({
                    ...c,
                    render: c.dataIndex === 'name' ? undefined : (v: unknown) => {
                      const s = fmt(v)
                      if (s === '—') return <span style={{ color: '#ccc' }}>—</span>
                      const n = Number(v)
                      if (!isNaN(n) && n < 0) return <span style={{ color: '#ff4d4f' }}>{s}</span>
                      return s
                    },
                  }))}
                  rowClassName={(r) => {
                    const n = String(r.name || '')
                    if (n.startsWith('一') || n.startsWith('二') || n.startsWith('三') || n.startsWith('四')) return 'row-bold'
                    return ''
                  }}
                />
              ) : renderEmpty(rptState, '选择报表类型和期间后点击查询')}
            </div>
          ),
        },
      ]} />

      {/* 新增凭证对话框 */}
      <Modal
        title="新增凭证" open={saveModalOpen} width={900}
        onCancel={() => setSaveModalOpen(false)}
        footer={null}
      >
        <Form form={saveForm} layout="vertical" onFinish={handleVoucherSave}>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="date" label="日期" rules={[{ required: true, message: '请选择日期' }]}>
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="group_name" label="凭证字" initialValue="记">
                <Input />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="attachments" label="附件数" initialValue={0}>
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="explanation" label="摘要" rules={[{ required: true, message: '请输入摘要' }]}>
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="link_id" label="外部单号（可选）">
            <Input placeholder="外部系统单据号，用于去重" />
          </Form.Item>

          <Typography.Text strong>分录</Typography.Text>
          <Form.List name="entries" initialValue={[{ dc: 1 }, { dc: -1 }]}>
            {(fields, { add, remove }) => (
              <div style={{ marginTop: 8 }}>
                {fields.map(({ key, name, ...rest }) => (
                  <div key={key} style={{ marginBottom: 8, padding: '8px 0', borderBottom: '1px dashed #f0f0f0' }}>
                    <Row gutter={8} align="middle">
                      <Col span={5}>
                        <Form.Item {...rest} name={[name, 'accountNumber']} rules={[{ required: true, message: '科目编码' }]} noStyle>
                          <Input placeholder="科目编码" size="small" />
                        </Form.Item>
                      </Col>
                      <Col span={5}>
                        <Form.Item {...rest} name={[name, 'explanation']} noStyle>
                          <Input placeholder="摘要（可选）" size="small" />
                        </Form.Item>
                      </Col>
                      <Col span={3}>
                        <Form.Item {...rest} name={[name, 'dc']} rules={[{ required: true }]} noStyle>
                          <Select size="small" options={[{ label: '借', value: 1 }, { label: '贷', value: -1 }]} />
                        </Form.Item>
                      </Col>
                      <Col span={4}>
                        <Form.Item {...rest} name={[name, 'amountFor']} rules={[{ required: true, message: '金额' }]} noStyle>
                          <InputNumber placeholder="金额" size="small" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                      <Col span={5}>
                        <Form.Item {...rest} name={[name, 'auxAccounting']} noStyle>
                          <AuxAccountingSelect />
                        </Form.Item>
                      </Col>
                      <Col span={2}>
                        {fields.length > 2 && (
                          <Button type="link" danger size="small" icon={<DeleteOutlined />} onClick={() => remove(name)} />
                        )}
                      </Col>
                    </Row>
                  </div>
                ))}
                <Button type="dashed" size="small" onClick={() => add({ dc: 1 })} icon={<PlusOutlined />} style={{ width: '100%' }}>
                  添加分录
                </Button>
              </div>
            )}
          </Form.List>

          <Form.Item style={{ marginTop: 16, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setSaveModalOpen(false)}>取消</Button>
              <Button type="primary" htmlType="submit" loading={actionLoading === 'save'}>保存凭证</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 基础表导入凭证 */}
      <Modal
        title={importStep === 'sheets' ? '选择要导入的 Sheet' : `凭证预览 (${importVouchers.length} 张)`}
        open={importModalOpen} width={1000}
        onCancel={() => { setImportModalOpen(false); setImportVouchers([]); setImportWb(null) }}
        footer={
          <Space>
            <Button onClick={() => { setImportModalOpen(false); setImportVouchers([]); setImportWb(null) }}>取消</Button>
            {importStep === 'sheets' ? (
              <Button type="primary" loading={importLoading} disabled={importSelected.size === 0} onClick={handleGenerateVouchers}>
                生成凭证
              </Button>
            ) : (
              <Space>
                <Button onClick={() => setImportStep('sheets')}>返回选择</Button>
                <Button type="primary" loading={importLoading} onClick={handleImportSubmit}>
                  确认导入 ({importVouchers.length} 张凭证)
                </Button>
              </Space>
            )}
          </Space>
        }
      >
        {importStep === 'sheets' ? (
          <div>
            <Alert type="info" showIcon style={{ marginBottom: 12 }}
              message="系统检测到以下可导入的 Sheet，选择后点击「生成凭证」预览。会计分录将按发票号/银行回单自动分组生成。"
            />
            {importSheets.map(s => (
              <Card key={s.name} size="small" style={{ marginBottom: 8, cursor: 'pointer', border: importSelected.has(s.name) ? '2px solid #1677ff' : undefined }}
                onClick={() => setImportSelected(prev => {
                  const next = new Set(prev)
                  next.has(s.name) ? next.delete(s.name) : next.add(s.name)
                  return next
                })}
              >
                <Space>
                  <input type="checkbox" checked={importSelected.has(s.name)} readOnly />
                  <Typography.Text strong>{s.label}</Typography.Text>
                  <Tag>{s.name}</Tag>
                  <Typography.Text type="secondary">{s.rowCount} 行数据</Typography.Text>
                </Space>
              </Card>
            ))}
          </div>
        ) : (
          <div>
            <Space style={{ marginBottom: 12 }}>
              {Array.from(new Set(importVouchers.map(v => v.source))).map(src => (
                <Tag key={src} color="blue">{src}: {importVouchers.filter(v => v.source === src).length} 张</Tag>
              ))}
            </Space>
            {importVouchers.some(v => v.warnings?.length) && (
              <Alert type="warning" showIcon closable style={{ marginBottom: 12 }}
                message={`${importVouchers.reduce((n, v) => n + (v.warnings?.length || 0), 0)} 条数据存在问题`}
                description={
                  <ul style={{ margin: 0, paddingLeft: 16, maxHeight: 120, overflow: 'auto' }}>
                    {importVouchers.flatMap(v => v.warnings || []).map((w, i) => <li key={i}>{w}</li>)}
                  </ul>
                }
              />
            )}
            <Table<R>
              rowKey={(_: R, i?: number) => `iv-${i}`} dataSource={importVouchers as R[]} size="small" bordered
              scroll={{ x: 1000, y: 450 }}
              pagination={{ pageSize: 30, size: 'small', showTotal: (t: number) => `共 ${t} 张凭证` }}
              columns={[
                { title: '来源', dataIndex: 'source', width: 130, ellipsis: true },
                { title: '日期', dataIndex: 'date', width: 100 },
                { title: '摘要', dataIndex: 'explanation', ellipsis: true },
                { title: '分录数', width: 70, align: 'center' as const, render: (_: unknown, r: R) => (r.entries as R[])?.length || 0 },
                { title: '借方合计', width: 110, align: 'right' as const, render: (_: unknown, r: R) =>
                  fmt((r.entries as R[])?.filter((e: R) => e.dc === 1).reduce((s: number, e: R) => s + (e.amountFor || 0), 0))
                },
                { title: '贷方合计', width: 110, align: 'right' as const, render: (_: unknown, r: R) =>
                  fmt((r.entries as R[])?.filter((e: R) => e.dc === -1).reduce((s: number, e: R) => s + (e.amountFor || 0), 0))
                },
              ]}
              expandable={{
                expandedRowRender: (r: R) => (
                  <Table<R> rowKey={(_: R, i?: number) => `ie-${i}`} dataSource={r.entries as R[]} size="small" pagination={false} bordered
                    columns={[
                      { title: '科目', dataIndex: 'accountNumber', width: 100 },
                      { title: '摘要', dataIndex: 'explanation', ellipsis: true },
                      { title: '借/贷', width: 50, align: 'center' as const, render: (_: unknown, e: R) => e.dc === 1 ? '借' : '贷' },
                      { title: '金额', dataIndex: 'amountFor', width: 110, align: 'right' as const, render: (v: unknown) => fmt(v) },
                    ]}
                  />
                ),
              }}
            />
          </div>
        )}
      </Modal>

      {/* 凭证详情 */}
      <Modal
        title={detailVoucher ? `凭证详情 — ${detailVoucher.groupName || '记'}-${detailVoucher.number || ''} (${detailVoucher.date})` : '凭证详情'}
        open={!!detailVoucher}
        onCancel={() => setDetailVoucher(null)}
        footer={<Button onClick={() => setDetailVoucher(null)}>关闭</Button>}
        width={800}
      >
        {detailVoucher && (
          <div>
            <Row gutter={16} style={{ marginBottom: 12 }}>
              <Col span={6}><Typography.Text type="secondary">日期：</Typography.Text>{detailVoucher.date}</Col>
              <Col span={6}><Typography.Text type="secondary">期间：</Typography.Text>{detailVoucher.yearPeriod}</Col>
              <Col span={6}><Typography.Text type="secondary">审核：</Typography.Text>{detailVoucher.checked ? <Tag color="success">已审</Tag> : <Tag>未审</Tag>}</Col>
              <Col span={6}><Typography.Text type="secondary">附件：</Typography.Text>{detailVoucher.attachments ?? 0}</Col>
            </Row>
            {detailVoucher.explanation && <div style={{ marginBottom: 12 }}><Typography.Text type="secondary">摘要：</Typography.Text>{detailVoucher.explanation}</div>}
            <Table<R>
              rowKey={(_, i) => `d-${i}`}
              dataSource={detailVoucher.entries as R[] || []}
              size="small" bordered pagination={false}
              columns={[
                { title: '科目编码', dataIndex: 'acctNo', width: 110 },
                { title: '科目名称', dataIndex: 'acctName', width: 140, ellipsis: true },
                { title: '摘要', dataIndex: 'explanation', ellipsis: true, render: (v: string, e: R) => v || e.exp || '—' },
                { title: '币种', dataIndex: 'currency', width: 60, align: 'center' },
                { title: '汇率', dataIndex: 'rate', width: 70, align: 'right', render: (v: number) => v && v !== 1 ? v : '—' },
                { title: '原币金额', width: 110, align: 'right', render: (_, e) => fmt(e.amountFor || e.amount) },
                { title: '借方', width: 110, align: 'right', render: (_, e) => e.dc === 1 ? fmt(e.debit || e.amountFor || e.amount) : '—' },
                { title: '贷方', width: 110, align: 'right', render: (_, e) => e.dc === -1 ? fmt(e.credit || e.amountFor || e.amount) : '—' },
              ]}
              summary={() => (
                <Table.Summary fixed>
                  <Table.Summary.Row>
                    <Table.Summary.Cell index={0} colSpan={6} align="right"><strong>合计</strong></Table.Summary.Cell>
                    <Table.Summary.Cell index={6} align="right"><strong>{fmt(detailVoucher.debitTotal)}</strong></Table.Summary.Cell>
                    <Table.Summary.Cell index={7} align="right"><strong>{fmt(detailVoucher.creditTotal)}</strong></Table.Summary.Cell>
                  </Table.Summary.Row>
                </Table.Summary>
              )}
            />
          </div>
        )}
      </Modal>

      {/* 批量删除结果 */}
      <Modal
        title="批量删除结果"
        open={errorModalOpen}
        onCancel={() => setErrorModalOpen(false)}
        footer={<Button type="primary" onClick={() => setErrorModalOpen(false)}>确定</Button>}
        width={560}
      >
        <div style={{ maxHeight: 400, overflow: 'auto' }}>
          {errorResults.map((r, i) => (
            <Alert
              key={i}
              type={r.success ? 'success' : 'error'}
              message={`凭证 ${r.vch_id}: ${r.msg}`}
              showIcon
              style={{ marginBottom: 4 }}
              banner
            />
          ))}
        </div>
        <div style={{ marginTop: 12, color: '#666', fontSize: 13 }}>
          成功 {errorResults.filter(r => r.success).length} 条，
          失败 {errorResults.filter(r => !r.success).length} 条
        </div>
      </Modal>

      {/* 上传原始凭证对话框 */}
      <Modal
        title="上传原始凭证" open={uploadModalOpen}
        onCancel={() => setUploadModalOpen(false)}
        footer={null}
      >
        <Form form={uploadForm} layout="vertical" onFinish={handleEvidenceUpload}>
          <Form.Item name="period" label="会计期间" rules={[{ required: true, message: '请输入期间' }]} initialValue={defaultPeriod}>
            <InputNumber style={{ width: '100%' }} placeholder="如 202601" />
          </Form.Item>
          <Form.Item name="file" label="选择文件" valuePropName="fileList" getValueFromEvent={normFile} rules={[{ required: true, message: '请选择文件' }]}>
            <Upload beforeUpload={() => false} maxCount={1}>
              <Button icon={<UploadOutlined />}>选择文件</Button>
            </Upload>
          </Form.Item>
          <Form.Item style={{ textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setUploadModalOpen(false)}>取消</Button>
              <Button type="primary" htmlType="submit" loading={actionLoading === 'upload'}>上传</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 绑定原始凭证对话框 */}
      <Modal
        title="绑定原始凭证" open={attachModalOpen}
        onCancel={() => setAttachModalOpen(false)}
        footer={null}
      >
        <Form form={attachForm} layout="vertical" onFinish={handleEvidenceAttach}>
          <Form.Item name="voucher_id" label="凭证ID" rules={[{ required: true, message: '请输入凭证ID' }]}>
            <Input placeholder="voucherId" />
          </Form.Item>
          <Form.Item name="evid_ids" label="原始凭证ID" rules={[{ required: true, message: '请输入原始凭证ID' }]} extra="多个用逗号分隔，如 1001,1002">
            <Input placeholder="evidIds (多个用逗号分隔)" />
          </Form.Item>
          <Form.Item style={{ textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setAttachModalOpen(false)}>取消</Button>
              <Button type="primary" htmlType="submit" loading={actionLoading === 'attach'}>绑定</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 解绑原始凭证对话框 */}
      <Modal
        title="解绑原始凭证" open={unattachModalOpen}
        onCancel={() => setUnattachModalOpen(false)}
        footer={null}
      >
        <Form form={unattachForm} layout="vertical" onFinish={handleEvidenceUnattach}>
          <Form.Item name="evid_id" label="原始凭证ID" rules={[{ required: true, message: '请输入原始凭证ID' }]}>
            <Input placeholder="evidId" />
          </Form.Item>
          <Form.Item name="file_id" label="文件ID" rules={[{ required: true, message: '请输入文件ID' }]}>
            <Input placeholder="fileId" />
          </Form.Item>
          <Form.Item style={{ textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setUnattachModalOpen(false)}>取消</Button>
              <Button type="primary" danger htmlType="submit" loading={actionLoading === 'unattach'}>解绑</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}

// =====================================================================
// Main page
// =====================================================================
function IntegrationPage() {
  const [connected, setConnected] = useState<boolean | null>(null)
  const [connMsg, setConnMsg] = useState('')

  useEffect(() => {
    http.get<{ connected: boolean; message: string; enabled: boolean }>('/integration/kingdee/status')
      .then(r => { setConnected(r.connected); setConnMsg(r.message) })
      .catch(() => { setConnected(false); setConnMsg('获取连接状态失败') })
  }, [])

  const statusIcon = connected === null
    ? <LoadingOutlined style={{ color: '#1677ff' }} />
    : connected
      ? <CheckCircleOutlined style={{ color: '#52c41a' }} />
      : <CloseCircleOutlined style={{ color: '#ff4d4f' }} />

  return (
    <div>
      <PageHeader
        title="集成管理"
        subtitle="金蝶精斗云 · 凭证同步 · 原始凭证 · 账簿报表"
        extra={
          <Space size={4}>
            {statusIcon}
            <Typography.Text style={{ fontSize: 13 }} type={connected === false ? 'danger' : 'secondary'}>
              金蝶: {connected === null ? '检测中...' : connected ? '已连接' : connMsg || '未连接'}
            </Typography.Text>
          </Space>
        }
      />

      {connected === false && (
        <Alert type="warning" showIcon message="金蝶连接异常" description={`${connMsg}。凭证同步及金蝶数据查询功能不可用。`} style={{ marginBottom: 16 }}
          action={<Button size="small" onClick={() => {
            setConnected(null)
            http.post<{ connected: boolean; message: string }>('/integration/kingdee/test')
              .then(r => { setConnected(r.connected); setConnMsg(r.message); message[r.connected ? 'success' : 'error'](r.message) })
              .catch(() => { setConnected(false); setConnMsg('测试失败') })
          }}>重试连接</Button>}
        />
      )}

      <Card bodyStyle={{ padding: '12px 16px' }}>
        <Tabs
          size="large"
          items={[
            {
              key: 'sync',
              label: <span><SyncOutlined /> 凭证同步</span>,
              children: <VoucherSyncTab />,
            },
            {
              key: 'kingdee',
              label: <span><DatabaseOutlined /> 金蝶数据</span>,
              children: <KingdeeDataTab />,
            },
          ]}
        />
      </Card>

      <style>{`
        .row-bold td { font-weight: 600 !important; background: #fafafa !important; }
        .row-negative td { background: #fff2f0 !important; }
      `}</style>
    </div>
  )
}
