import {
  useQuery, useMutation, useQueryClient,
  type UseQueryResult, type UseMutationResult,
} from '@tanstack/react-query'
import { http } from '@lg/api-client'
import type { PageResponse } from '@lg/api-client'

export function useApiQuery<T>(
  queryKey: unknown[],
  endpoint: string,
  params?: Record<string, unknown>,
  options?: {
    enabled?: boolean
    staleTime?: number
    gcTime?: number
  }
): UseQueryResult<T, Error> {
  return useQuery<T, Error>({
    queryKey,
    queryFn: () => http.get<T>(endpoint, params),
    enabled: options?.enabled,
    staleTime: options?.staleTime,
    gcTime: options?.gcTime,
  })
}

export function usePageQuery<T>(
  queryKey: unknown[],
  endpoint: string,
  params?: Record<string, unknown>,
  options?: {
    enabled?: boolean
    staleTime?: number
  }
): UseQueryResult<PageResponse<T>, Error> {
  return useQuery<PageResponse<T>, Error>({
    queryKey,
    queryFn: () => http.get<PageResponse<T>>(endpoint, params),
    enabled: options?.enabled,
    staleTime: options?.staleTime,
  })
}

export function useApiPost<TData, TVariables = unknown>(
  endpoint: string,
  options?: {
    onSuccess?: (data: TData) => void
    onError?: (error: Error) => void
    invalidateKeys?: unknown[][]
  }
): UseMutationResult<TData, Error, TVariables> {
  const queryClient = useQueryClient()

  return useMutation<TData, Error, TVariables>({
    mutationFn: (variables: TVariables) => http.post<TData>(endpoint, variables),
    onSuccess: (data) => {
      options?.onSuccess?.(data)
      options?.invalidateKeys?.forEach((key) => {
        queryClient.invalidateQueries({ queryKey: key })
      })
    },
    onError: (error: Error) => {
      options?.onError?.(error)
    },
  })
}

export function useApiPut<TData, TVariables = unknown>(
  endpoint: string,
  options?: {
    onSuccess?: (data: TData) => void
    onError?: (error: Error) => void
    invalidateKeys?: unknown[][]
  }
): UseMutationResult<TData, Error, TVariables> {
  const queryClient = useQueryClient()

  return useMutation<TData, Error, TVariables>({
    mutationFn: (variables: TVariables) => http.put<TData>(endpoint, variables),
    onSuccess: (data) => {
      options?.onSuccess?.(data)
      options?.invalidateKeys?.forEach((key) => {
        queryClient.invalidateQueries({ queryKey: key })
      })
    },
    onError: (error: Error) => {
      options?.onError?.(error)
    },
  })
}

export function useApiDelete<TData, TVariables = number | string>(
  endpoint: string,
  options?: {
    onSuccess?: (data: TData) => void
    onError?: (error: Error) => void
    invalidateKeys?: unknown[][]
  }
): UseMutationResult<TData, Error, TVariables> {
  const queryClient = useQueryClient()

  return useMutation<TData, Error, TVariables>({
    mutationFn: (id: TVariables) => http.delete<TData>(`${endpoint}/${id}`),
    onSuccess: (data) => {
      options?.onSuccess?.(data)
      options?.invalidateKeys?.forEach((key) => {
        queryClient.invalidateQueries({ queryKey: key })
      })
    },
    onError: (error: Error) => {
      options?.onError?.(error)
    },
  })
}

export function useInvalidateQueries(): (queryKey: unknown[]) => void {
  const queryClient = useQueryClient()
  return (queryKey: unknown[]) => {
    queryClient.invalidateQueries({ queryKey })
  }
}
