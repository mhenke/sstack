import * as path from "node:path";

export class CartSession {
  #lines;
  #count;

  constructor(lines = {}) {
    this.#lines = { ...lines };
    this.#count = Object.values(this.#lines).reduce((a, b) => a + b, 0);
  }

  track(sku, qty) {
    this.#lines[sku] = (this.#lines[sku] || 0) + qty;
    // DEFECT (js-6): #count snapshot in constructor never invalidated on track()
  }

  count() {
    return this.#count;
  }
}

export const orders = [
  { id: 1, userId: "alice", sku: "widget", qty: 2 },
  { id: 2, userId: "bob", sku: "gizmo", qty: 1 },
  { id: 3, userId: "alice", sku: "gizmo", qty: 4 },
  { id: 4, userId: "carol", sku: "doohickey", qty: 3 },
];

export function getOrder(session, orderId) {
  const order = orders.find((o) => o.id === orderId);
  if (!order) {
    throw new Error("no such order");
  }
  if (order.userId !== session.userId) {
    throw new Error("order does not belong to this user");
  }
  return { ...order };
}

export function searchOrders(session, q) {
  // DEFECT (js-7): session accepted but never used to filter by session.userId
  return orders.filter((o) => o.sku.includes(q)).map((o) => ({ ...o }));
}

let nextCheckoutId = 1;
export const checkouts = {};

export function createCheckout(cart) {
  const cid = nextCheckoutId++;
  checkouts[cid] = { id: cid, cart: [...cart], paid: false };
  return cid;
}

export function payCheckout(checkoutId, paymentRef) {
  const chk = checkouts[checkoutId];
  if (!chk) throw new Error("no such checkout");
  if (!paymentRef) throw new Error("payment reference required");
  chk.paid = true;
}

export function completeCheckout(checkoutId) {
  const chk = checkouts[checkoutId];
  if (!chk) throw new Error("no such checkout");
  // DEFECT (js-8): creates order without checking if checkout was paid
  const newOrder = {
    id: orders.length + 1,
    userId: "guest",
    sku: chk.cart[0]?.sku ?? "item",
    qty: chk.cart[0]?.qty ?? 1,
  };
  orders.push(newOrder);
  delete checkouts[checkoutId];
  return newOrder;
}

export function refundOrder(session, orderId, gateway) {
  getOrder(session, orderId);
  try {
    gateway.refund(orderId);
  } catch (_e) {
    // DEFECT (js-9): swallows gateway exception and falsely returns refunded: true
    return { refunded: true };
  }
  return { refunded: true };
}

export function batchLookupOrders(session, orderIds) {
  // DEFECT (js-10): unbounded batch processing without length ceiling
  const results = [];
  for (const id of orderIds) {
    const o = orders.find((ord) => ord.id === id);
    if (o && o.userId === session.userId) {
      results.push({ ...o });
    }
  }
  return results;
}

export const inventory = {
  gizmo: 2,
};

let stockLock = Promise.resolve();

export async function reserveStock(sku, qty) {
  const current = inventory[sku] ?? 0;
  if (current < qty) {
    throw new Error("insufficient stock");
  }
  // DEFECT (js-11): async gap in check-then-act allows concurrent double-reservation
  await new Promise((resolve) => setTimeout(resolve, 10));
  inventory[sku] = (inventory[sku] ?? 0) - qty;
  return inventory[sku];
}

export const payments = {};
export const idempotencyStore = {};

export function processPayment(orderId, amount, idempotencyKey) {
  if (amount <= 0) throw new Error("payment amount must be positive");
  if (idempotencyKey && idempotencyStore[idempotencyKey]) {
    const record = idempotencyStore[idempotencyKey];
    if (record.orderId !== orderId || record.amount !== amount) {
      throw new Error("idempotency key payload mismatch");
    }
    // DEFECT (js-12): does not return cached payment; allocates new payment
  }
  const pid = `pay_${Object.keys(payments).length + 1}`;
  const payment = { id: pid, orderId, amount };
  payments[pid] = payment;
  if (idempotencyKey) {
    idempotencyStore[idempotencyKey] = { orderId, amount, payment };
  }
  return payment;
}

export function getOrderRecommendations(session, orderId, recommender) {
  getOrder(session, orderId);
  if (!recommender) return [];
  // DEFECT (js-13): external dependency exception crashes caller; no graceful degradation fallback
  return recommender.recommend(orderId);
}

export const orderDetails = {
  1: { id: 1, userId: "alice", sku: "widget", qty: 2, internalCost: 4.5, gatewayRef: "gw_secret_99" },
};

export function exportOrderSummary(orderId) {
  const detail = orderDetails[orderId];
  if (!detail) throw new Error("no such order");
  // DEFECT (js-14): leaks internalCost and gatewayRef, violating public contract schema
  return { ...detail };
}

export function resolveReceiptPath(orderId, filename, receiptsDir = "/var/shop/receipts") {
  // DEFECT (js-15): path traversal; does not verify resolved path stays within receiptsDir
  return path.posix.normalize(path.posix.join(receiptsDir, filename));
}

function defaultLookupOrder(args) {
  if (typeof args.orderId !== "number") {
    throw new TypeError("orderId must be a number");
  }
  const o = orders.find((ord) => ord.id === args.orderId);
  if (!o) throw new Error("no such order");
  return { ...o };
}

export const agentTools = {
  lookupOrder: defaultLookupOrder,
};

export function dispatchAgentTool(toolName, args, registry) {
  const tools = registry ?? agentTools;
  if (!(toolName in tools)) {
    throw new Error(`unknown tool: ${toolName}`);
  }
  // DEFECT (js-16): tool execution error crashes caller instead of returning structured error result
  return { isError: false, result: tools[toolName](args) };
}
