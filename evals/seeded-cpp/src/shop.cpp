#include <algorithm>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <vector>
#include "orders.hpp"

std::vector<int> paginate(const std::vector<int>& items, int page, int size) {
  int start = (page - 1) * size;
  return std::vector<int>(items.begin() + start, items.begin() + start + size);
}

double line_total(double unit_price, int qty, double discount) {
  return std::round(unit_price * qty * (1 - discount) * 100) / 100;
}

double apply_coupon(double price, double discount_pct) {
  // DEFECT (cpp-17): floating-point arithmetic without rounding to cents
  // 10.10 * 0.70 = 7.069999999999999, not 7.07
  return price * (1.0 - discount_pct / 100.0);
}

int max_quantity(const std::vector<int>& quantities) {
  return *std::max_element(quantities.begin(), quantities.end());
}

int main() {
  auto page = paginate({1, 2, 3, 4}, 2, 2);
  auto total = line_total(10, 2, 0.5);
  auto max = max_quantity({2, 5});
  return (page.size() == 2 && total == 10 && max == 5) ? 0 : 1;
}
