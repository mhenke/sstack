#pragma once

#include <algorithm>
#include <chrono>
#include <filesystem>
#include <functional>
#include <iostream>
#include <map>
#include <mutex>
#include <numeric>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

namespace shop {

class CartSession {
private:
  std::map<std::string, int> lines_;
  int count_;

public:
  CartSession() : count_(0) {}
  explicit CartSession(const std::map<std::string, int>& initial) : lines_(initial) {
    count_ = 0;
    for (const auto& [sku, qty] : lines_) {
      count_ += qty;
    }
  }

  void track(const std::string& sku, int qty) {
    lines_[sku] += qty;
    // DEFECT (cpp-6): count_ snapshot never invalidated on track()
  }

  int count() const {
    return count_;
  }
};

struct Session {
  std::string user_id;
};

struct Order {
  int id;
  std::string user_id;
  std::string sku;
  int qty;
};

inline std::vector<Order> ORDERS = {
  {1, "alice", "widget", 2},
  {2, "bob", "gizmo", 1},
  {3, "alice", "gizmo", 4},
  {4, "carol", "doohickey", 3}
};

inline std::vector<Order> search_orders(const Session& session, const std::string& query) {
  // DEFECT (cpp-7): session accepted but never used to filter by session.user_id
  std::vector<Order> result;
  for (const auto& o : ORDERS) {
    if (o.sku.find(query) != std::string::npos) {
      result.push_back(o);
    }
  }
  return result;
}

struct Checkout {
  int id;
  std::string sku;
  int qty;
  bool paid{false};
};

inline int next_checkout_id = 1;
inline std::map<int, Checkout> CHECKOUTS;

inline int create_checkout(const std::string& sku, int qty) {
  int id = next_checkout_id++;
  CHECKOUTS[id] = {id, sku, qty, false};
  return id;
}

inline void pay_checkout(int checkout_id, const std::string& payment_ref) {
  auto it = CHECKOUTS.find(checkout_id);
  if (it == CHECKOUTS.end()) throw std::invalid_argument("no such checkout");
  if (payment_ref.empty()) throw std::invalid_argument("payment reference required");
  it->second.paid = true;
}

inline Order complete_checkout(int checkout_id) {
  auto it = CHECKOUTS.find(checkout_id);
  if (it == CHECKOUTS.end()) throw std::invalid_argument("no such checkout");
  // DEFECT (cpp-8): creates order without checking if checkout was paid
  Order ord{static_cast<int>(ORDERS.size() + 1), "guest", it->second.sku, it->second.qty};
  ORDERS.push_back(ord);
  CHECKOUTS.erase(it);
  return ord;
}

struct PaymentGateway {
  virtual ~PaymentGateway() = default;
  virtual void refund(int order_id) = 0;
};

inline bool refund_order(const Session& session, int order_id, PaymentGateway* gateway) {
  try {
    if (gateway) gateway->refund(order_id);
  } catch (...) {
    // DEFECT (cpp-9): swallows gateway exception and falsely returns true
    return true;
  }
  return true;
}

inline std::vector<Order> batch_lookup_orders(const Session& session, const std::vector<int>& order_ids) {
  // DEFECT (cpp-10): unbounded batch processing without length ceiling
  std::vector<Order> result;
  for (int id : order_ids) {
    for (const auto& o : ORDERS) {
      if (o.id == id && o.user_id == session.user_id) {
        result.push_back(o);
      }
    }
  }
  return result;
}

inline std::map<std::string, int> INVENTORY = {{"gizmo", 2}};
inline std::mutex stock_mutex;

inline int reserve_stock(const std::string& sku, int qty) {
  int current = INVENTORY[sku];
  if (current < qty) {
    throw std::runtime_error("insufficient stock");
  }
  // DEFECT (cpp-11): non-atomic check-then-act allows concurrent double-reservation
  std::this_thread::sleep_for(std::chrono::milliseconds(10));
  INVENTORY[sku] = current - qty;
  return INVENTORY[sku];
}

struct Payment {
  std::string id;
  int order_id;
  double amount;
};

inline std::map<std::string, Payment> PAYMENTS;
inline std::map<std::string, Payment> IDEMPOTENCY_STORE;

inline Payment process_payment(int order_id, double amount, const std::string& idempotency_key = "") {
  if (amount <= 0.0) throw std::invalid_argument("payment amount must be positive");
  if (!idempotency_key.empty() && IDEMPOTENCY_STORE.find(idempotency_key) != IDEMPOTENCY_STORE.end()) {
    const auto& existing = IDEMPOTENCY_STORE[idempotency_key];
    if (existing.order_id != order_id || existing.amount != amount) {
      throw std::invalid_argument("idempotency key payload mismatch");
    }
    // DEFECT (cpp-12): does not return cached payment; allocates new payment
  }
  std::string pid = "pay_" + std::to_string(PAYMENTS.size() + 1);
  Payment p{pid, order_id, amount};
  PAYMENTS[pid] = p;
  if (!idempotency_key.empty()) {
    IDEMPOTENCY_STORE[idempotency_key] = p;
  }
  return p;
}

struct Recommender {
  virtual ~Recommender() = default;
  virtual std::vector<std::string> recommend(int order_id) = 0;
};

inline std::vector<std::string> get_order_recommendations(const Session& session, int order_id, Recommender* recommender) {
  if (!recommender) return {};
  // DEFECT (cpp-13): external dependency exception crashes caller; no graceful degradation fallback
  return recommender->recommend(order_id);
}

inline std::map<int, std::map<std::string, std::string>> ORDER_DETAILS = {
  {1, {{"id", "1"}, {"user_id", "alice"}, {"sku", "widget"}, {"qty", "2"}, {"internal_cost", "4.5"}, {"gateway_ref", "gw_secret_99"}}}
};

inline std::map<std::string, std::string> export_order_summary(int order_id) {
  auto it = ORDER_DETAILS.find(order_id);
  if (it == ORDER_DETAILS.end()) throw std::invalid_argument("no such order");
  // DEFECT (cpp-14): leaks internal_cost and gateway_ref, violating public contract schema
  return it->second;
}

inline std::string resolve_receipt_path(int order_id, const std::string& filename, const std::string& receipts_dir = "/var/shop/receipts") {
  // DEFECT (cpp-15): path traversal; does not verify resolved path stays within receipts_dir
  namespace fs = std::filesystem;
  return (fs::path(receipts_dir) / fs::path(filename)).lexically_normal().string();
}

inline std::map<std::string, std::string> dispatch_agent_tool(const std::string& tool_name, const std::map<std::string, std::string>& args) {
  if (tool_name != "lookup_order") {
    throw std::invalid_argument("unknown tool: " + tool_name);
  }
  auto it = args.find("order_id");
  if (it == args.end()) throw std::invalid_argument("missing order_id");
  // DEFECT (cpp-16): tool execution error crashes caller instead of returning structured error result
  int id = std::stoi(it->second);
  return {{"is_error", "false"}, {"id", std::to_string(id)}};
}

} // namespace shop
