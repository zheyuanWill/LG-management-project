import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import { ConfigProvider, App as AntdApp, theme as antdTheme } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { configureHttp } from '@lg/api-client'
import { useAuthStore } from '@lg/react-hooks'
import { routeTree } from './routeTree.gen'
import { useThemeStore } from './stores/themeStore'
import './styles/global.css'

configureHttp({
  onUnauthorized: () => {
    useAuthStore.getState().logout()
    window.location.href = '/login'
  },
})

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

const router = createRouter({
  routeTree,
  context: { auth: undefined! },
  defaultPreload: 'intent',
})

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

function InnerApp() {
  const auth = useAuthStore()
  const isDark = useThemeStore((s) => s.isDark)

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: isDark ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
        token: {
          colorPrimary: '#1677ff',
          borderRadius: 6,
        },
      }}
    >
      <AntdApp>
        <RouterProvider router={router} context={{ auth }} />
      </AntdApp>
    </ConfigProvider>
  )
}

function AppRoot() {
  React.useEffect(() => {
    useAuthStore.getState().init()
  }, [])

  return (
    <QueryClientProvider client={queryClient}>
      <InnerApp />
    </QueryClientProvider>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AppRoot />
  </React.StrictMode>
)
