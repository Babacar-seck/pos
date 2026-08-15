import { TranslateService } from '@ngx-translate/core';
import { intlLocaleFromTranslate } from './intl-locale';

/**
 * Stripe's documented zero-decimal currencies: the stored integer amount IS the whole unit
 * (e.g. 1500 XOF = 1500 francs, not 15.00). Mirrors back/app/tenant_currency.py.
 * See CONTEXT.md: "Devise sans décimales".
 */
export const ZERO_DECIMAL_CURRENCIES = new Set([
  'BIF',
  'CLP',
  'DJF',
  'GNF',
  'JPY',
  'KMF',
  'KRW',
  'MGA',
  'PYG',
  'RWF',
  'UGX',
  'VND',
  'VUV',
  'XAF',
  'XOF',
  'XPF',
]);

/** Stripe's documented three-decimal currencies (thousandths). */
export const THREE_DECIMAL_CURRENCIES = new Set(['BHD', 'JOD', 'KWD', 'OMR', 'TND']);

/** Decimal places conventionally used by an ISO 4217 code. */
export function defaultDecimalPlaces(currencyCode: string | null | undefined): number {
  const code = (currencyCode || '').trim().toUpperCase();
  if (ZERO_DECIMAL_CURRENCIES.has(code)) return 0;
  if (THREE_DECIMAL_CURRENCIES.has(code)) return 3;
  return 2;
}

/** Explicit tenant override wins; otherwise derive from currency_code. */
export function resolveDecimalPlaces(
  currencyCode: string | null | undefined,
  currencyDecimalPlaces: number | null | undefined,
): number {
  return currencyDecimalPlaces ?? defaultDecimalPlaces(currencyCode);
}

/** Stored integer amount -> display number (1234, 2 -> 12.34; 1234, 0 -> 1234). */
export function toDisplayAmount(minorUnits: number, decimalPlaces: number): number {
  return minorUnits / Math.pow(10, decimalPlaces);
}

/** Display number -> stored integer amount, rounded to the nearest unit. */
export function toMinorUnits(displayAmount: number, decimalPlaces: number): number {
  return Math.round(displayAmount * Math.pow(10, decimalPlaces));
}

/** Full Intl-formatted money string (symbol + correct decimal places for the currency). */
export function formatMoney(
  translate: TranslateService,
  minorUnits: number,
  currencyCode: string,
  decimalPlaces: number,
): string {
  const locale = intlLocaleFromTranslate(translate);
  const amount = toDisplayAmount(minorUnits, decimalPlaces);
  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: currencyCode,
      currencyDisplay: 'symbol',
      minimumFractionDigits: decimalPlaces,
      maximumFractionDigits: decimalPlaces,
    }).format(amount);
  } catch {
    return amount.toLocaleString(locale, {
      minimumFractionDigits: decimalPlaces,
      maximumFractionDigits: decimalPlaces,
    });
  }
}
