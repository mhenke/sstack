# Negative Testing: Boundaries Lens

Research on negative testing for boundary values, edge conditions, numerical extremes, coordinate offsets, precision limits, and operating thresholds.

## Overview & Definition

Negative boundary testing (derived from Boundary Value Analysis / BVA) targets software behavior immediately outside valid operating thresholds ($Min - 1$, $Max + 1$) and at structural extremes (empty collections, singletons, capacity limits, stack-depth limits, and coordinate off-by-one errors).

In negative testing, boundary inputs are not expected to succeed; they must fail safely, reliably, and with explicit diagnostic errors rather than unhandled crashes, memory corruption, IEEE 754 precision drift, or silent truncation/clamping.

## Core Concepts & Failure Modes

1. **Numeric Range Violations ($Min - 1$, $Max + 1$, CWE-190):**
   - Inputs strictly below the allowed minimum (e.g., negative quantities, zero when 1-based, balances below floor).
   - Inputs strictly exceeding the maximum (e.g., age > 120, transfer > limit, integer overflow past `Number.MAX_SAFE_INTEGER` or `sys.maxsize`).
2. **Collection & Buffer Extremes (CWE-125, CWE-787):**
   - Empty collections (`len == 0`) passed to functions expecting non-empty inputs (e.g., min, max, average, reduce/fold without an initial accumulator).
   - Collections with single elements where pairwise algorithms assume $N \ge 2$.
   - Very large collections hitting runtime spread-argument stack limits (e.g., `Math.max(...arr)` throwing `RangeError: Maximum call stack size exceeded`).
3. **Index & Coordinate Off-by-One Traps:**
   - Accessing index equal to collection length (`arr[len]`).
   - Slicing with negative indices where language semantics cause silent empty results or wrap-around clamping rather than validation (e.g., Python `items[-3:0]` or JS `slice(-3, 0)` returning `[]`).
4. **Precision, Scale & Floating-Point Drift (CWE-682):**
   - Currency or scientific quantities requiring exact decimal representation passed to IEEE 754 binary floats (e.g., `0.1 + 0.2 !== 0.3`, banker's rounding `round(2.675, 2) === 2.67`).
   - Rounding or truncation occurring silently on numbers that fit declared thresholds.
5. **Temporal & Interval Boundaries:**
   - Zero or negative durations (`duration <= 0`).
   - Inverted time intervals (`end_time < start_time`).
   - Leap years, month boundaries (0-indexed vs 1-indexed month off-by-one), and daylight saving transition gaps.
6. **Operating Limits & Capacity Thresholds:**
   - Exceeding maximum concurrent connections, rate limit ceilings, payload byte limits, or pool quotas by exactly 1 ($Limit + 1$).

## Real-World Examples & Test Scenarios

### Scenario 1: Financial Transfer Amount Boundaries
- **Contract:** Minimum transfer £0.01, Maximum transfer £10,000.00.
- **Negative Inputs:**
  - `amount = 0.00` ($Min - 1$ boundary).
  - `amount = -0.01` (strictly negative).
  - `amount = 10000.01` ($Max + 1$ boundary).
- **Expected Oracle:** Explicit rejection (`ValidationError: Amount must be between £0.01 and £10,000.00`), no account balance modification, no ledger entry.

### Scenario 2: Identifier / Password Length Constraints
- **Contract:** String length between 8 and 64 characters.
- **Negative Inputs:**
  - `length = 7` (under minimum threshold).
  - `length = 65` (over maximum threshold).
  - `length = 0` (empty string).
- **Expected Oracle:** Immediate validation rejection before hashing, encryption, or persistence layers.

### Scenario 3: Time Interval Inversion & Negative Duration
- **Contract:** Event booking requires `start_time` and `end_time` where `end_time > start_time`, with `duration >= 60` seconds.
- **Negative Inputs:**
  - `start_time = 1700000000`, `end_time = 1700000000` (zero duration).
  - `start_time = 1700000000`, `end_time = 1699999900` (inverted interval).
- **Expected Oracle:** `ValueError: end_time must be strictly after start_time`; no reservation booked.

### Scenario 4: Collection Spread Stack Overflow
- **Contract:** Utility function computes the minimum value across an array of numbers.
- **Negative Input:** Array containing 250,000 items evaluated via `Math.min(...items)`.
- **Expected Oracle:** Implementation handles arbitrarily large arrays via iterative loop or chunking; does not crash with unhandled `RangeError: Maximum call stack size exceeded`.

### Scenario 5: Financial Precision & Scale Preservation
- **Contract:** Tax computation calculates exact tax on currency line items in cents.
- **Negative Input:** `amount = 2.675` with 2 decimal place contract.
- **Expected Oracle:** System uses decimal arithmetic or exact integer cents; does not silently round down to `2.67` due to IEEE 754 binary floating-point representation.

## Key Oracle Patterns

- **Explicit Validation Error:** The function raises a structured domain error or returns HTTP 400 Bad Request naming the out-of-bounds parameter.
- **Invariant Preservation:** Internal state (balances, counters, queues) remains completely unchanged when an out-of-bounds operation is attempted.
- **No Silent Fallback or Clamping:** Out-of-bounds coordinates, indices, or offsets must not silently return empty collections if the contract specifies valid ranges.
- **No Float Precision Loss:** Monetary and precision-critical fields maintain exact scale without IEEE 754 binary drift or unintended banker's rounding.
- **Predictable Boundary Rejection:** Exceeding operating caps by +1 yields deterministic rejection, never a process hang or memory exhaustion.

## Primary Sources & References

- ISO/IEC/IEEE 29119-4:2021 (Software Testing - Test Techniques: Boundary Value Analysis)
- Myers, Glenford J. *The Art of Software Testing* (Boundary condition testing, equivalence partitioning)
- IEEE 754-2019: IEEE Standard for Floating-Point Arithmetic
- CWE-125: Out-of-bounds Read
- CWE-787: Out-of-bounds Write
- CWE-190: Integer Overflow or Wraparound
- CWE-682: Incorrect Calculation
- OWASP Input Validation Cheat Sheet
