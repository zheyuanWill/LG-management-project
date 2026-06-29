/**
 * General Utilities - Unified Export
 *
 * Re-exports all utility functions from specialized modules
 * and provides additional general-purpose helpers.
 */

// Date utilities
export {
  formatDate,
  formatRelativeTime,
  isOverdue,
  daysRemaining,
  getDateRange,
  parseDate,
  toISODateString,
} from './date'

// String utilities
export {
  generateId,
  generateOrderNo,
  generateQuoteNo,
  generateContractNo,
  generateProcurementNo,
  truncate,
  capitalize,
  toKebabCase,
  toCamelCase,
  toSnakeCase,
  formatFileSize,
  parseFileName,
  getMimeType,
  isImageFile,
  maskPhone,
  maskBankAccount,
  maskEmail,
} from './string'

// Validation utilities
export {
  isValidPhone,
  isValidEmail,
  isValidIdCard,
  isValidTaxId,
  isValidBankAccount,
  isValidHsCode,
  isValidImoNumber,
  isRequired,
  isInRange,
  isPositive,
  isNonNegative,
  isInteger,
  isLengthInRange,
  createValidator,
  type ValidationResult,
} from './validation'

/**
 * Debounce function
 */
export const debounce = <T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay: number,
): ((...args: Parameters<T>) => void) => {
  let timer: ReturnType<typeof setTimeout> | null = null
  return (...args: Parameters<T>) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }
}

/**
 * Throttle function
 */
export const throttle = <T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay: number,
): ((...args: Parameters<T>) => void) => {
  let lastTime = 0
  return (...args: Parameters<T>) => {
    const now = Date.now()
    if (now - lastTime >= delay) {
      lastTime = now
      fn(...args)
    }
  }
}

/**
 * Deep clone object
 */
export const deepClone = <T>(obj: T): T => {
  if (obj === null || typeof obj !== 'object') return obj
  return JSON.parse(JSON.stringify(obj))
}

/**
 * Check if value is empty (null, undefined, empty string, empty array, empty object)
 */
export const isEmpty = (value: unknown): boolean => {
  if (value === null || value === undefined) return true
  if (typeof value === 'string') return value.trim() === ''
  if (Array.isArray(value)) return value.length === 0
  if (typeof value === 'object') return Object.keys(value).length === 0
  return false
}

/**
 * Sleep for a specified number of milliseconds
 */
export const sleep = (ms: number): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, ms))

/**
 * Omit specified keys from an object
 */
export const omit = <T extends Record<string, unknown>, K extends keyof T>(
  obj: T,
  keys: K[],
): Omit<T, K> => {
  const result = { ...obj }
  for (const key of keys) {
    delete result[key]
  }
  return result
}

/**
 * Pick specified keys from an object
 */
export const pick = <T extends Record<string, unknown>, K extends keyof T>(
  obj: T,
  keys: K[],
): Pick<T, K> => {
  const result = {} as Pick<T, K>
  for (const key of keys) {
    if (key in obj) {
      result[key] = obj[key]
    }
  }
  return result
}
