package com.sstack;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;
import java.util.List;

class ShopTest {
  @Test void paginates() { assertEquals(List.of(3, 4), Shop.paginate(List.of(1, 2, 3, 4), 2, 2)); }
  @Test void totals() { assertEquals(10.0, Shop.lineTotal(10, 2, 0.5)); }
  @Test void maxes() { assertEquals(5, Shop.maxQuantity(List.of(2, 5))); }
}
