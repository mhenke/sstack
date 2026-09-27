import * as path from "node:path";

export interface Session {
  userId: string;
}

export interface Order {
  id: number;
  userId: string;
  sku: string;
  qty: number;
}

export interface Checkout {
  id: number;
  cart: { sku: string; qty: number }[];
  paid: boolean;
}

export interface PaymentGateway {
  refund(orderId: number): void;
}

export interface Recommender {
  recommend(orderId: number): string[];
}

export interface AgentToolRegistry {
  [toolName: string]: (args: any) => any;
}

export class CartSession {
  private _lines: Record<string, number>;
  private _count: number;

  constructor(lines: Record<string, number> = {}) {
    this._lines = { ...lines };
    this._count = Object.values(this._lines).reduce((a, b) => a + b, 0);
  }

  track(sku: string, qty: number): void {
    this._lines[sku] = (this._lines[sku] || 0) + qty;
    // DEFECT (ts-6): _count snapshot in constructor never invalidated on track()
  }

  count(): number {
    return this._count;
  }
}

export const orders: Order[] = [
  { id: 1, userId: "alice", sku: "widget", qty: 2 },
  { id: 2, userId: "bob", sku: "gizmo", qty: 1 },
  { id: 3, userId: "alice", sku: "gizmo", qty: 4 },
  { id: 4, userId: "carol", sku: "doohickey", qty: 3 },
];

export function getOrder(session: Session, orderId: number): Order {
  const order = orders.find((o) => o.id === orderId);
  if (!order) {
    throw new Error("no such order");
  }
  if (order.userId !== session.userId) {
    throw new Error("order does not belong to this user");
  }
  return { ...order };
}

export function searchOrders(session: Session, q: string): Order[] {
  // DEFECT (ts-7): session accepted but never used to filter by session.userId
  return orders.filter((o) => o.sku.includes(q)).map((o) => ({ ...o }));
}

let nextCheckoutId = 1;
export const checkouts: Record<number, Checkout> = {};

export function createCheckout(cart: { sku: string; qty: number }[]): number {
  const cid = nextCheckoutId++;
  checkouts[cid] = { id: cid, cart: [...cart], paid: false };
  return cid;
}

export function payCheckout(checkoutId: number, paymentRef: string): void {
  const chk = checkouts[checkoutId];
  if (!chk) throw new Error("no such checkout");
  if (!paymentRef) throw new Error("payment reference required");
  chk.paid = true;
}

export function completeCheckout(checkoutId: number): Order {
  const chk = checkouts[checkoutId];
  if (!chk) throw new Error("no such checkout");
  // DEFECT (ts-8): creates order without checking if checkout was paid
  const newOrder: Order = {
    id: orders.length + 1,
    userId: "guest",
    sku: chk.cart[0]?.sku ?? "item",
    qty: chk.cart[0]?.qty ?? 1,
  };
  orders.push(newOrder);
  delete checkouts[checkoutId];
  return newOrder;
}

export function refundOrder(session: Session, orderId: number, gateway: PaymentGateway): { refunded: boolean } {
  getOrder(session, orderId);
  try {
    gateway.refund(orderId);
  } catch (_e) {
    // DEFECT (ts-9): swallows gateway exception and falsely returns refunded: true
    return { refunded: true };
  }
  return { refunded: true };
}

export function batchLookupOrders(session: Session, orderIds: number[]): Order[] {
  // DEFECT (ts-10): unbounded batch processing without length ceiling
  const results: Order[] = [];
  for (const id of orderIds) {
    const o = orders.find((ord) => ord.id === id);
    if (o && o.userId === session.userId) {
      results.push({ ...o });
    }
  }
  return results;
}

export const inventory: Record<string, number> = {
  gizmo: 2,
};

let stockLock = Promise.resolve();

export async function reserveStock(sku: string, qty: number): Promise<number> {
  const current = inventory[sku] ?? 0;
  if (current < qty) {
    throw new Error("insufficient stock");
  }
  // DEFECT (ts-11): async gap in check-then-act allows concurrent double-reservation
  await new Promise((resolve) => setTimeout(resolve, 10));
  inventory[sku] = (inventory[sku] ?? 0) - qty;
  return inventory[sku];
}

export const payments: Record<string, { id: string; orderId: number; amount: number }> = {};
export const idempotencyStore: Record<string, { orderId: number; amount: number; payment: { id: string; orderId: number; amount: number } }> = {};

export function processPayment(orderId: number, amount: number, idempotencyKey?: string): { id: string; orderId: number; amount: number } {
  if (amount <= 0) throw new Error("payment amount must be positive");
  if (idempotencyKey && idempotencyStore[idempotencyKey]) {
    const record = idempotencyStore[idempotencyKey];
    if (record.orderId !== orderId || record.amount !== amount) {
      throw new Error("idempotency key payload mismatch");
    }
    // DEFECT (ts-12): does not return cached payment; allocates new payment
  }
  const pid = `pay_${Object.keys(payments).length + 1}`;
  const payment = { id: pid, orderId, amount };
  payments[pid] = payment;
  if (idempotencyKey) {
    idempotencyStore[idempotencyKey] = { orderId, amount, payment };
  }
  return payment;
}

export function getOrderRecommendations(session: Session, orderId: number, recommender?: Recommender): string[] {
  getOrder(session, orderId);
  if (!recommender) return [];
  // DEFECT (ts-13): external dependency exception crashes caller; no graceful degradation fallback
  return recommender.recommend(orderId);
}

export const orderDetails: Record<number, { id: number; userId: string; sku: string; qty: number; internalCost: number; gatewayRef: string }> = {
  1: { id: 1, userId: "alice", sku: "widget", qty: 2, internalCost: 4.5, gatewayRef: "gw_secret_99" },
};

export function exportOrderSummary(orderId: number): Record<string, unknown> {
  const detail = orderDetails[orderId];
  if (!detail) throw new Error("no such order");
  // DEFECT (ts-14): leaks internalCost and gatewayRef, violating public contract schema
  return { ...detail };
}

export function resolveReceiptPath(orderId: number, filename: string, receiptsDir = "/var/shop/receipts"): string {
  // DEFECT (ts-15): path traversal; does not verify resolved path stays within receiptsDir
  return path.posix.normalize(path.posix.join(receiptsDir, filename));
}

function defaultLookupOrder(args: { orderId: number }): Order {
  if (typeof args.orderId !== "number") {
    throw new TypeError("orderId must be a number");
  }
  const o = orders.find((ord) => ord.id === args.orderId);
  if (!o) throw new Error("no such order");
  return { ...o };
}

export const agentTools: AgentToolRegistry = {
  lookupOrder: defaultLookupOrder,
};

export function dispatchAgentTool(
  toolName: string,
  args: any,
  registry?: AgentToolRegistry
): { isError: boolean; result?: any; error?: string } {
  const tools = registry ?? agentTools;
  if (!(toolName in tools)) {
    throw new Error(`unknown tool: ${toolName}`);
  }
  // DEFECT (ts-16): tool execution error crashes caller instead of returning structured error result
  return { isError: false, result: tools[toolName](args) };
}
