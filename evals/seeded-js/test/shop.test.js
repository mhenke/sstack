import test from "node:test";
import assert from "node:assert/strict";
import { paginate } from "../src/pagination.js";
import { lineTotal, parseOrder } from "../src/pricing.js";
import { maxQuantity } from "../src/cart.js";

test("happy paths", () => {
  assert.deepEqual(paginate([1, 2, 3, 4], 2, 2), [3, 4]);
  assert.equal(lineTotal({ unitPrice: 10, qty: 2, discount: 0.5 }), 10);
  assert.deepEqual(parseOrder('[{"unitPrice": 9.99, "qty": 3}]'), [{ unitPrice: 9.99, qty: 3 }]);
  assert.equal(maxQuantity([{ qty: 2 }, { qty: 5 }]), 5);
});
