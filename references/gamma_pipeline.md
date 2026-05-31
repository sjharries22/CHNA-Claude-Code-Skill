# From a previous report to a branded Gamma deck

This is the workflow the skill follows when a client wants a **new** CHNA that
matches a **previous** report's brand visuals, structure, and tone — delivered
as a Gamma deck.

## The three artifacts (parse once, reuse)

| Artifact | Built by | Captures |
| --- | --- | --- |
| `brand_profile.json` | `scripts/extract_brand.py` | palette, fonts, logo/media, header/footer, heading styles |
| `structure.json` | `scripts/extract_structure.py` | heading outline + classified CHNA section types |
| tone guide | Claude, from `extract_docx.py` output | voice, reading level, terminology, do/don't |

## Step 1 — Parse the previous report

```bash
python3 scripts/extract_brand.py     "PREV.docx" -o brand_profile.json --media-dir out/media
python3 scripts/extract_structure.py "PREV.docx" -o structure.json
python3 scripts/extract_docx.py      "PREV.docx" -o out/prev.md
```

Then read `out/prev.md` and write a short **tone guide** (3–6 bullets): typical
sentence length, first vs. third person, how needs/data are framed, recurring
terminology, and anything to avoid.

## Step 2 — Pick the brand theme

Brand visuals in Gamma are **themes**. Reuse an existing custom theme rather
than recreating styling:

- List themes with the Gamma `get_themes` tool. This account already has
  custom themes (e.g. **"Metopio Theme"**, `r8c4e2hgwcz2ikc`, and themes
  imported from a client PPTX).
- Cross-check the theme against `brand_profile.json` (do the palette/fonts
  match?). If there's drift, the fix is a one-time edit **in the Gamma
  editor** — the API can apply a theme but cannot create or edit one.

## Step 3 — Assemble branded content

Use `structure.json` as the card outline and the blueprints in
`components/card_blueprints.md` to draft each card, written in the tone guide's
voice. Gamma treats `\n---\n` as a **card break**, and the first `#` heading on
a card is its title. Fill data only from the source/inputs — never invent
figures.

## Step 4 — Generate the deck

Call the Gamma `generate` tool with:

- `inputText`: the assembled Markdown (one card per section, `---` separated)
- `themeName`: the chosen brand theme id/name
- `textMode`: `preserve` when you've already written final copy (so Gamma
  doesn't rewrite it); use `generate`/`condense` only if you want Gamma to
  expand an outline
- `format`: `presentation` (deck) or `document` (long-form page)

**Always dry-run first**: generate a 2–3 card deck, share the URL for sign-off,
then produce the full report.

## Step 5 — Make it reusable

Once a deck looks right, save it **as a template in the Gamma editor**. Future
reports can then start from it via `generate_from_template`, locking in both
the brand and the CHNA card structure. (No templates exist on the account yet,
so the first run uses `generate`.)

## Guardrails

- Don't fabricate indicators, quotes, or figures — pull them from inputs.
- Treat resident stories/quotes as sensitive; paraphrase rather than reprint.
- The brand theme is the source of visual truth; `brand_profile.json`
  documents the brand and flags drift, it does not re-implement styling.
