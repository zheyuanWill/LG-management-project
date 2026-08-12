import { useState, useMemo } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { Plus, Search, Ship, ChevronRight } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { useApiGet } from '@/hooks/useApi'
import type { Project } from '@/types'
import { cn } from '@/lib/utils'

const statusOptions = [
  { value: 'all', label: '全部状态' },
  { value: 'active', label: '进行中' },
  { value: 'completed', label: '已完成' },
  { value: 'cancelled', label: '已取消' },
]

const statusVariantMap: Record<string, 'default' | 'secondary' | 'destructive'> = {
  active: 'default',
  completed: 'secondary',
  cancelled: 'destructive',
}

export default function BrokerageSaleIndex() {
  const navigate = useNavigate()
  const [statusFilter, setStatusFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')

  const { data: projects, isLoading } = useApiGet<Project[]>('/projects', {
    params: { type: 'brokerage_sale' },
  })

  const filteredProjects = useMemo(() => {
    let result = projects || []
    if (statusFilter !== 'all') {
      result = result.filter((p) => p.status === statusFilter)
    }
    if (searchQuery.trim()) {
      const query = searchQuery.trim().toLowerCase()
      result = result.filter(
        (p) =>
          (p.ship_name).toLowerCase().includes(query) ||
          p.project_no.toLowerCase().includes(query)
      )
    }
    return result
  }, [projects, statusFilter, searchQuery])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">买卖经纪项目</h1>
          <p className="text-muted-foreground mt-1">管理船舶买卖经纪项目,跟踪报价与成交</p>
        </div>
        <Button onClick={() => navigate({ to: '/projects/new', search: { type: 'brokerage_sale' } })} size="lg">
          <Plus className="h-5 w-5" />
          新建项目
        </Button>
      </div>

      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">状态:</span>
          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            options={statusOptions}
            className="w-40"
          />
        </div>
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="搜索船名..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="py-16 text-center text-muted-foreground">
          <p>加载中...</p>
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="py-16 text-center text-muted-foreground">
          <Ship className="mx-auto h-12 w-12 opacity-50 mb-3" />
          <p className="text-lg">暂无买卖经纪项目</p>
          <p className="text-sm mt-1">点击"新建项目"创建第一个项目</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredProjects.map((project) => (
            <Card
              key={project.id}
              className={cn(
                'cursor-pointer transition-all hover:shadow-md hover:-translate-y-0.5'
              )}
              onClick={() => navigate({ to: `/brokerage-sale/${project.id}` })}
            >
              <CardContent className="p-5">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="rounded-lg bg-primary/10 p-2">
                      <Ship className="h-4 w-4 text-primary" />
                    </div>
                    <div>
                      <h3 className="font-semibold leading-tight">{project.ship_name}</h3>
                      <p className="text-xs text-muted-foreground">{project.project_no}</p>
                    </div>
                  </div>
                  <Badge variant={statusVariantMap[project.status] || 'default'}>
                    {project.status === 'active' ? '进行中' : project.status === 'completed' ? '已完成' : '已取消'}
                  </Badge>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">船东</span>
                    <span className={project.owner_name ? '' : 'text-muted-foreground/50'}>{project.owner_name || '未设置'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">报价金额</span>
                    <span className="font-medium">
                      {project.total_amount ? `¥${project.total_amount.toLocaleString()}` : '-'}
                    </span>
                  </div>
                  <div className="flex items-center justify-end pt-2 text-primary text-sm font-medium">
                    查看详情 <ChevronRight className="h-4 w-4" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}