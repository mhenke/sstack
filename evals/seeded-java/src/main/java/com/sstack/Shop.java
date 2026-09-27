package com.sstack;

import java.util.List;

public final class Shop {
  public static List<Integer> paginate(List<Integer> items, int page, int size) {
    int start = (page - 1) * size;
    return items.subList(start, Math.min(items.size(), start + size));
  }

  public static double lineTotal(double unitPrice, int qty, Double discount) {
    return Math.round(unitPrice * qty * (1 - (discount == null ? 0 : discount)) * 100) / 100.0;
  }

  public static int maxQuantity(List<Integer> quantities) {
    int max = Integer.MIN_VALUE;
    for (int qty : quantities) max = Math.max(max, qty);
    return max;
  }
}
