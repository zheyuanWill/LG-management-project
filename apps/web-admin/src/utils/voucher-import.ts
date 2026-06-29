/**
 * Voucher generation from LG accounting base-table Excel.
 *
 * Recognized sheets → voucher generation rules:
 *   取得发票--内采  → AP (domestic purchase)
 *   取得发票--外采  → AP (foreign purchase + customs)
 *   开具发票--内销  → AR (domestic sales)
 *   开具发票--外销  → AR (foreign sales)
 *   银行            → Bank receipts / payments
 */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type R = Record<string, any>
type Row = unknown[]

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

export interface VoucherEntry {
  accountNumber: string
  explanation: string
  dc: 1 | -1
  amountFor: number
  cur?: string
  rate?: number
  projectCode?: string
  supplierCode?: string
  customerCode?: string
  departmentCode?: string
  employeeCode?: string
}

export interface VoucherDraft {
  date: string
  groupName: string
  explanation: string
  attachments: number
  entries: VoucherEntry[]
  source: string
  warnings?: string[]
}

export type SheetType =
  | 'dom-purchase'
  | 'fgn-purchase'
  | 'dom-sales'
  | 'fgn-sales'
  | 'bank'

export interface DetectedSheet {
  name: string
  type: SheetType
  label: string
  rowCount: number
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function excelDate(v: unknown): string {
  if (typeof v === 'number' && v > 40000 && v < 60000) {
    const d = new Date((v - 25569) * 86400000)
    const y = d.getUTCFullYear()
    const m = String(d.getUTCMonth() + 1).padStart(2, '0')
    const day = String(d.getUTCDate()).padStart(2, '0')
    return `${y}-${m}-${day}`
  }
  const s = String(v ?? '')
  if (/^\d{4}-\d{2}-\d{2}/.test(s)) return s.slice(0, 10)
  return s
}

function r2(n: number): number {
  return Math.round((n + Number.EPSILON) * 100) / 100
}

function num(v: unknown): number {
  if (typeof v === 'number') return v
  const n = Number(v)
  return isNaN(n) ? 0 : n
}

function str(v: unknown): string {
  const s = String(v ?? '').trim()
  return s === '#N/A' || s === '#REF!' || s === '#VALUE!' || s === '-' || s === '—' || s === '/' ? '' : s
}

function col(headers: Row, ...keywords: string[]): number {
  return headers.findIndex(h => {
    const s = String(h ?? '').replace(/[\r\n\s]+/g, '')
    return keywords.some(k => s.includes(k))
  })
}

function colExact(headers: Row, keyword: string): number {
  return headers.findIndex(h => {
    const s = String(h ?? '').replace(/[\r\n\s]+/g, '')
    return s === keyword
  })
}

function groupBy(rows: Row[], keyIdx: number): Map<string, Row[]> {
  const m = new Map<string, Row[]>()
  for (const r of rows) {
    const k = str(r[keyIdx])
    if (!k) continue
    if (!m.has(k)) m.set(k, [])
    m.get(k)!.push(r)
  }
  return m
}

/* ------------------------------------------------------------------ */
/*  Default counter-party account numbers                              */
/* ------------------------------------------------------------------ */

const ACCT = {
  inputVAT: '2221010101',        // 进项税额_货物（明细科目）
  importVAT: '2221010103',       // 进口增值税
  importDuty: '222122',          // 进口关税（辅助核算：项目）
  outputVAT: '22210107',         // 销项税额
  apRMB: '22020101',             // 应付账款_人民币（辅助核算：项目+供应商）
  apFGN: '22020102',             // 应付账款_外币（辅助核算：项目+供应商）
  arRMB: '112201',               // 应收账款_人民币（辅助核算：客户+项目）
  arFGN: '112202',               // 应收账款_外币（辅助核算：客户+项目）
}

const BANK_MAP: R = {
  '建R': '10020101', '建行R': '10020101',
  '建U': '10020102', '建行U': '10020102',
  '交R': '10020201', '交行R': '10020201',
  '宁R': '10020301', '宁波R': '10020301',
  '宁U': '10020302', '宁波U': '10020302',
}

const FGN_BANK_ACCOUNTS = new Set(['10020102', '10020302'])

/* ------------------------------------------------------------------ */
/*  Sheet detection                                                    */
/* ------------------------------------------------------------------ */

const SHEET_MAP: { pattern: string; type: SheetType; label: string }[] = [
  { pattern: '取得发票--内采', type: 'dom-purchase', label: '取得发票 (国内采购)' },
  { pattern: '取得发票--外采', type: 'fgn-purchase', label: '取得发票 (国外采购)' },
  { pattern: '开具发票--内销', type: 'dom-sales', label: '开具发票 (国内销售)' },
  { pattern: '开具发票--外销', type: 'fgn-sales', label: '开具发票 (国外销售)' },
  { pattern: '银行', type: 'bank', label: '银行收付款' },
]

export function detectSheets(sheetNames: string[]): DetectedSheet[] {
  const result: DetectedSheet[] = []
  for (const sn of sheetNames) {
    const m = SHEET_MAP.find(s => sn.includes(s.pattern))
    if (m) result.push({ name: sn, type: m.type, label: m.label, rowCount: 0 })
  }
  return result
}

/* ------------------------------------------------------------------ */
/*  取得发票--内采 (Domestic Purchase)                                   */
/* ------------------------------------------------------------------ */

function processDomPurchase(data: Row[]): VoucherDraft[] {
  if (data.length < 2) return []
  const h = data[0]
  const iInvoice = col(h, '发票号码')
  const iDate = col(h, '开票日期')
  const iDeduct = col(h, '进项抵扣')
  const iAmtExTax = col(h, '发票金额')
  const iTax = col(h, '税额')
  const iTotal = col(h, '价税合计')
  const iSummary = col(h, '入账摘要')
  const iAcct = col(h, '科目编码')
  const iSupplier = col(h, '供应商代码')
  const iProject = col(h, '项目代码')
  const iDept = col(h, '部门代码')

  if (iInvoice < 0 || iAcct < 0) return []

  const groups = groupBy(data.slice(1), iInvoice)
  const vouchers: VoucherDraft[] = []

  for (const [inv, rows] of groups) {
    const first = rows[0]
    const date = excelDate(first[iDate])
    if (!date) continue
    const entries: VoucherEntry[] = []
    const warnings: string[] = []
    let creditTotal = 0

    for (const r of rows) {
      const acct = str(r[iAcct])
      const summary = str(r[iSummary])
      const exTax = num(r[iAmtExTax])
      const tax = num(r[iTax])
      const total = num(r[iTotal])
      const deductible = str(r[iDeduct]) === '抵扣'
      if (!acct) {
        const rawAcct = String(r[iAcct] ?? '')
        if (rawAcct === '#N/A' || rawAcct === '#REF!' || rawAcct === '#VALUE!') {
          warnings.push(`发票 ${inv}: 科目编码为 ${rawAcct}（公式错误），该行已跳过`)
        }
        continue
      }

      const aux = {
        projectCode: str(r[iProject]),
        supplierCode: str(r[iSupplier]),
        departmentCode: str(r[iDept]),
      }

      if (deductible && exTax) {
        entries.push({ accountNumber: acct, explanation: summary, dc: 1, amountFor: r2(exTax), ...aux })
        if (tax) {
          entries.push({ accountNumber: ACCT.inputVAT, explanation: summary, dc: 1, amountFor: r2(tax) })
        }
        creditTotal += total || (exTax + tax)
      } else {
        const amt = total || exTax
        if (amt) {
          entries.push({ accountNumber: acct, explanation: summary, dc: 1, amountFor: r2(amt), ...aux })
          creditTotal += amt
        }
      }
    }

    if (entries.length > 0 && creditTotal > 0) {
      entries.push({
        accountNumber: ACCT.apRMB,
        explanation: `应付-${inv}`,
        dc: -1,
        amountFor: r2(creditTotal),
        supplierCode: str(first[iSupplier]),
        projectCode: str(first[iProject]),
        departmentCode: str(first[iDept]),
      })
      vouchers.push({
        date, groupName: '记',
        explanation: str(first[iSummary]) || `内采-${inv}`,
        attachments: 0, entries, source: '取得发票--内采',
        ...(warnings.length > 0 ? { warnings } : {}),
      })
    } else if (warnings.length > 0) {
      vouchers.push({
        date, groupName: '记',
        explanation: str(first[iSummary]) || `内采-${inv}`,
        attachments: 0, entries: [], source: '取得发票--内采',
        warnings,
      })
    }
  }
  return vouchers
}

/* ------------------------------------------------------------------ */
/*  取得发票--外采 (Foreign Purchase)                                    */
/* ------------------------------------------------------------------ */

function processFgnPurchase(data: Row[]): VoucherDraft[] {
  if (data.length < 2) return []
  const h = data[0]
  const iInvoice = col(h, '发票号码')
  const iDate = col(h, '开票日期')
  const iCur = col(h, '原币')
  const iFgnAmt = col(h, '发票金额')
  const iRate = col(h, '海关汇率', '汇率')
  const iRMB = col(h, '人民币金额')
  const iDuty = col(h, '关税')
  const iVAT = col(h, '增值税')
  const iSummary = col(h, '入账摘要')
  const iAcct = col(h, '科目编码')
  const iSupplier = col(h, '供应商代码')
  const iProject = col(h, '项目代码')
  const iDept = col(h, '部门代码')

  if (iInvoice < 0 || iAcct < 0) return []

  const groups = groupBy(data.slice(1), iInvoice)
  const vouchers: VoucherDraft[] = []

  for (const [inv, rows] of groups) {
    const first = rows[0]
    const date = excelDate(first[iDate])
    if (!date) continue
    const entries: VoucherEntry[] = []
    let costRmbSum = 0
    let fgnTotal = 0
    let dutyTotal = 0
    let vatTotal = 0
    const currency = iCur >= 0 ? str(first[iCur]) : ''
    const rate = iRate >= 0 ? num(first[iRate]) : 1
    let lastCostIdx = -1

    for (const r of rows) {
      const acct = str(r[iAcct])
      const summary = str(r[iSummary])
      const rmb = num(r[iRMB])
      const fgnAmt = iFgnAmt >= 0 ? num(r[iFgnAmt]) : 0
      const duty = num(r[iDuty])
      const vat = num(r[iVAT])
      if (!acct || !rmb) continue

      const rounded = r2(rmb)
      lastCostIdx = entries.length
      entries.push({
        accountNumber: acct, explanation: summary, dc: 1, amountFor: rounded,
        projectCode: str(r[iProject]),
        supplierCode: str(r[iSupplier]),
        departmentCode: str(r[iDept]),
      })
      costRmbSum += rounded
      fgnTotal += fgnAmt
      dutyTotal += duty
      vatTotal += vat
    }

    if (dutyTotal > 0) {
      entries.push({ accountNumber: ACCT.importDuty, explanation: `进口关税-${inv}`, dc: 1, amountFor: r2(dutyTotal), projectCode: str(first[iProject]) })
    }
    if (vatTotal > 0) {
      entries.push({ accountNumber: ACCT.importVAT, explanation: `进口增值税-${inv}`, dc: 1, amountFor: r2(vatTotal) })
    }

    if (entries.length > 0 && costRmbSum > 0) {
      const isFgn = currency && currency !== 'RMB' && fgnTotal > 0 && rate > 0
      const taxTotal = r2(dutyTotal + vatTotal)

      if (isFgn) {
        const apRmbEquiv = r2(r2(fgnTotal) * rate)
        const diff = r2(apRmbEquiv - r2(costRmbSum))
        if (diff !== 0 && lastCostIdx >= 0) {
          entries[lastCostIdx].amountFor = r2(entries[lastCostIdx].amountFor + diff)
        }

        entries.push({
          accountNumber: ACCT.apFGN,
          explanation: `应付外币-${inv}`,
          dc: -1,
          amountFor: r2(fgnTotal),
          cur: currency,
          rate: rate,
          supplierCode: str(first[iSupplier]),
          projectCode: str(first[iProject]),
          departmentCode: str(first[iDept]),
        })

        if (taxTotal > 0) {
          entries.push({
            accountNumber: ACCT.apRMB,
            explanation: `应付关税增值税-${inv}`,
            dc: -1,
            amountFor: taxTotal,
            supplierCode: str(first[iSupplier]),
            projectCode: str(first[iProject]),
          })
        }
      } else {
        entries.push({
          accountNumber: ACCT.apFGN,
          explanation: `应付外币-${inv}`,
          dc: -1,
          amountFor: r2(costRmbSum + dutyTotal + vatTotal),
          supplierCode: str(first[iSupplier]),
          projectCode: str(first[iProject]),
          departmentCode: str(first[iDept]),
        })
      }

      vouchers.push({
        date, groupName: '记',
        explanation: str(first[iSummary]) || `外采-${inv}`,
        attachments: 0, entries, source: '取得发票--外采',
      })
    }
  }
  return vouchers
}

/* ------------------------------------------------------------------ */
/*  开具发票--内销 (Domestic Sales)                                      */
/* ------------------------------------------------------------------ */

function processDomSales(data: Row[]): VoucherDraft[] {
  if (data.length < 2) return []
  const h = data[0]
  const iInvoice = col(h, '发票号码')
  const iDate = col(h, '开票日期')
  const iAmtExTax = col(h, '发票金额')
  const iTax = col(h, '税额')
  const iTotal = col(h, '价税合计')
  const iSummary = col(h, '入账摘要')
  const iAcct = col(h, '科目编码')
  const iCustomer = col(h, '客户代码')
  const iProject = col(h, '项目代码')
  const iDept = col(h, '部门代码')

  if (iInvoice < 0 || iAcct < 0) return []

  const groups = groupBy(data.slice(1), iInvoice)
  const vouchers: VoucherDraft[] = []

  for (const [inv, rows] of groups) {
    const first = rows[0]
    const date = excelDate(first[iDate])
    if (!date) continue
    const entries: VoucherEntry[] = []
    let debitTotal = 0
    let taxTotal = 0

    for (const r of rows) {
      const acct = str(r[iAcct])
      const summary = str(r[iSummary])
      const exTax = num(r[iAmtExTax])
      const tax = num(r[iTax])
      const total = num(r[iTotal])
      if (!acct || !exTax) continue

      entries.push({
        accountNumber: acct, explanation: summary, dc: -1, amountFor: r2(exTax),
        projectCode: str(r[iProject]),
        customerCode: str(r[iCustomer]),
        departmentCode: str(r[iDept]),
      })
      debitTotal += total || (exTax + tax)
      taxTotal += tax
    }

    if (taxTotal > 0) {
      entries.push({ accountNumber: ACCT.outputVAT, explanation: `销项税-${inv}`, dc: -1, amountFor: r2(taxTotal) })
    }

    if (entries.length > 0 && debitTotal > 0) {
      entries.unshift({
        accountNumber: ACCT.arRMB,
        explanation: `应收-${inv}`,
        dc: 1,
        amountFor: r2(debitTotal),
        customerCode: str(first[iCustomer]),
        projectCode: str(first[iProject]),
        departmentCode: str(first[iDept]),
      })
      vouchers.push({
        date, groupName: '记',
        explanation: str(first[iSummary]) || `内销-${inv}`,
        attachments: 0, entries, source: '开具发票--内销',
      })
    }
  }
  return vouchers
}

/* ------------------------------------------------------------------ */
/*  开具发票--外销 (Foreign Sales)                                       */
/* ------------------------------------------------------------------ */

function processFgnSales(data: Row[]): VoucherDraft[] {
  if (data.length < 2) return []
  const h = data[0]
  const iInvoice = col(h, '发票号码')
  const iDate = col(h, '开票日期')
  const iCur = col(h, '原币')
  const iFgnAmt = col(h, '发票金额')
  const iRate = col(h, '汇率')
  const iRMB = col(h, '折人民币')
  const iSummary = col(h, '入账摘要')
  const iAcct = col(h, '科目编码')
  const iCustomer = col(h, '客户代码')
  const iProject = col(h, '项目代码')
  const iDept = col(h, '部门代码')

  if (iInvoice < 0 || iAcct < 0) return []

  const groups = groupBy(data.slice(1), iInvoice)
  const vouchers: VoucherDraft[] = []

  for (const [inv, rows] of groups) {
    const first = rows[0]
    const date = excelDate(first[iDate])
    if (!date) continue
    const entries: VoucherEntry[] = []
    let entryRmbSum = 0
    let fgnTotal = 0
    const currency = iCur >= 0 ? str(first[iCur]) : ''
    const rate = iRate >= 0 ? num(first[iRate]) : 1

    for (const r of rows) {
      const acct = str(r[iAcct])
      const summary = str(r[iSummary])
      const rmb = num(r[iRMB])
      const fgnAmt = iFgnAmt >= 0 ? num(r[iFgnAmt]) : 0
      if (!acct || !rmb) continue

      const rounded = r2(rmb)
      entries.push({
        accountNumber: acct, explanation: summary, dc: -1, amountFor: rounded,
        projectCode: str(r[iProject]),
        customerCode: str(r[iCustomer]),
        departmentCode: str(r[iDept]),
      })
      entryRmbSum += rounded
      fgnTotal += fgnAmt
    }

    if (entries.length > 0 && entryRmbSum > 0) {
      const isFgn = currency && currency !== 'RMB' && fgnTotal > 0 && rate > 0

      if (isFgn) {
        const arRmbEquiv = r2(r2(fgnTotal) * rate)
        const diff = r2(arRmbEquiv - r2(entryRmbSum))
        if (diff !== 0 && entries.length > 0) {
          entries[entries.length - 1].amountFor = r2(entries[entries.length - 1].amountFor + diff)
        }
      }

      entries.unshift({
        accountNumber: ACCT.arFGN,
        explanation: `应收外币-${inv}`,
        dc: 1,
        amountFor: isFgn ? r2(fgnTotal) : r2(entryRmbSum),
        cur: isFgn ? currency : undefined,
        rate: isFgn ? rate : undefined,
        customerCode: str(first[iCustomer]),
        projectCode: str(first[iProject]),
        departmentCode: str(first[iDept]),
      })
      vouchers.push({
        date, groupName: '记',
        explanation: str(first[iSummary]) || `外销-${inv}`,
        attachments: 0, entries, source: '开具发票--外销',
      })
    }
  }
  return vouchers
}

/* ------------------------------------------------------------------ */
/*  银行 (Bank)                                                        */
/* ------------------------------------------------------------------ */

function processBank(data: Row[]): VoucherDraft[] {
  if (data.length < 2) return []
  const h = data[0]
  const iRef = col(h, '银行回单编码')
  const iDate = col(h, '交易日期')
  const iType = col(h, '交易类型')
  const iBank = col(h, '交易银行')
  const iCur = col(h, '币种')
  const iAmt = col(h, '拆分金额')
  const iRate = col(h, '汇率')
  const iRMB = col(h, '折人民币')
  const iSummary = col(h, '入账摘要')
  const iAcct = col(h, '科目编码')
  const iSupplier = colExact(h, '供应商代码')
  const iCustomer = colExact(h, '客户代码')
  const iProject = colExact(h, '项目编码')
  const iDept = colExact(h, '部门代码')
  const iEmployee = colExact(h, '职员代码')

  if (iRef < 0 || iAcct < 0) return []

  const groups = groupBy(data.slice(1), iRef)
  const vouchers: VoucherDraft[] = []

  for (const [ref, rows] of groups) {
    const first = rows[0]
    const date = excelDate(first[iDate])
    if (!date) continue
    const txType = str(first[iType])
    const isPay = txType.includes('付')
    const bankKey = str(first[iBank])
    const bankAcct = BANK_MAP[bankKey] || Object.entries(BANK_MAP).find(([k]) => bankKey.startsWith(k))?.[1]
    if (!bankAcct) continue

    const isFgnBank = FGN_BANK_ACCOUNTS.has(bankAcct)
    const currency = isFgnBank && iCur >= 0 ? str(first[iCur]) : ''
    const rate = isFgnBank && iRate >= 0 ? num(first[iRate]) : 1
    const hasFgn = isFgnBank && currency && currency !== 'RMB' && rate > 0

    // Detect inter-bank foreign exchange (结汇/购汇): an RMB bank whose
    // counter-party is a foreign-currency bank account.  The foreign bank's
    // own row already produces the correct USD/JPY/EUR entry, so generating
    // a duplicate voucher from the RMB side would double-count.
    if (!isFgnBank) {
      const counterAcct = str(first[iAcct])
      if (FGN_BANK_ACCOUNTS.has(counterAcct)) continue
    }

    const entries: VoucherEntry[] = []
    let entryRmbSum = 0
    let fgnTotal = 0

    for (const r of rows) {
      const acct = str(r[iAcct])
      const summary = str(r[iSummary])
      const splitAmt = num(r[iAmt])
      const rmbAmt = num(r[iRMB]) || splitAmt
      if (!acct || !rmbAmt) continue

      // Normalise negative amounts: flip debit/credit instead of booking
      // a negative figure, which Kingdee may reject.
      let dc: 1 | -1 = isPay ? 1 : -1
      let amt = r2(rmbAmt)
      if (amt < 0) { dc = (dc * -1) as 1 | -1; amt = -amt }

      entries.push({
        accountNumber: acct,
        explanation: summary,
        dc,
        amountFor: amt,
        projectCode: str(r[iProject]),
        supplierCode: str(r[iSupplier]),
        customerCode: str(r[iCustomer]),
        departmentCode: str(r[iDept]),
        employeeCode: str(r[iEmployee]),
      })
      entryRmbSum += r2(rmbAmt)
      if (hasFgn) fgnTotal += splitAmt
    }

    if (entries.length > 0 && entryRmbSum > 0) {
      if (hasFgn && fgnTotal > 0) {
        const bankRmbEquiv = r2(r2(fgnTotal) * rate)
        const diff = r2(bankRmbEquiv - r2(entryRmbSum))
        if (diff !== 0 && entries.length > 0) {
          entries[entries.length - 1].amountFor = r2(entries[entries.length - 1].amountFor + diff)
        }
      }

      entries.push({
        accountNumber: bankAcct,
        explanation: `${isPay ? '付' : '收'}-${ref}`,
        dc: isPay ? -1 : 1,
        amountFor: hasFgn && fgnTotal > 0 ? r2(fgnTotal) : r2(entryRmbSum),
        cur: hasFgn && fgnTotal > 0 ? currency : undefined,
        rate: hasFgn && fgnTotal > 0 ? rate : undefined,
      })
      vouchers.push({
        date, groupName: '记',
        explanation: str(first[iSummary]) || `银行${isPay ? '付' : '收'}-${ref}`,
        attachments: 0, entries, source: '银行',
      })
    }
  }
  return vouchers
}

/* ------------------------------------------------------------------ */
/*  Public API                                                         */
/* ------------------------------------------------------------------ */

const PROCESSORS: Record<SheetType, (data: Row[]) => VoucherDraft[]> = {
  'dom-purchase': processDomPurchase,
  'fgn-purchase': processFgnPurchase,
  'dom-sales': processDomSales,
  'fgn-sales': processFgnSales,
  'bank': processBank,
}

export function processSheet(type: SheetType, data: Row[]): VoucherDraft[] {
  const fn = PROCESSORS[type]
  return fn ? fn(data) : []
}

const FOREIGN_CURRENCY_WHITELIST = new Set([
  ACCT.apFGN,    // 22020102 应付账款_外币
  ACCT.arFGN,    // 112202   应收账款_外币
  '10020102',    // 建U 建行外币
  '10020302',    // 宁U 宁波银行外币
])

export function toKingdeePayload(draft: VoucherDraft) {
  const yearPeriod = parseInt(draft.date.slice(0, 4) + draft.date.slice(5, 7), 10)
  return {
    date: draft.date,
    group_name: draft.groupName,
    explanation: draft.explanation,
    attachments: draft.attachments,
    year_period: yearPeriod,
    entries: draft.entries.map(e => {
      const wantsFgn = e.cur && e.cur !== 'RMB' && FOREIGN_CURRENCY_WHITELIST.has(e.accountNumber)
      const entry: Record<string, unknown> = {
        acctNo: e.accountNumber,
        dc: e.dc,
        exp: e.explanation,
        currency: wantsFgn ? e.cur : 'RMB',
        rate: wantsFgn ? (e.rate || 1) : 1,
        amount: e.amountFor,
      }
      if (e.supplierCode) entry.suppNo = e.supplierCode
      if (e.customerCode) entry.custNo = e.customerCode
      if (e.departmentCode) entry.deptNo = e.departmentCode
      if (e.employeeCode) entry.empNo = e.employeeCode
      if (e.projectCode) entry.projectNo = e.projectCode
      return entry
    }),
  }
}
