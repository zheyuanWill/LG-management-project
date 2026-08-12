import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import zh from 'dayjs/locale/zh-cn'
import { DATE_FORMAT, DATE_TIME_FORMAT } from './constants'

dayjs.extend(relativeTime)
dayjs.locale(zh)

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(
  date: string | Date | undefined | null,
  format: string = DATE_FORMAT
): string {
  if (!date) return '-'
  return dayjs(date).format(format)
}

export function formatDateTime(
  date: string | Date | undefined | null,
  format: string = DATE_TIME_FORMAT
): string {
  if (!date) return '-'
  return dayjs(date).format(format)
}

export function formatRelativeTime(
  date: string | Date | undefined | null
): string {
  if (!date) return '-'
  return dayjs(date).fromNow()
}

export function formatCurrency(
  value: number | undefined | null,
  currency: string = 'CNY'
): string {
  if (value == null) return '-'
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
  }).format(value)
}

export function formatNumber(
  value: number | undefined | null,
  decimals: number = 0
): string {
  if (value == null) return '-'
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

/**
 * Strip markdown formatting and render as plain text.
 * Removes headers (#, ##, ###), bold (**), list markers (-, *, ---),
 * and converts to readable plain text.
 */
export function stripMarkdown(text: string): string {
  if (!text) return ''
  return text
    .replace(/^#{1,6}\s+/gm, '')        // remove headers
    .replace(/\*\*(.+?)\*\*/g, '$1')     // remove bold **text** → text
    .replace(/\*(.+?)\*/g, '$1')         // remove italic *text* → text
    .replace(/^-+\s*/gm, '')             // remove list markers at start of line
    .replace(/^\s*---+\s*$/gm, '')       // remove horizontal rules
    .replace(/\n{3,}/g, '\n\n')          // collapse multiple blank lines
    .trim()
}