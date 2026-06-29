import { App } from 'antd'
import { useCallback } from 'react'

export function useErrorHandler() {
  const { message, notification } = App.useApp()

  const handleError = useCallback(
    (error: unknown, fallbackMessage = '操作失败') => {
      if (error instanceof Error) {
        if (error.message === 'cancel') return
        message.error(error.message || fallbackMessage)
      } else if (typeof error === 'string') {
        if (error === 'cancel') return
        message.error(error)
      } else {
        message.error(fallbackMessage)
      }
    },
    [message],
  )

  const handleSuccess = useCallback(
    (msg: string) => {
      message.success(msg)
    },
    [message],
  )

  const handleWarning = useCallback(
    (msg: string) => {
      message.warning(msg)
    },
    [message],
  )

  const notify = useCallback(
    (title: string, description: string, type: 'success' | 'warning' | 'info' | 'error' = 'info') => {
      notification[type]({ message: title, description })
    },
    [notification],
  )

  return { handleError, handleSuccess, handleWarning, notify }
}
