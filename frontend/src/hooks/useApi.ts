import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
  type UseMutationOptions,
} from '@tanstack/react-query'
import apiClient from '@/lib/api'

function maybeUnwrap<T>(data: T): T {
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    const d = data as Record<string, unknown>
    if (Array.isArray(d.items)) {
      return d.items as unknown as T
    }
    if (Array.isArray(d.value)) {
      return d.value as unknown as T
    }
  }
  return data
}

export function useApiGet<T>(
  url: string,
  options?: Omit<UseQueryOptions<T>, 'queryKey' | 'queryFn'> & {
    params?: Record<string, unknown>
  }
) {
  const { params, ...queryOptions } = options || {}
  return useQuery<T>({
    queryKey: [url, params],
    queryFn: async () => {
      const response = await apiClient.get<T>(url, { params })
      return maybeUnwrap(response.data)
    },
    ...queryOptions,
  })
}

export function useApiPost<T>(
  url: string,
  options?: Omit<UseMutationOptions<T, unknown, unknown>, 'mutationFn'>
) {
  const queryClient = useQueryClient()
  return useMutation<T, unknown, unknown>({
    mutationFn: async (body) => {
      const response = await apiClient.post<T>(url, body)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [url] })
    },
    ...options,
  })
}

export function useApiPatch<T>(
  url: string,
  options?: Omit<UseMutationOptions<T, unknown, unknown>, 'mutationFn'>
) {
  const queryClient = useQueryClient()
  return useMutation<T, unknown, unknown>({
    mutationFn: async (body) => {
      const response = await apiClient.patch<T>(url, body)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [url] })
    },
    ...options,
  })
}

export function useApiPut<T>(
  url: string,
  options?: Omit<UseMutationOptions<T, unknown, unknown>, 'mutationFn'>
) {
  const queryClient = useQueryClient()
  return useMutation<T, unknown, unknown>({
    mutationFn: async (body) => {
      const response = await apiClient.put<T>(url, body)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [url] })
    },
    ...options,
  })
}

export function useApiDelete<T = void>(
  url: string,
  options?: Omit<UseMutationOptions<T, unknown, string>, 'mutationFn'>
) {
  const queryClient = useQueryClient()
  return useMutation<T, unknown, string>({
    mutationFn: async (id) => {
      const response = await apiClient.delete<T>(`${url}/${id}`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [url] })
    },
    ...options,
  })
}