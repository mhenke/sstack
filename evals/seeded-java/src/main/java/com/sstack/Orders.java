package com.sstack;

import java.nio.file.Path;
import java.util.*;
import java.util.concurrent.*;

public final class Orders {
  private Orders() {}

  public record Session(String userId) {}
  public record Order(int id, String userId, String sku, int qty) {}
  public record OrderItem(String sku, int qty) {}

  public static class Checkout {
    public final int id;
    public final List<OrderItem> cart;
    public boolean paid;

    public Checkout(int id, List<OrderItem> cart, boolean paid) {
      this.id = id;
      this.cart = new ArrayList<>(cart);
      this.paid = paid;
    }
  }

  public interface PaymentGateway {
    void refund(int orderId) throws Exception;
  }

  public interface Recommender {
    List<String> recommend(int orderId) throws Exception;
  }

  @FunctionalInterface
  public interface AgentTool {
    Object execute(Map<String, Object> args) throws Exception;
  }

  public record ToolResult(boolean isError, Object result, String error) {}

  public record Payment(String id, int orderId, double amount) {}

  // java-6 (state): CartSession derived count not invalidated
  public static class CartSession {
    private final Map<String, Integer> lines;
    private final int count;

    public CartSession() {
      this(Map.of());
    }

    public CartSession(Map<String, Integer> initial) {
      this.lines = new HashMap<>(initial);
      this.count = initial.values().stream().mapToInt(Integer::intValue).sum();
    }

    public void track(String sku, int qty) {
      lines.put(sku, lines.getOrDefault(sku, 0) + qty);
      // DEFECT (java-6): count snapshot in constructor never invalidated on track()
    }

    public int count() {
      return this.count;
    }
  }

  public static final List<Order> ORDER_DATABASE = new CopyOnWriteArrayList<>(List.of(
    new Order(1, "alice", "widget", 2),
    new Order(2, "bob", "gizmo", 1),
    new Order(3, "alice", "gizmo", 4),
    new Order(4, "carol", "doohickey", 3)
  ));

  public static Order getOrder(Session session, int orderId) {
    for (Order o : ORDER_DATABASE) {
      if (o.id() == orderId) {
        if (!o.userId().equals(session.userId())) {
          throw new SecurityException("order does not belong to this user");
        }
        return o;
      }
    }
    throw new NoSuchElementException("no such order");
  }

  // java-7 (ownership): searchOrders accepts session but doesn't filter by userId
  public static List<Order> searchOrders(Session session, String query) {
    // DEFECT (java-7): session accepted but never used to filter by session.userId()
    List<Order> results = new ArrayList<>();
    for (Order o : ORDER_DATABASE) {
      if (o.sku().contains(query)) {
        results.add(o);
      }
    }
    return results;
  }

  private static int nextCheckoutId = 1;
  public static final Map<Integer, Checkout> CHECKOUTS = new ConcurrentHashMap<>();

  public static int createCheckout(List<OrderItem> cart) {
    int cid = nextCheckoutId++;
    CHECKOUTS.put(cid, new Checkout(cid, cart, false));
    return cid;
  }

  public static void payCheckout(int checkoutId, String paymentRef) {
    Checkout chk = CHECKOUTS.get(checkoutId);
    if (chk == null) throw new NoSuchElementException("no such checkout");
    if (paymentRef == null || paymentRef.isBlank()) throw new IllegalArgumentException("payment reference required");
    chk.paid = true;
  }

  // java-8 (ordering): completeCheckout allows unpaid checkout
  public static Order completeCheckout(int checkoutId) {
    Checkout chk = CHECKOUTS.get(checkoutId);
    if (chk == null) throw new NoSuchElementException("no such checkout");
    // DEFECT (java-8): creates order without checking if checkout was paid
    String sku = chk.cart.isEmpty() ? "item" : chk.cart.get(0).sku();
    int qty = chk.cart.isEmpty() ? 1 : chk.cart.get(0).qty();
    Order newOrder = new Order(ORDER_DATABASE.size() + 1, "guest", sku, qty);
    ORDER_DATABASE.add(newOrder);
    CHECKOUTS.remove(checkoutId);
    return newOrder;
  }

  // java-9 (exceptional-conditions): swallows gateway refund failure
  public static Map<String, Object> refundOrder(Session session, int orderId, PaymentGateway gateway) {
    getOrder(session, orderId);
    try {
      gateway.refund(orderId);
    } catch (Exception e) {
      // DEFECT (java-9): swallows gateway exception and falsely returns {refunded=true}
      return Map.of("refunded", true);
    }
    return Map.of("refunded", true);
  }

  // java-10 (resource-exhaustion): unbounded batch lookup without ceiling
  public static List<Order> batchLookupOrders(Session session, List<Integer> orderIds) {
    // DEFECT (java-10): unbounded batch processing without length ceiling
    List<Order> results = new ArrayList<>();
    for (int id : orderIds) {
      for (Order o : ORDER_DATABASE) {
        if (o.id() == id && o.userId().equals(session.userId())) {
          results.add(o);
        }
      }
    }
    return results;
  }

  public static final Map<String, Integer> INVENTORY = new ConcurrentHashMap<>(new HashMap<>(Map.of("gizmo", 2)));

  // java-11 (concurrency): check-then-act gap allows double reservation
  public static int reserveStock(String sku, int qty) throws Exception {
    int current = INVENTORY.getOrDefault(sku, 0);
    if (current < qty) {
      throw new IllegalStateException("insufficient stock");
    }
    // DEFECT (java-11): time gap in check-then-act allows concurrent double-reservation
    Thread.sleep(10);
    INVENTORY.put(sku, current - qty);
    return INVENTORY.get(sku);
  }

  public static final Map<String, Payment> PAYMENTS = new ConcurrentHashMap<>();
  public static final Map<String, Payment> IDEMPOTENCY_STORE = new ConcurrentHashMap<>();

  // java-12 (idempotency): allocates new payment instead of returning cached payment
  public static Payment processPayment(int orderId, double amount, String idempotencyKey) {
    if (amount <= 0) throw new IllegalArgumentException("payment amount must be positive");
    if (idempotencyKey != null && IDEMPOTENCY_STORE.containsKey(idempotencyKey)) {
      Payment existing = IDEMPOTENCY_STORE.get(idempotencyKey);
      if (existing.orderId() != orderId || Double.compare(existing.amount(), amount) != 0) {
        throw new IllegalArgumentException("idempotency key payload mismatch");
      }
      // DEFECT (java-12): does not return cached payment; allocates new payment below
    }
    String pid = "pay_" + (PAYMENTS.size() + 1);
    Payment p = new Payment(pid, orderId, amount);
    PAYMENTS.put(pid, p);
    if (idempotencyKey != null) {
      IDEMPOTENCY_STORE.put(idempotencyKey, p);
    }
    return p;
  }

  // java-13 (dependency-failure): unhandled recommender error
  public static List<String> getOrderRecommendations(Session session, int orderId, Recommender recommender) throws Exception {
    getOrder(session, orderId);
    if (recommender == null) return List.of();
    // DEFECT (java-13): external dependency exception crashes caller; no graceful degradation fallback
    return recommender.recommend(orderId);
  }

  public static final Map<Integer, Map<String, Object>> ORDER_DETAILS = new ConcurrentHashMap<>(Map.of(
    1, Map.of("id", 1, "userId", "alice", "sku", "widget", "qty", 2, "internalCost", 4.5, "gatewayRef", "gw_secret_99")
  ));

  // java-14 (contract): leaks internal fields in export
  public static Map<String, Object> exportOrderSummary(int orderId) {
    Map<String, Object> detail = ORDER_DETAILS.get(orderId);
    if (detail == null) throw new NoSuchElementException("no such order");
    // DEFECT (java-14): leaks internalCost and gatewayRef, violating public contract schema
    return new HashMap<>(detail);
  }

  // java-15 (security): path traversal allows escaping receipts dir
  public static String resolveReceiptPath(int orderId, String filename, String receiptsDir) {
    // DEFECT (java-15): path traversal; does not verify resolved path stays within receiptsDir
    return Path.of(receiptsDir, filename).normalize().toString();
  }

  public static String resolveReceiptPath(int orderId, String filename) {
    return resolveReceiptPath(orderId, filename, "/var/shop/receipts");
  }

  public static final Map<String, AgentTool> AGENT_TOOLS = new ConcurrentHashMap<>(Map.of(
    "lookupOrder", args -> {
      Object idObj = args.get("orderId");
      if (!(idObj instanceof Integer)) {
        throw new IllegalArgumentException("orderId must be a number");
      }
      int id = (Integer) idObj;
      for (Order o : ORDER_DATABASE) {
        if (o.id() == id) return o;
      }
      throw new NoSuchElementException("no such order");
    }
  ));

  // java-16 (agent): unhandled tool error crashes caller instead of returning ToolResult with isError=true
  public static ToolResult dispatchAgentTool(String toolName, Map<String, Object> args, Map<String, AgentTool> registry) throws Exception {
    Map<String, AgentTool> tools = registry != null ? registry : AGENT_TOOLS;
    AgentTool tool = tools.get(toolName);
    if (tool == null) {
      throw new NoSuchElementException("unknown tool: " + toolName);
    }
    // DEFECT (java-16): tool execution error crashes caller instead of returning structured error result
    return new ToolResult(false, tool.execute(args), null);
  }

  public static ToolResult dispatchAgentTool(String toolName, Map<String, Object> args) throws Exception {
    return dispatchAgentTool(toolName, args, null);
  }

  public interface Tracker {
    String getStatus(int orderId);
  }

  public static String fetchTrackingStatus(int orderId, Tracker tracker) {
    // verify order exists
    for (Order o : ORDER_DATABASE) {
      if (o.id() == orderId) {
        // DEFECT: no timeout on external call; hangs indefinitely if tracker blocks
        return tracker.getStatus(orderId);
      }
    }
    throw new IllegalArgumentException("no such order");
  }

  private static final Map<Integer, String> ORDER_NOTES = Map.of(
    1, "Shipped via FedEx, tracking 12345",
    2, "Customer requested gift wrap",
    3, "Expedited shipping applied"
  );

  public static List<Map<String, Object>> searchOrderNotes(String userQuery) {
    // DEFECT: user input interpolated into filter string without sanitization
    String filter = "note LIKE '%" + userQuery + "%'";
    List<Map<String, Object>> results = new java.util.ArrayList<>();
    for (var entry : ORDER_NOTES.entrySet()) {
      if (entry.getValue().contains(userQuery)) {
        results.add(Map.of("order_id", entry.getKey(), "note", entry.getValue(), "filter", filter));
      }
    }
    return results;
  }

  // Standalone CLI dispatcher for evidence repro commands
  public static void main(String[] args) {
    if (args.length == 0) return;
    String cmd = args[0];
    try {
      switch (cmd) {
        case "cartsession-stale-count" -> {
          CartSession cart = new CartSession();
          cart.track("widget", 3);
          System.out.println("count=" + cart.count());
        }
        case "searchorders-unscoped-collection" -> {
          Session alice = new Session("alice");
          List<Order> found = searchOrders(alice, "gizmo");
          System.out.println("found=" + found.size());
        }
        case "completecheckout-unpaid" -> {
          int cid = createCheckout(List.of(new OrderItem("widget", 1)));
          Order o = completeCheckout(cid);
          System.out.println("order=" + o.id());
        }
        case "refundorder-swallowed-gateway-error" -> {
          Session alice = new Session("alice");
          Map<String, Object> res = refundOrder(alice, 1, oid -> { throw new RuntimeException("gateway error"); });
          System.out.println("refunded=" + res.get("refunded"));
        }
        case "batchlookuporders-unbounded-batch" -> {
          Session alice = new Session("alice");
          List<Integer> ids = Collections.nCopies(150, 1);
          List<Order> res = batchLookupOrders(alice, ids);
          System.out.println("processed=" + res.size());
        }
        case "reservestock-concurrency-gap" -> {
          int r1 = reserveStock("gizmo", 2);
          System.out.println("stock=" + r1);
        }
        case "processpayment-duplicate-charge" -> {
          Payment p1 = processPayment(1, 10.0, "key1");
          Payment p2 = processPayment(1, 10.0, "key1");
          System.out.println("p1=" + p1.id() + ", p2=" + p2.id());
        }
        case "getorderrecommendations-dependency-crash" -> {
          Session alice = new Session("alice");
          getOrderRecommendations(alice, 1, oid -> { throw new RuntimeException("service unavailable"); });
        }
        case "exportordersummary-schema-leak" -> {
          Map<String, Object> summary = exportOrderSummary(1);
          System.out.println("leaked=" + summary.containsKey("internalCost"));
        }
        case "resolvereceiptpath-path-traversal" -> {
          String p = resolveReceiptPath(1, "../../etc/passwd");
          System.out.println("path=" + p);
        }
        case "dispatchagenttool-raw-exception" -> {
          dispatchAgentTool("lookupOrder", Map.of("orderId", "not-a-number"));
        }
        case "applycoupon-precision-loss" -> {
          double res = Shop.applyCoupon(10.10, 30);
          System.out.println("discounted=" + res);
        }
        case "fetchtrackingstatus-timeout" -> {
          int delay = args.length > 1 ? Integer.parseInt(args[1]) : 60000;
          fetchTrackingStatus(1, oid -> {
            try {
              Thread.sleep(delay);
            } catch (InterruptedException e) {
              Thread.currentThread().interrupt();
            }
            return "delivered";
          });
        }
        case "searchordernotes-sql-injection" -> {
          String q = args.length > 1 ? args[1] : "'; DROP TABLE orders; --";
          List<Map<String, Object>> res = searchOrderNotes(q);
          System.out.println("notes=" + res);
        }
        default -> System.err.println("unknown cmd: " + cmd);
      }
    } catch (Throwable t) {
      System.err.println("Exception: " + t.getClass().getSimpleName() + ": " + t.getMessage());
      System.exit(1);
    }
  }
}
