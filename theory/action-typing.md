# Action-typing doctrine — mutation vs observe/verification at the work-block level

**Status:** INSTRUMENTED (v0.7.9, 2026-08-24) — doctrine + `examples/a4_action_typing.py`
**Thread:** CURIOSITY — κ-over-φ dense-φ thread, "remaining honest gap" closure.
**Class:** logging-doctrine upgrade, NOT a measurement. The `a3_dense_phi.py` harness is
read-only and already consumes this field when present.

---

## 1. Why

`a3_dense_phi.py` (v0.7.8) proved the diary's *tool histogram* is a dense φ signal:
`φ_exec_ratio` covers 100% of sessions (vs the sparse `!Dc:`/`⊗Er:` layer's 5-8%). But
its honest verdict is a **null, not a curve**: high-κ sessions keep *executing*
(`Q̄_low/Q̄_high ≈ 1.0`, ρ ≈ −0.1), so there is no measurable *collapse* in execution
density as κ grows.

The remaining gap the harness itself names (CURIOSITY, "Remaining honest gap"):

> the ratio proves density ≠ collapse, but it cannot separate *why* terminal stays
> high (verification vs. genuine mutation).

A session that runs `terminal` 90% of the time to `build && test && git status` looks
identical on `φ_exec_ratio` to one that runs `terminal` 90% to `patch` production
state. The tool name carries the *name*, not the *intent*. To move from "no collapse"
to a **curve** (mutation-rate vs κ), the diary needs per-step action-typing.

## 2. The marker

A work-block's step is either a **mutation** (changes system/state: a `patch`/`write_file`
with a diff, a state-changing `execute_code`, a side-effecting `terminal` command)
or an **observe/verification** (reads, greps, web fetches, build/test/git-status checks,
a `terminal` that only reads). Every step with a `>T:` line SHOULD also carry a typed
intent marker so the curve is computable without guessing from tool-kind.

Format follows the existing `⊗` residue family (`⊗Er:` error, `⊗RCA:` root-cause):

```
⊗S:mutation          /mnt/...   # patch/write/execute with a diff, state-changing cmd
⊗S:observe           /mnt/...   # read/grep/web/build-check/git-status — reads state
```

`⊗S:` is the **step-intent residue**. When a mutation is also observable in the file
system (patch applied, file written, deploy ran), the mismatch between the marker and
the actual state is itself a log. The marker is a *claim* the read-only harness can
cross-check against tool-kind (see §4 honesty guard).

### Canonical tool→intent mapping (when the source is untyped, and to *verify* a typed marker)

| Intent | Tools / command shape |
|---|---|
| **mutation** | `patch`, `write_file`, `execute_code` (diff-producing or state-changing), `terminal` with write ops (git commit/push, deploy, npm i -g, sed patching real file), `browser_post`, `delegate_task` with a build goal |
| **observe** | `read_file`, `search_files`, `session_search`, `skill_view`, `web_search`, `web_extract`, `memory`, `vision_analyze`, `process.pending`-style peek, `terminal` read-only (git status/log/diff --stat, ls, test, build-check, curl GET), `todo` |

`terminal` is **ambiguous by design** — it is the #1 tool (2101 turns in 08-24 window)
precisely because it carries both intents. The typing exists to resolve that ambiguity;
a markerless `>T:terminal` is treated as *unknown* and excluded from the curve (see §4),
never guessed when the source gives no evidence.

## 3. Where the marker bites (the curve, not just a null)

With per-step typing, the α → β instrument computes the cursor the dense-φ null could
not:

```
mut_rate(session) = #mutation_blocks / (#mutation_blocks + #observe_blocks)
```

bucketed at the median κ, with a falsifiable claim:

> κ-over-φ with ACTION-INTENT: as κ grows past the turnover point, sessions stop
> *mutating* and spend their executing turns *verifying* — mut_rate collapses while
> φ_exec_ratio (density) stays flat.

That is a *different, sharper* fall-off than density collapse: a session that keeps
executing but only to *confirm* is a session whose per-capability Q is still collapsing,
just not on the raw exec/read axis. The goodhart guard is: φ_exec_core (patch+write+
execute_code, terminal excluded) must NOT be the thing doing the falling — if high-κ
sessions mutate plenty and merely verify more passively, there is no intent collapse either.

## 4. Honesty guards

1. **Unknown > typed:** a markerless `>T:` line is *unknown*, not guessed. The harness
   reports **action-typing coverage** (`typed_blocks / all_blocks`): if coverage is
   below a floor (15%, parity with the sparse layer's abstain bar), it ABSTAINS from a
   curve claim — an abstain, not a fabricated curve, exactly like `a3_kappa_proliferation.py`.
2. **Cross-check typed vs tool-kind:** a `⊗S:mutation` on a read-only `terminal` is a
   mislabel; the harness reports `mislabel_rate` and refuses to fire detection if it is
   high (> 10% of typed blocks) — the typing itself must be trustworthy before the curve is.
3. **Read-only:** `a4_action_typing.py` never writes the diary or triggers actions; it only
   reports. Its `--selftest` manufactures a synthetic intent-collapse and a flat control
   to prove the fragment fires on signal and stays silent on noise.

## 5. Backfill strategy (why this is doctrine first, curve later)

The marker is **forward-only** in production: past diary lines were written without it.
Backfilling intent on old lines is classification, not recording — legitimate only as a
*probe* the harness labels `inferred`, separated from `typed` so the two never mix in a
curve. The honest path: (a) this doctrine standardizes what agents write going forward,
(b) `a4_action_typing.py` today reports coverage ≃ 0 + an *inferred* ∫read-only trend as a
floor/bias probe, (c) next cron loops adopting `⊗S:` push typed coverage past the 15% bar,
(d) only then does `a4` turn its abstain into a defensible curve, closing the thread
end-to-end on *recorded*, not *classified*, intent.

## 6. Files

- `theory/action-typing.md` — this doctrine.
- `examples/a4_action_typing.py` — the read-only instrument (stdlib, zero deps).
- `CHANGELOG.md` v0.7.9 — entry.

Zero deps. Stdlib only. Reversible: deleting the marker (or ignoring it) returns the
diary to the dense-φ null — the curve is additive, never destructive.