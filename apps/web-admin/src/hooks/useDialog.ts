import { useState, useCallback } from 'react'

export function useDialog<T extends Record<string, unknown>>(defaultForm: T) {
  const [visible, setVisible] = useState(false)
  const [title, setTitle] = useState('')
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState<T>({ ...defaultForm })
  const [isEdit, setIsEdit] = useState(false)

  const open = useCallback(
    (dialogTitle: string, data?: Partial<T>) => {
      setTitle(dialogTitle)
      setIsEdit(!!data)
      setForm({ ...defaultForm, ...data })
      setVisible(true)
    },
    [defaultForm],
  )

  const close = useCallback(() => {
    setVisible(false)
    setLoading(false)
  }, [])

  const resetForm = useCallback(() => {
    setForm({ ...defaultForm })
  }, [defaultForm])

  const updateForm = useCallback((patch: Partial<T>) => {
    setForm((prev) => ({ ...prev, ...patch }))
  }, [])

  return { visible, title, loading, setLoading, form, isEdit, open, close, resetForm, updateForm }
}
