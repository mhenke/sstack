export function lineTotal(item) {
  const discount = item.discount ?? 0;
  return Math.round(item.unitPrice * item.qty * (1 - discount) * 100) / 100;
}

export function parseOrder(raw) {
  return JSON.parse(raw);
}
