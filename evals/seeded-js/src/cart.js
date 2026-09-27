export function maxQuantity(lines) {
  return Math.max(...lines.map((line) => line.qty));
}
