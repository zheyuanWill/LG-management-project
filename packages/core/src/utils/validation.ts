/**
 * Validation Utilities
 */

/**
 * 验证手机号
 */
export function isValidPhone(phone: string): boolean {
  return /^1[3-9]\d{9}$/.test(phone)
}

/**
 * 验证邮箱
 */
export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

/**
 * 验证身份证号
 */
export function isValidIdCard(idCard: string): boolean {
  return /^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$/.test(idCard)
}

/**
 * 验证统一社会信用代码
 */
export function isValidTaxId(taxId: string): boolean {
  return /^[0-9A-HJ-NPQRTUWXY]{2}\d{6}[0-9A-HJ-NPQRTUWXY]{10}$/.test(taxId)
}

/**
 * 验证银行账号（基本验证）
 */
export function isValidBankAccount(account: string): boolean {
  return /^\d{16,19}$/.test(account.replace(/\s/g, ''))
}

/**
 * 验证 HS 编码
 */
export function isValidHsCode(code: string): boolean {
  return /^\d{8,10}$/.test(code)
}

/**
 * 验证 IMO 编号
 */
export function isValidImoNumber(imo: string): boolean {
  return /^IMO\s?\d{7}$/i.test(imo)
}

/**
 * 验证必填字段
 */
export function isRequired(value: unknown): boolean {
  if (value === null || value === undefined) return false
  if (typeof value === 'string') return value.trim().length > 0
  if (Array.isArray(value)) return value.length > 0
  return true
}

/**
 * 验证数值范围
 */
export function isInRange(value: number, min: number, max: number): boolean {
  return value >= min && value <= max
}

/**
 * 验证正数
 */
export function isPositive(value: number): boolean {
  return value > 0
}

/**
 * 验证非负数
 */
export function isNonNegative(value: number): boolean {
  return value >= 0
}

/**
 * 验证整数
 */
export function isInteger(value: number): boolean {
  return Number.isInteger(value)
}

/**
 * 验证字符串长度
 */
export function isLengthInRange(value: string, min: number, max: number): boolean {
  const len = value.length
  return len >= min && len <= max
}

/**
 * 验证结果类型
 */
export interface ValidationResult {
  valid: boolean
  errors: string[]
}

/**
 * 创建验证器
 */
export function createValidator<T>(
  rules: Array<{
    field: keyof T
    check: (value: unknown) => boolean
    message: string
  }>
) {
  return (data: T): ValidationResult => {
    const errors: string[] = []

    for (const rule of rules) {
      const value = data[rule.field]
      if (!rule.check(value)) {
        errors.push(rule.message)
      }
    }

    return {
      valid: errors.length === 0,
      errors
    }
  }
}

