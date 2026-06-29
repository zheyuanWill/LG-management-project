import { configureHttp } from '@lg/api-client'
import { router } from 'expo-router'

const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || 'https://lg-management.zeabur.app/api'

export function setupApi() {
  configureHttp({
    baseUrl: API_BASE_URL,
    onUnauthorized: () => {
      router.replace('/(auth)/login')
    },
  })
}
