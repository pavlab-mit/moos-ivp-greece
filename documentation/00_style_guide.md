---
status: stub
applies_to: All documents in moos-ivp-greece/documentation/
last_updated: 2026-06-02
owner: TBD
---

# Documentation Style Guide

Conventions for everything in this folder. The goal is a documentation set
that reads consistently across files and that cleanly separates **why** from
**what to do**, so an operator following a procedure isn't bouncing between
context and steps.

---

## 1. File Naming

- **`NN_topic_name.md`** — two-digit prefix, snake_case, lowercase, `.md`
  extension only.
- Numeric prefix encodes read order and category. `00_…` reference/meta
  files; `01_…`–`02_…` deployment-level docs (once per site); `10_…`–`17_…`
  per-boat build sequence; `20_…` per-boat verification; `30_…` operations;
  `99_…` optional appendices.
- One topic per file. If a file would have two unrelated procedures, it
  becomes two files.

## 2. Frontmatter

Every file opens with a YAML-style header in a `---`-fenced block:

```yaml
---
status: stub | draft | review | stable
applies_to: <which fleet / deployment / hardware>
last_updated: YYYY-MM-DD
owner: <name or TBD>
---
```

Then the H1 title.

## 3. Section Structure

Procedural docs use this skeleton. Sections may be omitted if not applicable;
do not reorder.

| § | Heading | Contents |
|---|---|---|
| 1 | Overview | One paragraph: what this doc covers, who it's for. |
| 2 | Prerequisites | Hardware, files, credentials, and prior steps required before §4. |
| 3 | Context | Prose explanation of how the thing works, what the parts are, and why the procedure is shaped the way it is. **No numbered steps in §3.** |
| 4+ | Procedure | Numbered, imperative steps. Multiple §4-style sections are fine for distinct procedures (e.g., §4 Bind, §5 Flash, §6 Verify). |
| N | Verification | Concrete, observable success criteria. "Run X, expect Y." |
| N+1 | Troubleshooting | Symptom → likely cause → fix table or list. |
| N+2 | Quick Reference | At-a-glance card for experienced operators. |

Reference docs (anything `00_…` or `01_…`) skip §2 and §4+ and use topical
sections instead. The QC sign-off (`20_…`) is a pure checklist and skips
§3.

## 4. Voice and Tense

- **Steps:** second-person imperative, present tense. "Edit
  `/etc/boat-network.conf`. Set `BOAT_ID=31`. Reboot."
- **Context:** third-person, descriptive. "The Pi runs `systemd-networkd` and
  manages three interfaces…"
- Avoid "we will" / "you should consider" in procedures. Either it's a step
  or it belongs in §3.

## 5. Callouts

Use blockquote callouts sparingly, with a bolded prefix:

```markdown
> **Critical.** Reversing +5 V and GND will damage the Mini-OEM board.

> **Tip.** Photograph each step during disassembly.

> **Note.** This setting is non-volatile and persists across reboots.
```

There is no `[Greece]` flag in these docs — these docs are Greece-only. If
you need to call out a lab-vs-Greece difference for a contributor's benefit,
use a `> **Lab note.**` callout and keep it short.

## 6. Code Blocks

- Always tag the language: ` ```bash `, ` ```yaml `, ` ```text `, etc.
- Shell prefix convention:
  - `$ ` → command run on a **laptop / shoreside workstation**.
  - No prefix → command run on the **target device** (the Pi, the radio, the
    backseat). Identify the target in a sentence above the block.
- Inline comments live **above** the line they describe, not at end-of-line.
- Long output: include only what's needed to verify the step. Omit boilerplate.

## 7. Secrets and Identifiers

- Never inline a real password or key.
- Reference credentials by handlebar key: `{{PI_DEFAULT_PASSWORD}}`,
  `{{RADIO_MESH_PASSWORD}}`, etc.
- Every new placeholder must be added to `00_secrets.template.md` with a
  description.
- Real values live in `00_secrets.md` (gitignored). Operators populate that
  file locally from a trusted source (1Password, USB key, written from a
  trusted operator, etc.).
- Network identifiers (BOAT_IDs, hostnames, mesh ID) live in
  `01_fleet_and_network_reference.md`, not duplicated in every doc.

## 8. Cross-References

- Within the same file: `§3.2`.
- Across files: `` [`13_frontseat_first_boot.md` §6](13_frontseat_first_boot.md#6-update-etcboat-networkconf) ``.
- Don't link to legacy un-numbered docs from new numbered docs; reach back
  through the new file that supersedes the old one.

## 9. Tables vs. Lists

- Use a **table** when each item has ≥3 attributes (e.g., pinouts, IP plans,
  channel maps).
- Use a **list** for single-attribute enumerations (bullet of parts, ordered
  procedure steps).
- Don't use a table to render a two-column "term → definition" set unless
  there are more than five entries.

## 10. Diagrams

ASCII-art diagrams are fine and preferred for portability. If a diagram needs
maintenance, prefer a Mermaid block (` ```mermaid `) over a hand-drawn box
diagram so future edits don't require pixel-pushing.

## 11. Status Discipline

Update the `status` field in the frontmatter when the file changes state:

- `stub` → file exists, content not yet written.
- `draft` → content present, expect changes; not yet reviewed.
- `review` → content present, ready for second eyes.
- `stable` → reviewed and considered current.

If you make a substantive edit to a `stable` file, drop it back to `review`.

## 12. Linting Checklist (for the author)

Before opening a PR for a doc edit:

- [ ] Frontmatter present and `last_updated` bumped.
- [ ] No real passwords or keys in the body.
- [ ] Procedure steps are imperative and numbered.
- [ ] Context is in §3, not interleaved with steps.
- [ ] Every code block has a language tag.
- [ ] Every cross-reference resolves (file exists, anchor exists).
- [ ] Status field reflects reality.
