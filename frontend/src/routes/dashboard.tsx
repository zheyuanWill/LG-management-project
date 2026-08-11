import { useApiGet } from '@/hooks/useApi'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import {
  AlertTriangle,
  TrendingUp,
  FileText,
  ClipboardList,
  Wrench,
  Package,
  StickyNote,
  BookOpen,
  Users,
  FolderOpen,
  Ship,
} from 'lucide-react'
import type { Project, RiskEvent } from '@/types'
import {
  PROJECT_TYPE_LABELS,
  PROJECT_STATUS_LABELS,
  RISK_LEVEL_LABELS,
} from '@/lib/constants'
import { formatDate } from '@/lib/utils'

export default function Dashboard() {
  const { data: projects } = useApiGet<Project[]>('/projects')
  const { data: risks } = useApiGet<RiskEvent[]>('/risks/summary')

  const stats = [
    {
      label: '活跃项目',
      value: projects?.filter(
        (p) => p.status === 'active'
      ).length ?? 0,
      icon: ClipboardList,
      color: 'text-primary',
    },
    {
      label: '已完成项目',
      value: projects?.filter(
        (p) => p.status === 'completed'
      ).length ?? 0,
      icon: TrendingUp,
      color: 'text-secondary',
    },
    {
      label: '风险预警',
      value: risks?.length ?? 0,
      icon: AlertTriangle,
      color: 'text-accent',
    },
    {
      label: '项目总数',
      value: projects?.length ?? 0,
      icon: FolderOpen,
      color: 'text-foreground',
    },
  ]

  const modules = [
    {
      name: '监修项目',
      description: '船舶监修过程管理',
      icon: Ship,
      href: '/supervision',
      color: 'from-blue-500 to-blue-600',
    },
    {
      name: '买卖经纪',
      description: '船舶买卖经纪业务',
      icon: FileText,
      href: '/brokerage/sale',
      color: 'from-emerald-500 to-emerald-600',
    },
    {
      name: '修船经纪',
      description: '修船项目经纪管理',
      icon: Wrench,
      href: '/brokerage/repair',
      color: 'from-amber-500 to-amber-600',
    },
    {
      name: '备件供应',
      description: '备件采购与供应链',
      icon: Package,
      href: '/spare-parts',
      color: 'from-purple-500 to-purple-600',
    },
    {
      name: '随手存',
      description: '快速记录与备忘',
      icon: StickyNote,
      href: '/quick-save',
      color: 'from-pink-500 to-pink-600',
    },
    {
      name: 'RAG 知识库',
      description: '智能文档问答',
      icon: BookOpen,
      href: '/knowledge',
      color: 'from-cyan-500 to-cyan-600',
    },
    {
      name: '客户名录',
      description: '客户信息管理',
      icon: Users,
      href: '/customers',
      color: 'from-indigo-500 to-indigo-600',
    },
    {
      name: '文件中心',
      description: '项目文件管理',
      icon: FolderOpen,
      href: '/files',
      color: 'from-teal-500 to-teal-600',
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">工作台</h1>
          <p className="text-muted-foreground mt-1">
            欢迎回来,这里是您的项目总览
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label} className="shadow-card">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">
                    {stat.label}
                  </p>
                  <p className="mt-2 text-3xl font-bold">{stat.value}</p>
                </div>
                <div
                  className={`rounded-lg bg-surface-muted p-3 ${stat.color}`}
                >
                  <stat.icon className="h-6 w-6" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2 shadow-card">
          <CardHeader>
            <CardTitle>最近项目</CardTitle>
          </CardHeader>
          <CardContent>
            {projects && projects.length > 0 ? (
              <div className="space-y-3">
                {projects.slice(0, 5).map((project) => (
                  <div
                    key={project.id}
                    className="flex items-center justify-between rounded-lg border border-border p-4 hover:bg-surface-muted transition-colors"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{project.ship_name}</span>
                        <Badge variant="secondary">
                          {PROJECT_TYPE_LABELS[project.type]}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        编号 {project.project_no} · 创建于 {formatDate(project.created_at)}
                      </p>
                    </div>
                    <Badge
                      variant={
                        project.status === 'active'
                          ? 'default'
                          : project.status === 'completed'
                            ? 'secondary'
                            : 'destructive'
                      }
                    >
                      {PROJECT_STATUS_LABELS[project.status]}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="py-8 text-center text-muted-foreground">
                暂无项目数据
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="shadow-card">
          <CardHeader>
            <CardTitle>风险预警</CardTitle>
          </CardHeader>
          <CardContent>
            {risks && risks.length > 0 ? (
              <div className="space-y-3">
                {risks.slice(0, 5).map((risk) => (
                  <div
                    key={risk.id}
                    className="rounded-lg border border-border p-4"
                  >
                    <div className="flex items-center justify-between">
                      <Badge
                        variant={
                          risk.risk_level === 'critical'
                            ? 'destructive'
                            : risk.risk_level === 'warning'
                              ? 'accent'
                              : 'secondary'
                        }
                      >
                        {RISK_LEVEL_LABELS[risk.risk_level] || risk.risk_level}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {formatDate(risk.created_at)}
                      </span>
                    </div>
                    <p className="mt-2 text-sm">{risk.title}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
                <AlertTriangle className="mb-2 h-8 w-8 text-secondary" />
                <p>暂无风险预警</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div>
        <h2 className="mb-4 text-xl font-semibold">快捷入口</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {modules.map((module) => (
            <a
              key={module.name}
              href={module.href}
              className="group rounded-xl border border-border bg-white p-5 shadow-card transition-all hover:shadow-card-hover hover:-translate-y-0.5"
            >
              <div
                className={`inline-flex rounded-lg bg-gradient-to-br ${module.color} p-3 text-white shadow-sm`}
              >
                <module.icon className="h-6 w-6" />
              </div>
              <h3 className="mt-3 font-semibold group-hover:text-primary transition-colors">
                {module.name}
              </h3>
              <p className="mt-1 text-sm text-muted-foreground">
                {module.description}
              </p>
            </a>
          ))}
        </div>
      </div>
    </div>
  )
}