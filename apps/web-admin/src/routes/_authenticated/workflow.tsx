import { useState, useCallback, useMemo, useEffect } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { Button, Space, Modal, Form, Input, Select, message, Card, Table, Tabs, Spin } from 'antd'
import {
  PlusOutlined, SaveOutlined, UndoOutlined, RedoOutlined,
  DeleteOutlined, CheckCircleOutlined, PlayCircleOutlined,
} from '@ant-design/icons'
import { ReactFlow, Background, Controls, MiniMap, type NodeTypes } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useApiQuery, usePageQuery } from '@lg/react-hooks'
import { PageHeader } from '@/components/common'
import { useFormat } from '@/hooks/useFormat'
import { http } from '@lg/api-client'
import type { WorkflowTemplate, WorkflowTemplateListItem, WorkflowInstance, WorkflowValidationResult, PageResponse } from '@lg/api-client'
import { useQueryClient } from '@tanstack/react-query'
import { CustomNode } from '@/components/workflow/CustomNode'
import { NodePanel } from '@/components/workflow/NodePanel'
import { NodeEditDialog } from '@/components/workflow/NodeEditDialog'
import { ValidationPanel } from '@/components/workflow/ValidationPanel'
import { useWorkflowEditor } from '@/components/workflow/useWorkflowEditor'

export const Route = createFileRoute('/_authenticated/workflow')({
  component: WorkflowPage,
})

const nodeTypes: NodeTypes = {
  start: CustomNode,
  end: CustomNode,
  approval: CustomNode,
  notification: CustomNode,
  condition: CustomNode,
  parallel: CustomNode,
  timer: CustomNode,
  quote: CustomNode,
  contract: CustomNode,
  procurement: CustomNode,
  delivery: CustomNode,
  payment: CustomNode,
  settlement: CustomNode,
  custom: CustomNode,
}

function WorkflowPage() {
  const { fmtDate } = useFormat()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('editor')
  const [templateId, setTemplateId] = useState<number | null>(null)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [saveOpen, setSaveOpen] = useState(false)
  const [validationResult, setValidationResult] = useState<WorkflowValidationResult | null>(null)
  const [customNameOpen, setCustomNameOpen] = useState(false)
  const [customNodeName, setCustomNodeName] = useState('')
  const [form] = Form.useForm()

  const editor = useWorkflowEditor()

  const { data: templates, isLoading: loadingTemplates } = usePageQuery<WorkflowTemplateListItem>(
    ['workflow', 'templates'], '/workflows/templates', { size: 50 }
  )
  const { data: instances } = usePageQuery<WorkflowInstance>(
    ['workflow', 'instances'], '/workflows/instances', { size: 50 }
  )

  const handleLoadTemplate = useCallback(async (id: number) => {
    try {
      const tpl = await http.get<WorkflowTemplate>(`/workflows/templates/${id}`)
      editor.loadDefinition({
        nodes: tpl.definition.nodes.map((n) => ({
          ...n,
          type: n.type || 'task',
          data: n.data ?? { label: 'Node' },
        })),
        edges: tpl.definition.edges.map((e) => ({
          ...e,
          sourceHandle: e.source_handle,
          targetHandle: e.target_handle,
        })),
      })
      setTemplateId(id)
      message.success(`已加载模板: ${tpl.name}`)
    } catch (e) {
      message.error('加载模板失败')
    }
  }, [editor])

  const handleSave = async (values: { name: string; description?: string; project_type?: string }) => {
    try {
      const definition = editor.getDefinition()
      // Validate before saving
      const validation = await http.post<WorkflowValidationResult>('/workflows/validate', { definition })
      if (!validation.valid) {
        setValidationResult(validation)
        message.error(`保存失败：${validation.errors.length} 个验证错误，请先修正`)
        return
      }
      if (templateId) {
        await http.put(`/workflows/templates/${templateId}`, { ...values, definition })
        message.success('模板已更新')
      } else {
        await http.post('/workflows/templates', { ...values, definition })
        message.success('模板已创建')
      }
      queryClient.invalidateQueries({ queryKey: ['workflow'] })
      setSaveOpen(false)
    } catch (e) {
      message.error(e instanceof Error ? e.message : '保存失败')
    }
  }

  // Keyboard shortcuts: Ctrl+Z undo, Ctrl+Shift+Z redo, Ctrl+S save
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isCtrl = e.ctrlKey || e.metaKey
      if (!isCtrl) return

      if (e.key === 'z' && !e.shiftKey) {
        e.preventDefault()
        editor.undo()
      } else if ((e.key === 'z' && e.shiftKey) || e.key === 'y') {
        e.preventDefault()
        editor.redo()
      } else if (e.key === 's') {
        e.preventDefault()
        setSaveOpen(true)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [editor])

  const handleValidate = async () => {
    try {
      const definition = editor.getDefinition()
      const result = await http.post<WorkflowValidationResult>('/workflows/validate', { definition })
      setValidationResult(result)
      if (result.valid) message.success('验证通过')
      else message.warning(`${result.errors.length} 个错误`)
    } catch (e) {
      message.error('验证失败')
    }
  }

  const handleAddNode = (type: string, data: Record<string, unknown>) => {
    if (type === 'custom') {
      setCustomNodeName('')
      setCustomNameOpen(true)
      return
    }
    editor.addNode(type, { x: 250 + Math.random() * 200, y: 150 + Math.random() * 200 }, data)
  }

  const handleCustomNodeConfirm = () => {
    const name = customNodeName.trim()
    if (!name) {
      message.warning('请输入节点名称')
      return
    }
    editor.addNode('custom', { x: 250 + Math.random() * 200, y: 150 + Math.random() * 200 }, {
      label: name, nodeType: 'custom', config: {},
    })
    setCustomNameOpen(false)
    setCustomNodeName('')
  }

  const handleNodeDoubleClick = useCallback((_: React.MouseEvent, node: { id: string }) => {
    const found = editor.nodes.find((n) => n.id === node.id) ?? null
    editor.setSelectedNode(found)
    setEditDialogOpen(true)
  }, [editor])

  const templateColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '项目类型', dataIndex: 'project_type', key: 'project_type', width: 100 },
    { title: '节点数', dataIndex: 'node_count', key: 'node_count', width: 70 },
    { title: '版本', dataIndex: 'version', key: 'version', width: 60 },
    { title: '更新时间', dataIndex: 'updated_at', key: 'updated_at', width: 120, render: (v: string) => fmtDate(v) },
    {
      title: '操作', key: 'actions', width: 120,
      render: (_: unknown, r: WorkflowTemplateListItem) => (
        <Space>
          <Button type="link" size="small" onClick={() => { handleLoadTemplate(r.id); setActiveTab('editor') }}>编辑</Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <PageHeader title="工作流编排" />

      <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
        {
          key: 'editor',
          label: '流程编辑器',
          children: (
            <div style={{ display: 'flex', gap: 12 }}>
              <NodePanel onAdd={handleAddNode} />

              <div style={{ flex: 1 }}>
                <Space style={{ marginBottom: 8 }}>
                  <Button icon={<UndoOutlined />} disabled={!editor.canUndo} onClick={editor.undo}>撤销</Button>
                  <Button icon={<RedoOutlined />} disabled={!editor.canRedo} onClick={editor.redo}>重做</Button>
                  <Button icon={<DeleteOutlined />} danger onClick={editor.removeSelected}>删除选中</Button>
                  <Button icon={<CheckCircleOutlined />} onClick={handleValidate}>验证</Button>
                  <Button type="primary" icon={<SaveOutlined />} onClick={() => setSaveOpen(true)}>保存</Button>
                </Space>

                <div style={{ height: 500, border: '1px solid #e8e8e8', borderRadius: 8 }}>
                  <ReactFlow
                    nodes={editor.nodes}
                    edges={editor.edges}
                    onNodesChange={editor.onNodesChange}
                    onEdgesChange={editor.onEdgesChange}
                    onConnect={editor.onConnect}
                    onNodeDoubleClick={handleNodeDoubleClick}
                    nodeTypes={nodeTypes}
                    snapToGrid
                    snapGrid={[15, 15]}
                    fitView
                    deleteKeyCode="Delete"
                  >
                    <Background />
                    <Controls />
                    <MiniMap />
                  </ReactFlow>
                </div>

                <ValidationPanel result={validationResult} />
              </div>
            </div>
          ),
        },
        {
          key: 'templates',
          label: '模板列表',
          children: (
            <Table
              rowKey="id"
              columns={templateColumns}
              dataSource={templates?.items}
              loading={loadingTemplates}
              pagination={false}
            />
          ),
        },
        {
          key: 'instances',
          label: '运行实例',
          children: (
            <Table
              rowKey="id"
              columns={[
                { title: '名称', dataIndex: 'name', key: 'name' },
                { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
                { title: '订单号', dataIndex: 'order_no', key: 'order_no', width: 140 },
                { title: '模板', dataIndex: 'template_name', key: 'template_name', width: 140 },
                { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 120, render: (v: string) => fmtDate(v) },
              ]}
              dataSource={instances?.items}
              pagination={false}
            />
          ),
        },
      ]} />

      <NodeEditDialog
        node={editor.selectedNode}
        open={editDialogOpen}
        onClose={() => setEditDialogOpen(false)}
        onSave={editor.updateNodeData}
      />

      <Modal title={templateId ? '更新模板' : '保存为模板'} open={saveOpen} onCancel={() => setSaveOpen(false)} onOk={() => form.submit()}>
        <Form form={form} layout="vertical" onFinish={handleSave}>
          <Form.Item name="name" label="模板名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="描述"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="project_type" label="项目类型">
            <Select allowClear options={[
              { value: 'SUPERVISION', label: '监修' },
              { value: 'SPARE_PARTS', label: '备件' },
              { value: 'GENERAL', label: '一般贸易' },
            ]} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="添加自定义节点"
        open={customNameOpen}
        onCancel={() => setCustomNameOpen(false)}
        onOk={handleCustomNodeConfirm}
        okText="添加"
      >
        <p style={{ marginBottom: 12, color: '#666', fontSize: 13 }}>
          为自定义节点命名（如「派遣」「验收」「质检」等），该节点需要手动标记完成。
        </p>
        <Input
          placeholder="输入节点名称"
          value={customNodeName}
          onChange={(e) => setCustomNodeName(e.target.value)}
          onPressEnter={handleCustomNodeConfirm}
          autoFocus
        />
      </Modal>
    </div>
  )
}
