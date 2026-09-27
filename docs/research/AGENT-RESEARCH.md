# Agent lens: what an `agent` lens would own

Every claim below was read from the primary source named beside it. Where a
source does not say something, this file says so rather than filling the gap.
Research date: 2026-09-27. Linked from [`RESEARCH.md`](RESEARCH.md).

The `agent` row in the lens index reads "AI agent tool-call errors, truncated
context, prompt injection" and is unbuilt. This note exists to decide whether
shipping it would duplicate `boundaries` (context limits) or `malformed` (JSON
tool payloads), and to establish the primary specifications governing LLM agent
systems.

## The overlap, settled

While traditional software parses deterministic inputs, AI agent systems
(orchestrators, MCP servers, tool-calling loops) introduce non-deterministic
generative failure modes:

| Case | Shipped owner | Notes |
|---|---|---|
| Malformed JSON in REST API payload | `malformed` | Standard HTTP payload |
| String length exceeding maximum limit | `boundaries` | Scalar length bound |
| Host system command injection via unsanitized arg | `ownership` / `security` | Host shell execution |
| Agent tool-call argument schema divergence | `agent` | LLM hallucinated tool args |
| Unhandled tool execution error crashing agent loop | `agent` | Broken feedback loop |
| Silent system prompt eviction via context overflow | `agent` | Token budget priority inversion |
| Indirect prompt injection via untrusted tool output | `agent` | Data-as-code control hijack |
| Runaway recursive tool calling loop | `agent` | Cycle detection failure |

Standard lenses test human or programmatic clients hitting deterministic endpoints.
The `agent` lens attacks the boundaries between LLMs, host orchestrators, and
executable tools.

## What standards and specifications prove

### OWASP Top 10 for LLM Applications (2025)

The OWASP Foundation maintains the primary taxonomy of generative AI security
and reliability failures:

1. **LLM01: Prompt Injection:**
   Direct injections (jailbreaks) and indirect injections (malicious instructions
   embedded in web pages, database records, or tool outputs that hijack the agent's
   reasoning).
2. **LLM05: Improper Output Handling:**
   Failure to validate LLM outputs (including tool call arguments) before passing
   them to downstream interpreters, shell commands, or SQL engines.
3. **LLM06: Excessive Agency:**
   Granting agents autonomous tool access without human-in-the-loop approvals,
   least-privilege scoping, or rollback mechanisms.
4. **LLM10: Unbounded Consumption:**
   Flooding context windows or inducing recursive loops that exhaust token
   budgets or compute allocations.

### Model Context Protocol (MCP) Specification

Anthropic's Model Context Protocol (modelcontextprotocol.io) defines the open
standard for agent-to-tool communication:
- Tools define strict JSON Schemas (`inputSchema`).
- When a tool returns an error (`isError: true`), the protocol mandates that the
  error content be structured so the model can read it and self-correct.
- Common defect: Orchestrators throwing unhandled host exceptions when a tool
  returns `isError: true` or when tool arguments fail schema validation, crashing
  the entire agent session instead of feeding the error back to the model.

### Context Window Eviction and Truncation Invariants

When conversation transcripts exceed context window token limits:
- A naive FIFO truncation strategy truncates the top of the transcript.
- If the system instructions (defining safety constraints, tool guidelines, and
  personas) live at the top of the context, naive truncation silently evicts the
  system prompt, stripping the agent of its guardrails while leaving it active.
- Resilient orchestrators pin system prompts and compress or sliding-window only
  ephemeral dialogue.

## The observable oracle, checked at the source

Under negative agent attacks:

1. **Tool Error Survivability:** When a tool fails (returns non-zero exit code or
   `isError: true`), the agent loop catches the error, formats it into a valid
   tool result message, and prompts the model for recovery. The agent runtime
   never crashes with an unhandled exception.
2. **Schema Validation Gate:** When a model hallucinates an invalid argument
   (e.g., passing string instead of integer, or omitting mandatory parameters),
   the orchestrator intercepts the call before execution, returning a schema
   validation error back to the LLM.
3. **Prompt Boundary Isolation:** Untrusted data ingested from tool outputs or
   user documents is treated strictly as data (via XML tagging, delimiters, or
   structured envelopes) and does not execute embedded instructions.
4. **Finite Loop Ceiling:** If an agent encounters repeated tool errors, it
   aborts after $K$ attempts with a clear user diagnostic rather than looping
   infinitely and exhausting token budgets.

## What the lens should own

1. **Tool Schema Divergence Attacks:** Supplying synthetic tool calls with
   hallucinated properties, nulls for required keys, or wrong types.
2. **Tool Failure Injection:** Forcing tools to return exit code 1, timeouts, or
   malformed outputs to verify agent recovery loops.
3. **Context Overflow Invariants:** Verifying that system instructions and safety
   rules remain active when context length approaches maximum capacity.
4. **Indirect Prompt Injection Probing:** Injecting prompt escape sequences into
   mock tool data to test agent compliance.

## Recommendation: Proceed with standalone lens

**Verdict: Recommended.**
As codebases increasingly incorporate LLM agents, RAG pipelines, and MCP tools,
the agent loop is a primary failure surface. The failure modes (infinite loops,
crashed orchestrators on tool errors, evicted system prompts) are completely
invisible to HTTP and classical unit testing lenses.

## Open questions

- Determinism in testing: Testing LLM reasoning directly can be non-deterministic.
  However, testing the *orchestrator and tool-runner* (schema validator, error
  catcher, truncation logic, loop limiter) is 100% deterministic and can be
  exercised with mock model outputs.
