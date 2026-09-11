---
name: PageAnchor
description: A dark zinc workbench; ask on the left, prove it on the page, inspect Trace on the right.
colors:
  zinc-bg: "#0b0b0c"
  zinc-panel: "#111113"
  zinc-field: "#161618"
  zinc-border: "#242428"
  zinc-text: "#ececef"
  zinc-muted: "#8a8a93"
  canvas: "#09090b"
  ask: "#f4f4f5"
  ask-ink: "#0b0b0c"
  ask-well: "#171b24"
  ask-well-border: "#3d4f73"
  ask-placeholder: "#9aa3b8"
  proof: "#5b8def"
  proof-wash: "rgb(91 141 239 / 18%)"
  answer-well: "rgb(91 141 239 / 16%)"
  answer-border: "#4a66a3"
  fault: "#f2a0a0"
  fault-well: "#2a1616"
  abstain: "#e8c36a"
  abstain-well: "#2a2414"
typography:
  display:
    fontFamily: "Geist, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 560
    lineHeight: 1.45
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Geist, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 560
    lineHeight: 1.45
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Geist, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.9rem"
    fontWeight: 560
    lineHeight: 1.45
    letterSpacing: "normal"
  body:
    fontFamily: "Geist, ui-sans-serif, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  label:
    fontFamily: "Geist, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.8rem"
    fontWeight: 560
    lineHeight: 1.45
    letterSpacing: "0.04em"
  mono:
    fontFamily: "Geist Mono, ui-monospace, monospace"
    fontSize: "0.8rem"
    fontWeight: 450
    lineHeight: 1.45
    letterSpacing: "normal"
rounded:
  sm: "4px"
  md: "6px"
  pill: "999px"
spacing:
  xs: "0.3rem"
  sm: "0.45rem"
  md: "0.7rem"
  lg: "0.85rem"
components:
  button-primary:
    backgroundColor: "{colors.ask}"
    textColor: "{colors.ask-ink}"
    typography: "{typography.title}"
    rounded: "{rounded.md}"
    height: "2.25rem"
  button-primary-hover:
    backgroundColor: "{colors.ask}"
    textColor: "{colors.ask-ink}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.zinc-text}"
    rounded: "{rounded.sm}"
    padding: "0 0.6rem"
    height: "1.85rem"
  button-ghost-hover:
    backgroundColor: "{colors.zinc-field}"
    textColor: "{colors.zinc-text}"
  button-mode:
    backgroundColor: "transparent"
    textColor: "{colors.zinc-muted}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    height: "1.85rem"
  button-mode-hover:
    backgroundColor: "rgb(255 255 255 / 5%)"
    textColor: "{colors.zinc-text}"
  button-mode-pressed:
    backgroundColor: "{colors.ask}"
    textColor: "{colors.ask-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    height: "1.85rem"
  button-mode-pressed-hover:
    backgroundColor: "#fff"
    textColor: "{colors.ask-ink}"
  input-query:
    backgroundColor: "{colors.ask-well}"
    textColor: "{colors.zinc-text}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "0.7rem 0.75rem"
  switch-off:
    backgroundColor: "#2a2a2e"
    rounded: "{rounded.pill}"
    height: "1.05rem"
    width: "1.85rem"
  switch-on:
    backgroundColor: "{colors.proof}"
    rounded: "{rounded.pill}"
    height: "1.05rem"
    width: "1.85rem"
  page-readout:
    backgroundColor: "{colors.zinc-field}"
    textColor: "{colors.zinc-muted}"
    typography: "{typography.mono}"
    rounded: "{rounded.sm}"
    padding: "0.28rem 0.5rem"
  citation-row:
    backgroundColor: "transparent"
    textColor: "{colors.zinc-text}"
    rounded: "{rounded.sm}"
    padding: "0.45rem 0.5rem"
  citation-row-current:
    backgroundColor: "rgb(91 141 239 / 8%)"
    textColor: "{colors.zinc-text}"
    rounded: "{rounded.sm}"
    padding: "0.45rem 0.5rem"
  banner-fault:
    backgroundColor: "{colors.fault-well}"
    textColor: "{colors.fault}"
    rounded: "{rounded.sm}"
    padding: "0.55rem 0.65rem"
  banner-abstain:
    backgroundColor: "{colors.abstain-well}"
    textColor: "{colors.abstain}"
    rounded: "{rounded.sm}"
    padding: "0.55rem 0.65rem"
  card-trace:
    backgroundColor: "{colors.zinc-panel}"
    textColor: "{colors.zinc-text}"
    rounded: "{rounded.md}"
    padding: "0.65rem 0.7rem 0.2rem"
  answer-block:
    backgroundColor: "{colors.answer-well}"
    textColor: "{colors.zinc-text}"
    rounded: "{rounded.md}"
    padding: "0.75rem 0.8rem"
---

# Design System: PageAnchor

## Overview

**Creative North Star: "The Zinc Workbench"**

PageAnchor is a dark operator workbench. Ask sits on the left, the cited page dominates the center, and Trace is the index on the right. Belief lives in a boxed region on the page, or in a refusal. Fluency in a card is not the product.

The chassis is near-black zinc: flat panels, 1px hairlines, 6px corners. Type is Geist for the operator and Geist Mono for measurements. The primary action is white Ask. Blue is scarce: it marks the selected region, a verified citation, a checked switch, the focus ring, the query well, and the answer well. There is no enamel, no sprocket rail, no putty plate, and no cadmium chrome.

This world rejects the microfilm reader and equal chat / PDF / sources cards. It also rejects round consumer chrome, traffic-light status pills, and a blue Ask button. Refusal is a first-class banner plus an empty canvas, not a polite invented answer.

**Key Characteristics:**
- Near-black zinc panels, 1px hairlines, 6px surfaces and 4px compact chrome
- 48px top bar; Ask ~22% / document canvas / Trace ~22%
- Geist for operator type; Geist Mono only for measures and ids
- White Ask and pressed mode chips; proof blue for selection, verified, the query well, and the answer well
- Page PNG on a darker canvas well; bbox is the citation
- Abstain omits the answer block and keeps citations for the trail

## Colors

Cool near-black zinc with one white action and one scarce proof blue.

### Primary
- **Ask White** (`ask` / `ask-ink`): The Ask control and the pressed segment in the mode group. Hover brightens the fill slightly. This is the only large light rectangle in the chrome.

### Secondary
- **Proof Blue** (`proof` / `proof-wash`): Selection and verified, plus the query and answer wells. Drawn as a 2px inset box plus an 18% wash on the cited region; as the selected citation hairline; as Verified status; as a checked switch track; as the 12px mark icon; as the 2px focus ring; as the query-well tint and the answer-well wash. Not a button fill, not a heading color, not a pane background.

### Neutral
- **Near-black Zinc** (`zinc-bg`): App chassis, top bar, and pane grounds.
- **Zinc Panel** (`zinc-panel`): Trace cards, one step up from the chassis.
- **Zinc Field** (`zinc-field`): Inset controls: mode track, page readout, JSON well, ghost hover, citation hover.
- **Ask Well** (`ask-well` / `ask-well-border` / `ask-placeholder`): The query textarea. A proof-tinted zinc field so the empty ask box is the first landing, not another mute inset. Placeholder is `#9aa3b8` for contrast on the tinted well. Not a pane fill.
- **Answer Well** (`answer-well` / `answer-border`): The grounded answer card. A 16% proof wash with a mixed proof hairline so the claim reads apart from Trace cards. Omitted on abstain.
- **Canvas Well** (`canvas`): The document stage behind the page PNG, slightly darker than the chassis.
- **Zinc Hairline** (`zinc-border`): Every seam: top bar, pane splits, fields, cards, readout, ghost.
- **Zinc Ink** (`zinc-text`): Body, wordmark, panel heads, Ask label, citation quotes.
- **Zinc Mute** (`zinc-muted`): Thesis, instrument labels, empty copy, unpressed modes, unverified-neutral captions.
- **Fault Rose** (`fault` / `fault-well`): Request-failure banner in Ask.
- **Abstain Amber** (`abstain` / `abstain-well`): Abstain banner in Ask. Does not replace the empty canvas.

### Named Rules
**The White Ask Rule.** Ask is zinc-white on near-black ink. A blue Ask, a cadmium Ask, or a full-width enamel plate is out of world.

**The Blue-for-Proof Rule.** Proof blue marks the bbox, the current citation, Verified, a checked switch, focus, the query well tint, and the answer well. If a screen needs more blue, the finder has already been overused. It is not a button fill, a heading color, or a pane background.

## Typography

**Display Font:** Geist (with ui-sans-serif, system-ui)
**Body Font:** Geist (same stack, 15px on the root)
**Label/Mono Font:** Geist Mono (with ui-monospace)

**Character:** A dense dashboard sans. The wordmark is a slightly heavy sentence-case name, not a condensed machine stamp. Mono is an instrument face for pages, ids, scores, and JSON.

### Hierarchy
- **Display** (560, 1rem, -0.02em): `PageAnchor` wordmark in the top bar.
- **Headline** (560, 0.875rem, -0.01em): `Ask`, `Document`, `Trace`, and `Citations` panel heads. Thesis uses the same size at body weight in mute.
- **Title** (560, 0.9rem): Ask label. Empty-canvas titles use the same weight.
- **Body** (400, 15px / 1.5): Answers (0.95rem), quotes (0.875rem), latch captions (0.9rem), banners (0.875rem). Thesis max-width is 52ch on desktop.
- **Label** (560, 0.8rem, 0.04em, uppercase): Mode segments (`text` / `visual` / `hybrid` and compare `TEXT` / `HYBRID`). Cite status is 0.75rem at body case.
- **Mono** (450, 0.75rem–0.8rem): Page readout, `doc_id`, cite index and `p. N`, `trace {id}`, scores, timings, JSON (0.75rem).

### Named Rules
**The Mono-for-Measure Rule.** Geist Mono is for counters, identifiers, and dumps. Wordmark, panel heads, mode chips, and Ask stay Geist sans. A mono wordmark is a defect.

## Layout

The overlay is a full-viewport column: a 48px top bar, then a three-pane shell. The top bar is `minmax(11rem, 1fr) minmax(0, 46rem) minmax(11rem, 1fr)`: wordmark, centered thesis, page readout plus Receipt. It pads `0.45rem 0.85rem` with a bottom hairline.

The shell is `minmax(16.5rem, 22vw) minmax(0, 1fr) minmax(16rem, 22vw)`. Ask and Trace are side indexes, not peer cards. Horizontal pane padding is `0.85rem`. Form stack gap is `0.7rem`. Citation rows stack at `0.3rem`. The document canvas margins `0.7rem` and is the remaining width.

Rhythm is dashboard-tight: `0.45rem` for control clusters, `0.7rem` for stacked blocks, `0.85rem` for pane inset. Body size is 15px.

At `960px` the top bar wraps (brand and utilities on row one, thesis full-width on row two, left-aligned). The shell becomes one column: Ask, Document, Trace, each separated by a bottom hairline. The page image may release its desktop max-height. Stacking does not make the three panes equal cards.

### Named Rules
**The Canvas Dominates Rule.** Ask stays about a fifth of the width, Trace about a fifth, the document canvas takes the rest. If the three panes can be swapped without changing the page, the chassis is wrong.

## Elevation & Depth

Depth is hairline and tone, not card lift. Panes share the chassis fill and split with a 1px zinc hairline. Fields and Trace cards step to `zinc-field` or `zinc-panel`. The query and the grounded answer step to proof-tinted wells. There is no inset enamel glaze and no punched-well shadow on inputs.

The one offset shadow is the page PNG on the canvas: a dark ambient under the paper so the document reads as an object in the well. Trace cards and Ask chrome stay flat. The bbox is an inset 2px proof ring, not a drop shadow.

### Shadow Vocabulary
- **Page stage** (`box-shadow: 0 18px 40px rgb(0 0 0 / 35%)`): The cited page PNG only, sitting on the canvas well.
- **BBox ring** (`box-shadow: inset 0 0 0 2px` proof, plus `proof-wash` fill): The selected region on that page.

### Named Rules
**The Hairline Depth Rule.** Chrome is flat. Separate surfaces with 1px zinc hairlines and one-step fills. Do not lift Ask, Trace, or the top bar. The page on the canvas is the only object that casts.

## Shapes

Surfaces and Ask use 6px. Compact chrome uses 4px: ghost Receipt, page readout, inner mode chips, banners, citation rows, JSON well, and the 1.35rem mark. Switches are the only pills (999px track and thumb).

Hairlines are 1px solid zinc-border. The selected citation adds a 1px proof hairline. The bbox is a sharp rectangle aligned to the citation, not a rounded highlight. Trace is captioned tables inside 6px cards, not a chip list.

### Named Rules
**The Six-and-Four Rule.** 6px on panes, fields, Ask, canvas, and Trace cards. 4px on compact controls. Pills only on switches. 16px consumer cards and circular icon buttons are out of world.

## Components

Quiet zinc chrome. One white Ask. Proof is a box on the page.

### Buttons
- **Shape:** 6px on Ask, 4px on ghost Receipt and inner mode chips. Ask has no border. Ghost and the mode track use a 1px zinc hairline.
- **Primary (Ask):** Full-width of the Ask pane, min-height 2.25rem, Geist 560 0.9rem, `ask` fill and `ask-ink`. Trailing 16px stroke arrow. Hover: `brightness(1.06)`. Disabled/busy: opacity 0.55, wait cursor, label `Asking`.
- **Ghost (Receipt):** Transparent, min-height 1.85rem, padding `0 0.6rem`, zinc ink, optional 16px stroke icon. Hover fills `zinc-field`. Disabled: opacity 0.45.
- **Mode segments:** Three equal cells in a 6px `zinc-field` track (padding and gap 0.15rem). Unpressed: mute, transparent. Hover (unpressed only): zinc ink on a 5% white wash. Pressed (`aria-pressed="true"`): the same white chip as Ask, with `ask-ink` that stays dark on hover. Compare uses the same track at two columns. Uppercase 0.8rem 560 with 0.04em.
- **Focus:** 2px solid proof, 2px offset, on every control.

### Chips
Not used. Retrieval mode is the segmented track above. Verified is a 0.75rem proof-colored status line with a 12px stroke check, not a pill.

### Cards / Containers
- **Corner Style:** 6px on Trace cards, answer block, canvas, and query.
- **Background:** Chassis on panes; `zinc-panel` on Trace cards; `ask-well` on the query; `answer-well` on the grounded answer; `zinc-field` on remaining inset wells.
- **Shadow Strategy:** Flat chrome; page-stage shadow only on the PNG. See Elevation.
- **Border:** 1px zinc hairline on Trace cards, canvas, and fields. Query uses `ask-well-border`. Answer uses `answer-border`. Current citation uses a proof hairline.
- **Internal Padding:** Trace cards `0.65rem 0.7rem`; answer `0.75rem 0.8rem`; pane inset `0.85rem`.

### Inputs / Fields
- **Style:** Query is an `ask-well`, 1px `ask-well-border`, 6px, min-height 6.5rem, zinc ink, `#9aa3b8` placeholder.
- **Focus:** The global proof ring. No glow.
- **Switches:** 1.85 × 1.05rem pills. Off track `#2a2a2e` with `#c7c7cc` thumb; on track is proof with a white thumb. Captions are 0.9rem Geist (`Strict`, `Compare TEXT`).
- **Error / Disabled:** Request failure is a fault banner in Ask. Abstain is an amber banner; the answer block is omitted; the canvas shows `No verified region` while citations may remain.

### Navigation
One route. The top bar is identity and utilities, not a site nav. Panel heads are 0.875rem 560 with mute 16px stroke glyphs. Trace is an index, not a menu.

### Page readout
Compact 4px field in the top bar. Copy is `p. N` or `No page`, Geist Mono ~0.75rem mute. It is a live page label, not a film-frame odometer.

### Citation row
Full-width transparent button, 4px, three columns: mono index, quote body, mono `p. N`. Status is `Verified` in proof or `Unverified` / `Unverified unsupported` in fault. Quote clamps to two lines at 0.875rem. Hover fills `zinc-field`. Current (`aria-current="true"`): proof hairline and 8% proof tint.

### Bounding box
Absolutely positioned on the page PNG from the citation bbox. Inset 2px proof ring, 18% proof wash, min-height 8px, pointer-events none. Enters in 180ms ease-out from a center clip (`inset(46%)`). Respect `prefers-reduced-motion`. This is the citation, not a tooltip.

### Document canvas
6px well, 1px hairline, `canvas` fill. Loaded pages sit on a white stage with the page-stage shadow, max-height `calc(100vh - 7.5rem)` on desktop. Busy dims the image to 0.55. Empty copy is centered, max-width 22rem: `Ask the corpus` or `No verified region`.

### Trace cards
6px `zinc-panel` cards with 0.8rem mute captions and mono cells. Row rules are zinc-border at 80%. Trace id is mute mono. JSON disclosure is a 4px `zinc-field` well, 0.75rem mono, max-height 16rem. Empty copy: `Trace prints after /v1/answer returns.`

## Do's and Don'ts

### Do:
- **Do** keep Ask near 22vw, Trace near 22vw, and let the document canvas take the rest, under a 48px zinc top bar.
- **Do** set operator type in Geist at 15px / 560 for names and actions, and measurements in Geist Mono.
- **Do** paint Ask and pressed mode chips zinc-white; draw the citation as a proof-blue bbox on the page PNG.
- **Do** refuse with an abstain banner, omit the answer block, and keep unverified citations visible for the trail.
- **Do** split panes with 1px zinc hairlines and 6px / 4px corners.

### Don't:
- **Don't** lay out chat, PDF, and sources as three equal cards.
- **Don't** revive enamel, sprockets, putty plates, cadmium reticles, Barlow, or a NO FRAME stamp.
- **Don't** paint Ask, panel heads, or pane fills in proof blue; blue is the finder.
- **Don't** introduce a green success token or a pill chip for verified / mode / strict.
- **Don't** lift Ask, Trace, or the top bar with drop shadows, or round chrome past 6px.
- **Don't** write a fluent answer into the canvas, or keep an answer block, when the system abstains.
