export interface CartLine {
  id: string;
  qty: number;
}

export function totalQuantity(lines: CartLine[]): number {
  return lines.reduce((acc, l) => acc + l.qty, 0);
}

export function maxQuantity(lines: CartLine[]): number {
  return Math.max(...lines.map((l) => l.qty));
}
