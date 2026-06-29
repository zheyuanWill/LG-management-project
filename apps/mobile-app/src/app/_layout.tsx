import { useEffect } from 'react'
import { Stack } from 'expo-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { PaperProvider, MD3LightTheme } from 'react-native-paper'
import { StatusBar } from 'expo-status-bar'
import { useAuthStore } from '../stores/authStore'
import { setupApi } from '../utils/api'

setupApi()

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
})

const theme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    primary: '#1677ff',
    secondary: '#52c41a',
  },
}

export default function RootLayout() {
  const init = useAuthStore((s) => s.init)

  useEffect(() => {
    init()
  }, [init])

  return (
    <QueryClientProvider client={queryClient}>
      <PaperProvider theme={theme}>
        <StatusBar style="dark" />
        <Stack screenOptions={{ headerShown: false }}>
          <Stack.Screen name="(auth)" />
          <Stack.Screen name="(tabs)" />
          <Stack.Screen name="project/[id]" options={{ headerShown: true, title: '项目详情' }} />
          <Stack.Screen name="approval/index" options={{ headerShown: true, title: '审批中心' }} />
          <Stack.Screen name="upload/index" options={{ headerShown: true, title: '上传附件' }} />
          <Stack.Screen name="settings/index" options={{ headerShown: true, title: '设置' }} />
          <Stack.Screen name="help/index" options={{ headerShown: true, title: '帮助与反馈' }} />
        </Stack>
      </PaperProvider>
    </QueryClientProvider>
  )
}
