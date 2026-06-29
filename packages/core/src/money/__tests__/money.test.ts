import { describe, it, expect } from 'vitest'
import { formatMoney, parseMoney, Currency, currencySymbols, currencyNames } from '../index'

describe('formatMoney', () => {
  it('formats CNY correctly', () => {
    const result = formatMoney(12345.67, Currency.CNY)
    expect(result).toContain('¥')
    expect(result).toContain('12,345.67')
  })

  it('formats USD correctly', () => {
    const result = formatMoney(1000, Currency.USD)
    expect(result).toContain('$')
  })

  it('handles null/undefined', () => {
    expect(formatMoney(null)).toContain('0')
    expect(formatMoney(undefined)).toContain('0')
  })

  it('handles string amounts', () => {
    const result = formatMoney('99.99')
    expect(result).toContain('99.99')
  })

  it('respects showSymbol option', () => {
    const result = formatMoney(100, Currency.CNY, { showSymbol: false })
    expect(result).not.toContain('¥')
  })

  it('respects decimals option', () => {
    const result = formatMoney(100, Currency.CNY, { decimals: 0 })
    expect(result).not.toContain('.')
  })
})

describe('parseMoney', () => {
  it('parses money strings', () => {
    expect(parseMoney('¥12,345.67')).toBe(12345.67)
    expect(parseMoney('$1,000')).toBe(1000)
    expect(parseMoney('abc')).toBe(0)
  })
})

describe('Currency enums', () => {
  it('has all currencies defined', () => {
    expect(Currency.CNY).toBe('CNY')
    expect(Currency.USD).toBe('USD')
    expect(Currency.EUR).toBe('EUR')
    expect(Currency.JPY).toBe('JPY')
    expect(Currency.HKD).toBe('HKD')
  })

  it('has symbols for all currencies', () => {
    expect(currencySymbols[Currency.CNY]).toBe('¥')
    expect(currencySymbols[Currency.USD]).toBe('$')
    expect(currencySymbols[Currency.EUR]).toBe('€')
  })

  it('has names for all currencies', () => {
    expect(currencyNames[Currency.CNY]).toBe('人民币')
    expect(currencyNames[Currency.USD]).toBe('美元')
  })
})
