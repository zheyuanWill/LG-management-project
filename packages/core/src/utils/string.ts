/**
 * String Utilities
 */

/**
 * 生成随机 ID
 */
export function generateId(prefix: string = ''): string {
  const timestamp = Date.now().toString(36)
  const random = Math.random().toString(36).substring(2, 8)
  return prefix ? `${prefix}_${timestamp}${random}` : `${timestamp}${random}`
}

/**
 * 生成订单号
 */
export function generateOrderNo(prefix: string = 'ORD'): string {
  const date = new Date()
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const random = String(Math.floor(Math.random() * 10000)).padStart(4, '0')
  return `${prefix}${year}${month}${day}${random}`
}

/**
 * 生成报价单号
 */
export function generateQuoteNo(prefix: string = 'QUO'): string {
  return generateOrderNo(prefix)
}

/**
 * 生成合同号
 */
export function generateContractNo(prefix: string = 'CON'): string {
  return generateOrderNo(prefix)
}

/**
 * 生成采购单号
 */
export function generateProcurementNo(prefix: string = 'PUR'): string {
  return generateOrderNo(prefix)
}

/**
 * 截断文本
 */
export function truncate(text: string, length: number, suffix: string = '...'): string {
  if (text.length <= length) return text
  return text.substring(0, length - suffix.length) + suffix
}

/**
 * 首字母大写
 */
export function capitalize(text: string): string {
  if (!text) return ''
  return text.charAt(0).toUpperCase() + text.slice(1)
}

/**
 * 转换为 kebab-case
 */
export function toKebabCase(text: string): string {
  return text
    .replace(/([a-z])([A-Z])/g, '$1-$2')
    .replace(/[\s_]+/g, '-')
    .toLowerCase()
}

/**
 * 转换为 camelCase
 */
export function toCamelCase(text: string): string {
  return text
    .replace(/[-_\s]+(.)?/g, (_, c) => (c ? c.toUpperCase() : ''))
    .replace(/^(.)/, c => c.toLowerCase())
}

/**
 * 转换为 snake_case
 */
export function toSnakeCase(text: string): string {
  return text
    .replace(/([a-z])([A-Z])/g, '$1_$2')
    .replace(/[\s-]+/g, '_')
    .toLowerCase()
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'

  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const k = 1024
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + units[i]
}

/**
 * 解析文件名和扩展名
 */
export function parseFileName(fileName: string): { name: string; ext: string } {
  const lastDot = fileName.lastIndexOf('.')
  if (lastDot === -1) {
    return { name: fileName, ext: '' }
  }
  return {
    name: fileName.substring(0, lastDot),
    ext: fileName.substring(lastDot + 1).toLowerCase()
  }
}

/**
 * 获取 MIME 类型
 */
export function getMimeType(ext: string): string {
  const mimeTypes: Record<string, string> = {
    jpg: 'image/jpeg',
    jpeg: 'image/jpeg',
    png: 'image/png',
    gif: 'image/gif',
    webp: 'image/webp',
    pdf: 'application/pdf',
    doc: 'application/msword',
    docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    xls: 'application/vnd.ms-excel',
    xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    zip: 'application/zip',
    rar: 'application/x-rar-compressed'
  }
  return mimeTypes[ext.toLowerCase()] || 'application/octet-stream'
}

/**
 * 是否为图片类型
 */
export function isImageFile(fileName: string): boolean {
  const { ext } = parseFileName(fileName)
  return ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'].includes(ext)
}

/**
 * 脱敏手机号
 */
export function maskPhone(phone: string): string {
  if (!phone || phone.length < 7) return phone
  return phone.substring(0, 3) + '****' + phone.substring(phone.length - 4)
}

/**
 * 脱敏银行账号
 */
export function maskBankAccount(account: string): string {
  if (!account || account.length < 8) return account
  return account.substring(0, 4) + ' **** **** ' + account.substring(account.length - 4)
}

/**
 * 脱敏邮箱
 */
export function maskEmail(email: string): string {
  const [name, domain] = email.split('@')
  if (!domain) return email
  const maskedName = name.length > 2 ? name.substring(0, 2) + '***' : name
  return `${maskedName}@${domain}`
}

