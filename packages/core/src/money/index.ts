/**
 * Money and Currency Utilities
 */

export enum Currency {
  CNY = 'CNY',
  USD = 'USD',
  EUR = 'EUR',
  JPY = 'JPY',
  HKD = 'HKD'
}

export const currencySymbols: Record<Currency, string> = {
  [Currency.CNY]: '¥',
  [Currency.USD]: '$',
  [Currency.EUR]: '€',
  [Currency.JPY]: '¥',
  [Currency.HKD]: 'HK$'
}

export const currencyNames: Record<Currency, string> = {
  [Currency.CNY]: '人民币',
  [Currency.USD]: '美元',
  [Currency.EUR]: '欧元',
  [Currency.JPY]: '日元',
  [Currency.HKD]: '港币'
}

/**
 * Format money value
 */
export const formatMoney = (
  amount: number | string | undefined | null,
  currency: Currency = Currency.CNY,
  options?: { showSymbol?: boolean; decimals?: number }
): string => {
  const { showSymbol = true, decimals = 2 } = options || {}
  const value = typeof amount === 'string' ? parseFloat(amount) : (amount ?? 0)
  const formatted = value.toLocaleString('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
  return showSymbol ? `${currencySymbols[currency]}${formatted}` : formatted
}

/**
 * Convert currency
 */
export const convertCurrency = (
  amount: number,
  fromCurrency: Currency,
  toCurrency: Currency,
  rates: Record<string, number>
): number => {
  if (fromCurrency === toCurrency) return amount
  
  // Convert to CNY first, then to target currency
  const rateKey = `${fromCurrency}_${Currency.CNY}`
  const targetRateKey = `${toCurrency}_${Currency.CNY}`
  
  const toCNY = rates[rateKey] ?? 1
  const fromTargetToCNY = rates[targetRateKey] ?? 1
  
  return (amount * toCNY) / fromTargetToCNY
}

/**
 * Parse money string to number
 */
export const parseMoney = (value: string): number => {
  const cleaned = value.replace(/[^\d.-]/g, '')
  return parseFloat(cleaned) || 0
}
