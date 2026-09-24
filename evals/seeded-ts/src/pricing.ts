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
