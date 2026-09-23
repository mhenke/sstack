export interface CartLine {
  id: string;
  qty: number;
}

export function totalQuantity(lines: CartLine[]): number {
  return lines.reduce((acc, l) => acc + l.qty);
}
