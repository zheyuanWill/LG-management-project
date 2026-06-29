import { describe, it, expect } from 'vitest'
import { formatMoney, Currency, parseMoney, currencySymbols } from '../money'

describe('formatMoney', () => {
  it('formats CNY', () => {
    expect(formatMoney(1234.56)).toBe('¥1,234.56')
  })

  it('formats USD', () => {
    expect(formatMoney(1000, Currency.USD)).toBe('$1,000.00')
  })

  it('handles null/undefined', () => {
    expect(formatMoney(null)).toBe('¥0.00')
    expect(formatMoney(undefined)).toBe('¥0.00')
  })

  it('handles string amount', () => {
    expect(formatMoney('2500.5')).toBe('¥2,500.50')
  })

  it('respects options', () => {
    expect(formatMoney(1000, Currency.CNY, { showSymbol: false })).toBe('1,000.00')
    expect(formatMoney(1000, Currency.CNY, { decimals: 0 })).toBe('¥1,000')
  })
})

describe('parseMoney', () => {
  it('parses formatted money string', () => {
    expect(parseMoney('¥1,234.56')).toBe(1234.56)
    expect(parseMoney('$100')).toBe(100)
  })
})

describe('currencySymbols', () => {
  it('has all currencies', () => {
    expect(currencySymbols[Currency.CNY]).toBe('¥')
    expect(currencySymbols[Currency.USD]).toBe('$')
    expect(currencySymbols[Currency.EUR]).toBe('€')
  })
})
