import { useParams } from '@tanstack/react-router'
import { ArrowLeft, FileText, Search, DollarSign, FileCheck } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Tabs } from '@/components/ui/Tabs'
import { useApiGet } from '@/hooks/useApi'
import type { Project } from '@/types'
import SurveyForm from '@/components/brokerage/SurveyForm'
import CommercialForm from '@/components/brokerage/CommercialForm'
import ContractUpload from '@/components/brokerage/ContractUpload'

export default function BrokerageSaleDetail() {
  const { id } = useParams({ strict: false })
  const { data: project, isLoading } = useApiGet<Project>(`/projects/${id}`)

  if (isLoading) {
    return (
      <div className="py-16 text-center text-muted-foreground">
        <p>加载中...</p>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="py-16 text-center text-muted-foreground">
        <FileText className="mx-auto h-12 w-12 opacity-50 mb-3" />
        <p className="text-lg">项目不存在</p>
      </div>
    )
  }

  const tabConfig = [
    {
      value: 'info',
      label: '项目信息',
      icon: <FileText className="h-4 w-4" />,
      content: (
        <Card>
          <CardContent className="p-6">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">项目编号</span>
                <p className="font-medium">{project.project_no}</p>
              </div>
              <div>
                <span className="text-muted-foreground">船名</span>
                <p className="font-medium">{project.ship_name}</p>
              </div>
              <div>
                <span className="text-muted-foreground">船东</span>
                <p className="font-medium">{project.owner_name || '-'}</p>
              </div>
              <div>
                <span className="text-muted-foreground">状态</span>
                <Badge variant={project.status === 'active' ? 'default' : 'secondary'}>
                  {project.status === 'active' ? '进行中' : '已完成'}
                </Badge>
              </div>
              <div>
                <span className="text-muted-foreground">创建时间</span>
                <p className="font-medium">{new Date(project.created_at).toLocaleDateString()}</p>
              </div>
              {project.remarks && (
                <div className="col-span-2">
                  <span className="text-muted-foreground">备注</span>
                  <p className="font-medium">{project.remarks}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      ),
    },
    {
      value: 'survey',
      label: '背景调研',
      icon: <Search className="h-4 w-4" />,
      content: <SurveyForm projectId={project.id} />,
    },
    {
      value: 'commercial',
      label: '商务结果',
      icon: <DollarSign className="h-4 w-4" />,
      content: <CommercialForm projectId={project.id} />,
    },
    {
      value: 'contract',
      label: 'MOA合同',
      icon: <FileCheck className="h-4 w-4" />,
      content: <ContractUpload projectId={project.id} />,
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => window.history.back()}>
          <ArrowLeft className="h-4 w-4" />
          返回
        </Button>
      </div>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{project.ship_name}</h1>
          <p className="text-muted-foreground mt-1">
            项目编号: {project.project_no}
          </p>
        </div>
        <Badge variant={project.status === 'active' ? 'default' : 'secondary'}>
          {project.status === 'active' ? '进行中' : '已完成'}
        </Badge>
      </div>

      <Tabs tabs={tabConfig} defaultValue="info" />
    </div>
  )
}