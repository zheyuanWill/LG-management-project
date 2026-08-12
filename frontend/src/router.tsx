import {
  createRootRoute,
  createRoute,
  createRouter,
  Navigate,
} from '@tanstack/react-router'
import RootLayout from '@/routes/__root'
import Dashboard from '@/routes/dashboard'
import Login from '@/routes/login'
import SupervisionIndex from '@/routes/supervision/index'
import SupervisionDetail from '@/routes/supervision/$id'
import DailyReportPage from '@/routes/supervision/$id/daily.$date'
import BrokerageSaleIndex from '@/routes/brokerage-sale/index'
import BrokerageSaleDetail from '@/routes/brokerage-sale/$id'
import BrokerageRepairIndex from '@/routes/brokerage-repair/index'
import BrokerageRepairDetail from '@/routes/brokerage-repair/$id'
import SparePartsIndex from '@/routes/spare-parts/index'
import SparePartsDetail from '@/routes/spare-parts/$id'
import QuickSavePage from '@/routes/quick-save'
import KnowledgePage from '@/routes/knowledge'
import CustomersPage from '@/routes/customers'
import FilesPage from '@/routes/files'
import NewProjectPage from '@/routes/new-project'

const rootRoute = createRootRoute({
  component: RootLayout,
})

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: Login,
})

const dashboardRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/dashboard',
  component: Dashboard,
})

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: () => <Navigate to="/dashboard" />,
})

const supervisionRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/supervision',
  component: SupervisionIndex,
})

const supervisionDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/supervision/$id',
  component: SupervisionDetail,
})

const dailyReportRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/supervision/$id/daily/$date',
  component: DailyReportPage,
})

const brokerageSaleRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/brokerage-sale',
  component: BrokerageSaleIndex,
})

const brokerageSaleDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/brokerage-sale/$id',
  component: BrokerageSaleDetail,
})

const brokerageRepairRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/brokerage-repair',
  component: BrokerageRepairIndex,
})

const brokerageRepairDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/brokerage-repair/$id',
  component: BrokerageRepairDetail,
})

const sparePartsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/spare-parts',
  component: SparePartsIndex,
})

const sparePartsDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/spare-parts/$id',
  component: SparePartsDetail,
})

const quickSaveRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/quick-save',
  component: QuickSavePage,
})

const knowledgeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/knowledge',
  component: KnowledgePage,
})

const customersRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/customers',
  component: CustomersPage,
})

const filesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/files',
  component: FilesPage,
})

const newProjectRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/new',
  component: NewProjectPage,
})

const routeTree = rootRoute.addChildren([
  indexRoute,
  loginRoute,
  dashboardRoute,
  supervisionRoute,
  supervisionDetailRoute,
  dailyReportRoute,
  brokerageSaleRoute,
  brokerageSaleDetailRoute,
  brokerageRepairRoute,
  brokerageRepairDetailRoute,
  sparePartsRoute,
  sparePartsDetailRoute,
  quickSaveRoute,
  knowledgeRoute,
  customersRoute,
  filesRoute,
  newProjectRoute,
])

export const router = createRouter({
  routeTree,
  defaultPreload: 'intent',
  defaultPendingComponent: () => (
    <div className="flex h-full items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  ),
})

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}