import { describe, it, expect } from 'vitest'
import { formatDate, isOverdue, daysRemaining, toISODateString, parseDate } from '../date'
import { formatFileSize, truncate, capitalize, toKebabCase, toCamelCase, toSnakeCase, generateId, parseFileName, isImageFile, maskPhone, maskEmail } from '../string'
import { isValidPhone, isValidEmail, isRequired, isPositive, isNonNegative, isInRange, createValidator } from '../validation'

// Date utilities
describe('formatDate', () => {
  it('formats date correctly', () => {
    const date = new Date('2024-03-15T10:30:00')
    const result = formatDate(date, 'date')
    expect(result).toContain('2024')
  })

  it('returns dash for invalid date', () => {
    expect(formatDate('invalid', 'date')).toBe('-')
  })
})

describe('isOverdue', () => {
  it('returns true for past dates', () => {
    expect(isOverdue('2020-01-01')).toBe(true)
  })

  it('returns false for future dates', () => {
    const futureDate = new Date()
    futureDate.setFullYear(futureDate.getFullYear() + 1)
    expect(isOverdue(futureDate)).toBe(false)
  })
})

describe('daysRemaining', () => {
  it('returns negative for past dates', () => {
    const pastDate = new Date()
    pastDate.setDate(pastDate.getDate() - 5)
    expect(daysRemaining(pastDate)).toBeLessThan(0)
  })

  it('returns positive for future dates', () => {
    const futureDate = new Date()
    futureDate.setDate(futureDate.getDate() + 5)
    expect(daysRemaining(futureDate)).toBeGreaterThan(0)
  })
})

describe('parseDate', () => {
  it('parses valid date string', () => {
    const result = parseDate('2024-01-15')
    expect(result).toBeInstanceOf(Date)
  })

  it('returns null for invalid date', () => {
    expect(parseDate('not-a-date')).toBeNull()
  })
})

describe('toISODateString', () => {
  it('formats date to ISO string without time', () => {
    const date = new Date('2024-03-15T10:30:00Z')
    expect(toISODateString(date)).toBe('2024-03-15')
  })
})

// String utilities
describe('formatFileSize', () => {
  it('formats bytes correctly', () => {
    expect(formatFileSize(0)).toBe('0 B')
    expect(formatFileSize(1024)).toBe('1 KB')
    expect(formatFileSize(1048576)).toBe('1 MB')
    expect(formatFileSize(1073741824)).toBe('1 GB')
  })
})

describe('truncate', () => {
  it('truncates long text', () => {
    expect(truncate('Hello World', 8)).toBe('Hello...')
  })

  it('does not truncate short text', () => {
    expect(truncate('Hi', 10)).toBe('Hi')
  })
})

describe('capitalize', () => {
  it('capitalizes first letter', () => {
    expect(capitalize('hello')).toBe('Hello')
  })

  it('returns empty for empty string', () => {
    expect(capitalize('')).toBe('')
  })
})

describe('case conversions', () => {
  it('converts to kebab-case', () => {
    expect(toKebabCase('helloWorld')).toBe('hello-world')
  })

  it('converts to camelCase', () => {
    expect(toCamelCase('hello-world')).toBe('helloWorld')
  })

  it('converts to snake_case', () => {
    expect(toSnakeCase('helloWorld')).toBe('hello_world')
  })
})

describe('generateId', () => {
  it('generates unique IDs', () => {
    const id1 = generateId()
    const id2 = generateId()
    expect(id1).not.toBe(id2)
  })

  it('adds prefix when provided', () => {
    const id = generateId('test')
    expect(id).toMatch(/^test_/)
  })
})

describe('parseFileName', () => {
  it('parses name and extension', () => {
    expect(parseFileName('photo.jpg')).toEqual({ name: 'photo', ext: 'jpg' })
  })

  it('handles no extension', () => {
    expect(parseFileName('README')).toEqual({ name: 'README', ext: '' })
  })
})

describe('isImageFile', () => {
  it('detects image files', () => {
    expect(isImageFile('photo.jpg')).toBe(true)
    expect(isImageFile('photo.png')).toBe(true)
    expect(isImageFile('doc.pdf')).toBe(false)
  })
})

describe('maskPhone', () => {
  it('masks phone number', () => {
    expect(maskPhone('13800138000')).toBe('138****8000')
  })
})

describe('maskEmail', () => {
  it('masks email', () => {
    const result = maskEmail('test@example.com')
    expect(result).toContain('***')
    expect(result).toContain('@example.com')
  })
})

// Validation utilities
describe('isValidPhone', () => {
  it('validates Chinese phone numbers', () => {
    expect(isValidPhone('13800138000')).toBe(true)
    expect(isValidPhone('12345')).toBe(false)
    expect(isValidPhone('23800138000')).toBe(false)
  })
})

describe('isValidEmail', () => {
  it('validates email addresses', () => {
    expect(isValidEmail('test@example.com')).toBe(true)
    expect(isValidEmail('invalid')).toBe(false)
    expect(isValidEmail('a@b.c')).toBe(true)
  })
})

describe('isRequired', () => {
  it('checks required values', () => {
    expect(isRequired(null)).toBe(false)
    expect(isRequired(undefined)).toBe(false)
    expect(isRequired('')).toBe(false)
    expect(isRequired('  ')).toBe(false)
    expect(isRequired('hello')).toBe(true)
    expect(isRequired(0)).toBe(true)
    expect(isRequired([])).toBe(false)
    expect(isRequired([1])).toBe(true)
  })
})

describe('number validators', () => {
  it('isPositive', () => {
    expect(isPositive(1)).toBe(true)
    expect(isPositive(0)).toBe(false)
    expect(isPositive(-1)).toBe(false)
  })

  it('isNonNegative', () => {
    expect(isNonNegative(0)).toBe(true)
    expect(isNonNegative(1)).toBe(true)
    expect(isNonNegative(-1)).toBe(false)
  })

  it('isInRange', () => {
    expect(isInRange(5, 1, 10)).toBe(true)
    expect(isInRange(0, 1, 10)).toBe(false)
    expect(isInRange(11, 1, 10)).toBe(false)
  })
})

describe('createValidator', () => {
  it('validates data against rules', () => {
    interface TestData { name: string; age: number }
    const validate = createValidator<TestData>([
      { field: 'name', check: (v) => typeof v === 'string' && (v as string).length > 0, message: 'Name is required' },
      { field: 'age', check: (v) => typeof v === 'number' && (v as number) > 0, message: 'Age must be positive' },
    ])

    expect(validate({ name: 'John', age: 30 })).toEqual({ valid: true, errors: [] })
    expect(validate({ name: '', age: -1 })).toEqual({
      valid: false,
      errors: ['Name is required', 'Age must be positive'],
    })
  })
})
