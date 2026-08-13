import { create } from 'zustand'
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react'
import { cn } from '@/lib/utils'

type ToastVariant = 'default' | 'success' | 'error' | 'warning' | 'info'

interface Toast {
  id: string
  title?: string
  description?: string
  variant: ToastVariant
  duration?: number
}

interface ToastStore {
  toasts: Toast[]
  addToast: (toast: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void
}

export const useToast = create<ToastStore>((set) => ({
  toasts: [],
  addToast: (toast) => {
    const id = Math.random().toString(36).substring(2, 9)
    const newToast: Toast = { ...toast, id, duration: toast.duration ?? 4000 }
    set((state) => ({ toasts: [...state.toasts, newToast] }))
    if (toast.duration > 0) {
      setTimeout(() => {
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id),
        }))
      }, toast.duration)
    }
  },
  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),
}))

const variantIcons = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
  default: Info,
}

const variantStyles = {
  success: 'border-secondary/50 bg-secondary/10 text-secondary',
  error: 'border-destructive/50 bg-destructive/10 text-destructive',
  warning: 'border-accent/50 bg-accent/10 text-accent',
  info: 'border-primary/50 bg-primary/10 text-primary',
  default: 'border-border bg-surface text-foreground',
}

export function ToastProvider() {
  const { toasts, removeToast } = useToast()

  return (
    <div className="fixed bottom-0 right-0 z-[100] flex max-h-screen w-full flex-col-reverse gap-2 p-4 sm:bottom-4 sm:right-4 sm:top-auto sm:w-96">
      {toasts.map((toast) => {
        const Icon = variantIcons[toast.variant]
        return (
          <div
            key={toast.id}
            className={cn(
              'pointer-events-auto relative flex w-full items-start gap-3 rounded-lg border p-4 shadow-lg animate-fade-in',
              variantStyles[toast.variant]
            )}
          >
            <Icon className="mt-0.5 h-5 w-5 shrink-0" />
            <div className="flex-1">
              {toast.title && (
                <p className="text-sm font-semibold">{toast.title}</p>
              )}
              {toast.description && (
                <p className="mt-0.5 text-sm opacity-90">
                  {toast.description}
                </p>
              )}
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              className="shrink-0 rounded-md opacity-50 transition-opacity hover:opacity-100"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )
      })}
    </div>
  )
}

export function toast(props: Omit<Toast, 'id'>) {
  const { addToast } = useToast.getState()
  addToast({ duration: 4000, variant: 'default', ...props })
}

toast.success = (props: Omit<Toast, 'id' | 'variant'>) =>
  useToast.getState().addToast({ ...props, variant: 'success', duration: 4000 })

toast.error = (props: Omit<Toast, 'id' | 'variant'>) =>
  useToast.getState().addToast({ ...props, variant: 'error', duration: 4000 })

toast.warning = (props: Omit<Toast, 'id' | 'variant'>) =>
  useToast.getState().addToast({ ...props, variant: 'warning', duration: 4000 })

toast.info = (props: Omit<Toast, 'id' | 'variant'>) =>
  useToast.getState().addToast({ ...props, variant: 'info', duration: 4000 })