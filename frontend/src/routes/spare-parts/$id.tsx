import { useParams } from '@tanstack/react-router'
import { ArrowLeft, Package, Camera, Clock, FileSignature, Receipt } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Tabs } from '@/components/ui/Tabs'
import { useApiGet } from '@/hooks/useApi'
import type { Project } from '@/types'
import SparePartForm from '@/components/spare/SparePartForm'
import SparePhotos from '@/components/spare/SparePhotos'
import LogisticsTimeline from '@/components/spare/LogisticsTimeline'
import HKSignature from '@/components/spare/HKSignature'
import InvoiceForm from '@/components/spare/InvoiceForm'

export default function SparePartsDetail() {
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
        <Package className="mx-auto h-12 w-12 opacity-50 mb-3" />
        <p className="text-lg">项目不存在</p>
      </div>
    )
  }

  const tabConfig = [
    {
      value: 'info',
      label: '备件信息',
      icon: <Package className="h-4 w-4" />,
      content: <SparePartForm projectId={project.id} />,
    },
    {
      value: 'photos',
      label: '发货照片',
      icon: <Camera className="h-4 w-4" />,
      content: <SparePhotos projectId={project.id} />,
    },
    {
      value: 'logistics',
      label: '物流时间线',
      icon: <Clock className="h-4 w-4" />,
      content: <LogisticsTimeline projectId={project.id} />,
    },
    {
      value: 'signature',
      label: '签收单',
      icon: <FileSignature className="h-4 w-4" />,
      content: <HKSignature projectId={project.id} />,
    },
    {
      value: 'invoice',
      label: '发票',
      icon: <Receipt className="h-4 w-4" />,
      content: <InvoiceForm projectId={project.id} />,
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