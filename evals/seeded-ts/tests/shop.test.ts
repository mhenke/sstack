import { describe, expect, it } from "vitest";
import { paginate } from "../src/pagination";
import { lineTotal, parseOrder } from "../src/pricing";
import { maxQuantity, totalQuantity } from "../src/cart";

describe("paginate", () => {
  it("returns the requested page", () => {
    expect(paginate([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 2, 3)).toEqual([4, 5, 6]);
  });
  it("returns a partial last page", () => {
    expect(paginate([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 4, 3)).toEqual([10]);
  });
});

describe("pricing", () => {
  it("applies the discount", () => {
    expect(lineTotal({ unitPrice: 10, qty: 2, discount: 0.5 })).toBe(10);
  });
  it("parses a valid order", () => {
    expect(parseOrder('[{"unitPrice": 9.99, "qty": 3}]')).toEqual([
      { unitPrice: 9.99, qty: 3 },
    ]);
  });
});

describe("cart", () => {
  it("sums quantities", () => {
    expect(
      totalQuantity([
        { id: "a", qty: 2 },
        { id: "b", qty: 5 },
      ]),
    ).toBe(7);
  });
  it("finds the max quantity", () => {
    expect(
      maxQuantity([
        { id: "a", qty: 2 },
        { id: "b", qty: 5 },
      ]),
    ).toBe(5);
  });
});
