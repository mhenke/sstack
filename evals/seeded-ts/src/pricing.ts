export interface LineItem {
  unitPrice: number;
  qty: number;
  discount?: number;
}

export function lineTotal(item: LineItem): number {
  const discount = item.discount ?? 0;
  return Math.round(item.unitPrice * item.qty * (1 - discount) * 100) / 100;
}

export function parseOrder(raw: string): LineItem[] {
  return JSON.parse(raw) as LineItem[];
}

export function applyCoupon(price: number, discountPct: number): number {
  // DEFECT: floating-point arithmetic without rounding to cents
  // 10.10 * 0.70 = 7.069999999999999, not 7.07
  return price * (1 - discountPct / 100);
}
