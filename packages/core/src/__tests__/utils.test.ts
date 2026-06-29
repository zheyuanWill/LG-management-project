import { describe, it, expect } from 'vitest'
import {
  formatDate,
  formatRelativeTime,
  isOverdue,
  daysRemaining,
  formatFileSize,
  truncate,
  capitalize,
  toKebabCase,
  toCamelCase,
  toSnakeCase,
  isValidPhone,
  isValidEmail,
  isValidIdCard,
  isRequired,
  isInRange,
  isPositive,
  isNonNegative,
  isInteger,
  createValidator,
  debounce,
  throttle,
  deepClone,
  isEmpty,
  omit,
  pick,
  maskPhone,
  maskEmail,
  generateId,
  parseFileName,
  isImageFile,
} from '../utils'

describe('formatDate', () => {
  it('formats date correctly', () => {
    const result = formatDate('2024-03-15', 'date')
    expect(result).toContain('2024')
  })

  it('returns - for invalid date', () => {
    expect(formatDate('invalid', 'date')).toBe('-')
  })
})

describe('formatFileSize', () => {
  it('formats bytes', () => {
    expect(formatFileSize(0)).toBe('0 B')
    expect(formatFileSize(1024)).toBe('1 KB')
    expect(formatFileSize(1048576)).toBe('1 MB')
  })
})

describe('string utils', () => {
  it('truncate', () => {
    expect(truncate('hello world', 8)).toBe('hello...')
    expect(truncate('short', 10)).toBe('short')
  })

  it('capitalize', () => {
    expect(capitalize('hello')).toBe('Hello')
    expect(capitalize('')).toBe('')
  })

  it('case conversions', () => {
    expect(toKebabCase('helloWorld')).toBe('hello-world')
    expect(toCamelCase('hello-world')).toBe('helloWorld')
    expect(toSnakeCase('helloWorld')).toBe('hello_world')
  })

  it('parseFileName', () => {
    expect(parseFileName('test.pdf')).toEqual({ name: 'test', ext: 'pdf' })
    expect(parseFileName('noext')).toEqual({ name: 'noext', ext: '' })
  })

  it('isImageFile', () => {
    expect(isImageFile('photo.jpg')).toBe(true)
    expect(isImageFile('doc.pdf')).toBe(false)
  })

  it('generateId', () => {
    const id = generateId()
    expect(id).toBeTruthy()
    expect(typeof id).toBe('string')
  })
})

describe('validation', () => {
  it('isValidPhone', () => {
    expect(isValidPhone('13800138000')).toBe(true)
    expect(isValidPhone('12345')).toBe(false)
  })

  it('isValidEmail', () => {
    expect(isValidEmail('test@example.com')).toBe(true)
    expect(isValidEmail('invalid')).toBe(false)
  })

  it('isRequired', () => {
    expect(isRequired('')).toBe(false)
    expect(isRequired(null)).toBe(false)
    expect(isRequired('hello')).toBe(true)
  })

  it('numeric validators', () => {
    expect(isInRange(5, 1, 10)).toBe(true)
    expect(isInRange(15, 1, 10)).toBe(false)
    expect(isPositive(5)).toBe(true)
    expect(isPositive(-1)).toBe(false)
    expect(isNonNegative(0)).toBe(true)
    expect(isInteger(5)).toBe(true)
    expect(isInteger(5.5)).toBe(false)
  })

  it('createValidator', () => {
    const validate = createValidator<{ name: string; age: number }>([
      { field: 'name', check: (v) => typeof v === 'string' && v !== '', message: 'Name required' },
      { field: 'age', check: (v) => typeof v === 'number' && v > 0, message: 'Age must be positive' },
    ])
    expect(validate({ name: 'John', age: 25 })).toEqual({ valid: true, errors: [] })
    expect(validate({ name: '', age: -1 })).toEqual({ valid: false, errors: ['Name required', 'Age must be positive'] })
  })
})

describe('general utils', () => {
  it('deepClone', () => {
    const obj = { a: 1, b: { c: 2 } }
    const clone = deepClone(obj)
    expect(clone).toEqual(obj)
    expect(clone).not.toBe(obj)
    expect(clone.b).not.toBe(obj.b)
  })

  it('isEmpty', () => {
    expect(isEmpty(null)).toBe(true)
    expect(isEmpty(undefined)).toBe(true)
    expect(isEmpty('')).toBe(true)
    expect(isEmpty([])).toBe(true)
    expect(isEmpty({})).toBe(true)
    expect(isEmpty('hello')).toBe(false)
    expect(isEmpty([1])).toBe(false)
  })

  it('omit', () => {
    const obj = { a: 1, b: 2, c: 3 }
    expect(omit(obj, ['b'])).toEqual({ a: 1, c: 3 })
  })

  it('pick', () => {
    const obj = { a: 1, b: 2, c: 3 }
    expect(pick(obj, ['a', 'c'])).toEqual({ a: 1, c: 3 })
  })

  it('maskPhone', () => {
    expect(maskPhone('13800138000')).toBe('138****8000')
  })

  it('maskEmail', () => {
    expect(maskEmail('test@example.com')).toBe('te***@example.com')
  })
})

describe('debounce', () => {
  it('delays function execution', async () => {
    let callCount = 0
    const fn = debounce(() => { callCount++ }, 50)

    fn()
    fn()
    fn()

    expect(callCount).toBe(0)
    await new Promise((r) => setTimeout(r, 80))
    expect(callCount).toBe(1)
  })

  it('resets timer on subsequent calls', async () => {
    let callCount = 0
    const fn = debounce(() => { callCount++ }, 50)

    fn()
    await new Promise((r) => setTimeout(r, 30))
    fn() // Reset timer

    await new Promise((r) => setTimeout(r, 30))
    expect(callCount).toBe(0) // Should not have fired yet

    await new Promise((r) => setTimeout(r, 40))
    expect(callCount).toBe(1)
  })
})

describe('throttle', () => {
  it('limits function execution frequency', () => {
    let callCount = 0
    const fn = throttle(() => { callCount++ }, 100)

    fn()
    fn()
    fn()

    expect(callCount).toBe(1) // Only first call should execute
  })

  it('allows execution after delay', async () => {
    let callCount = 0
    const fn = throttle(() => { callCount++ }, 50)

    fn()
    expect(callCount).toBe(1)

    await new Promise((r) => setTimeout(r, 60))
    fn()
    expect(callCount).toBe(2)
  })
})
