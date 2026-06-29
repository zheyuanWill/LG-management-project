import { Alert } from 'react-native'

export function getErrorMessage(error: unknown, fallback = '操作失败，请稍后重试'): string {
  if (error instanceof Error) return error.message
  if (typeof error === 'string') return error
  return fallback
}

export function showError(error: unknown, fallback?: string): void {
  const msg = getErrorMessage(error, fallback)
  Alert.alert('提示', msg)
}

export function logError(context: string, error: unknown): void {
  if (__DEV__) {
    console.error(`[${context}]`, error)
  }
}
