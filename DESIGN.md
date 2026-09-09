---
name: PageAnchor
description: A microfilm reader for grounded PDF answers; the page is a film frame, a citation is a cadmium reticle, a refusal is NO FRAME.
colors:
  reticle: "#d85a1a"
  hood: "#16181a"
  enamel: "#5c6158"
  enamel-dark: "#3e433c"
  enamel-edge: "#2a2e29"
  putty: "#d9d1bc"
  putty-ink: "#1a1c18"
  putty-muted: "#534e42"
  well: "#0e1012"
  led: "#e4e7df"
  led-dim: "#c5c9bf"
  fault: "#c43c2a"
  focus: "#f0ead8"
  plate: "#8a8676"
  fault-slip: "#f3d4ce"
  fault-ink: "#6b1c14"
  abstain-slip: "#efe3b8"
  abstain-ink: "#5c4a10"
  film: "#090a0b"
typography:
  display:
    fontFamily: "Barlow Condensed, Segoe UI, sans-serif"
    fontSize: "1.35rem"
    fontWeight: 700
    lineHeight: 1.4
    letterSpacing: "0.16em"
  headline:
    fontFamily: "Barlow Condensed, Segoe UI, sans-serif"
    fontSize: "0.95rem"
    fontWeight: 700
    lineHeight: 1.4
    letterSpacing: "0.14em"
  title:
    fontFamily: "Barlow Condensed, Segoe UI, sans-serif"
    fontSize: "1.05rem"
    fontWeight: 700
    lineHeight: 1.4
    letterSpacing: "0.12em"
  body:
    fontFamily: "Barlow, Segoe UI, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "normal"
  label:
    fontFamily: "Barlow Condensed, Segoe UI, sans-serif"
    fontSize: "0.78rem"
    fontWeight: 700
    lineHeight: 1.4
    letterSpacing: "0.12em"
  mono:
    fontFamily: "Azeret Mono, ui-monospace, monospace"
    fontSize: "0.78rem"
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "0.06em"
rounded:
  latch: "1px"
  sm: "2px"
  mode: "3px"
spacing:
  xs: "0.35rem"
  sm: "0.7rem"
  md: "1rem"
  lg: "1.25rem"
components:
  button-primary:
    backgroundColor: "{colors.plate}"
    textColor: "{colors.putty-ink}"
    typography: "{typography.title}"
    rounded: "{rounded.sm}"
    height: "3.15rem"
  button-primary-hover:
    backgroundColor: "{colors.plate}"
    textColor: "{colors.putty-ink}"
  button-primary-active:
    backgroundColor: "{colors.plate}"
    textColor: "{colors.putty-ink}"
  button-mode:
    backgroundColor: "{colors.enamel}"
    textColor: "{colors.led}"
    typography: "{typography.headline}"
    rounded: "{rounded.mode}"
    height: "2.6rem"
  button-mode-pressed:
    backgroundColor: "{colors.enamel-edge}"
    textColor: "{colors.led}"
    rounded: "{rounded.mode}"
    height: "2.6rem"
  input-query:
    backgroundColor: "{colors.well}"
    textColor: "{colors.led}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "0.7rem 0.75rem"
  citation-plate:
    backgroundColor: "{colors.putty}"
    textColor: "{colors.putty-ink}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "0.55rem 0.6rem"
  well-plate:
    backgroundColor: "{colors.putty}"
    textColor: "{colors.putty-ink}"
    rounded: "{rounded.sm}"
    padding: "0.65rem 0.7rem"
  frame-readout:
    backgroundColor: "{colors.well}"
    textColor: "{colors.led}"
    typography: "{typography.mono}"
    rounded: "{rounded.sm}"
    padding: "0.35rem 0.7rem"
  banner-fault:
    backgroundColor: "{colors.fault-slip}"
    textColor: "{colors.fault-ink}"
    rounded: "{rounded.sm}"
    padding: "0.65rem 0.7rem"
  banner-abstain:
    backgroundColor: "{colors.abstain-slip}"
    textColor: "{colors.abstain-ink}"
    rounded: "{rounded.sm}"
    padding: "0.65rem 0.7rem"
---

# Design System: PageAnchor

## Overview

**Creative North Star: "The Lighted Film Gate"**

PageAnchor is a microfilm reader, not a chat console. The visitor sits at a flocked hood with olive-gray enamel bezels. A query is loaded on the left catalog, the cited page appears as a film frame in the center gate, and the TRACE strip on the right prints the index. Belief lives in a boxed region on the page, or in a stamped refuse. Fluency in a card is not the product.

The machine is dense and tactile. Enamel, putty, and charcoal flock are tiled grain, not flat fills. Light is phosphor LED on dark metal, or dark ink on putty plates. The only hot color is matte cadmium, used as a finder reticle and as the VERIFIED stamp. Corners stay machined and nearly square. Motion is a short reticle snap, not page choreography.

This world rejects equal three-column chat / PDF / sources cards, round consumer chrome, and traffic-light status pills. A citation is not a highlighted snippet in a transcript. A refusal is not a polite empty state in the catalog; it is NO FRAME in the gate.

**Key Characteristics:**
- Charcoal flocked hood, olive-gray enamel bezels, putty catalog insets
- Center gate dominates; catalog and TRACE are side bezels, not peer cards
- Sprocket rails and inset charcoal wells as hardware, not decoration
- Barlow Condensed on the machine; Azeret Mono only for measurements
- Matte cadmium reticle and VERIFIED stamp as the sole proof accent
- Abstain empties the answer well and shows NO FRAME in the gate

## Colors

The palette is industrial enamel and flock, with one cadmium finder and oxide-red fault ink. Grain textures (`/textures/hood.png`, `enamel.png`, `putty.png`) ride on top of these fills; the fill is the fallback, the grain is the material.

### Primary
- **Matte Cadmium** (`reticle`): The finder. Drawn as a 2px inset box plus a 2px outline offset 3px, with a 16% cadmium wash, on the cited page region. The VERIFIED stamp uses the same hue as ink on putty. It is not a button fill, not a chart series, and not a page background.

### Secondary
- **Oxide Fault** (`fault`): Unverified lettering on a citation plate (`UNVERIFIED` in condensed caps). Not a success/fail pair with green. Unused CSS `--verified` green is not part of this system.

### Neutral
- **Flock Hood** (`hood`): The reader chassis and the cavity around the gate.
- **Olive Enamel** (`enamel`): Top rail and left catalog bezel, tiled with enamel grain and a faint top-lit glaze.
- **Enamel Dark** (`enamel-dark`): Right TRACE bezel and the gate-meta strip under the hood.
- **Enamel Edge** (`enamel-edge`): Hairline seams, mode-key borders, latch track.
- **Putty** (`putty`): Catalog insets: citation plates and the answer well. Tiled with putty grain. Ink on putty is `putty-ink`; muted plate captions are `putty-muted`.
- **Charcoal Well** (`well`): Inset instrument windows: query field, frame readout, odometer, TRACE JSON. LED type sits here, never putty ink.
- **Film Well** (`film`): The lighted gate behind the page PNG, ringed by a 6px `#111315` frame.
- **Phosphor LED** (`led`): Type on enamel and in wells. Dimmer instrument labels use `led-dim`.
- **Putty Plate** (`plate`): Fallback body of the primary LOAD FRAME control when the riveted-plate raster is absent.
- **Lamp Focus** (`focus`): Keyboard ring only (`2px` solid, `2px` offset).
- **Fault Slip** (`fault-slip` / `fault-ink`): Catalog banner when the request fails.
- **Abstain Slip** (`abstain-slip` / `abstain-ink`): Catalog banner when the model abstains. The gate still shows NO FRAME; this slip does not replace it.

### Named Rules
**The Cadmium Finder Rule.** Cadmium marks proof: the page reticle and the VERIFIED stamp. If a screen needs more orange, the finder has already been overused.

**The LED-on-Enamel Rule.** Phosphor LED type lives on enamel and in charcoal wells. Putty ink lives on putty plates. Do not park dark body copy on the hood, and do not park LED type on putty.

## Typography

**Display Font:** Barlow Condensed (with Segoe UI, sans-serif)
**Body Font:** Barlow (with Segoe UI, sans-serif)
**Label/Mono Font:** Azeret Mono (with ui-monospace)

**Character:** Condensed industrial sans is the machine voice: wordmark, bezels, keys, actions. Barlow regular is the catalog reading voice: thesis, quotes, answers. Mono is an instrument face, never a display face.

### Hierarchy
- **Display** (700, 1.35rem, 0.16em, uppercase): `PageAnchor` wordmark on the top enamel rail.
- **Headline** (700, 0.95rem, 0.14em, uppercase): TRACE `panel-title`, telemetry captions, enamel section labels.
- **Title** (700, 1.05rem, 0.12em, uppercase): Primary LOAD FRAME action.
- **Body** (400, 15px / 0.92rem, 1.4): Thesis (max ~42ch), quotes, answers, leader copy, banners.
- **Label** (700, 0.78rem–0.85rem, 0.08em–0.12em, uppercase): Plate captions, STRICT caption, mode keys, UNVERIFIED.
- **Mono** (500, 0.72rem–0.95rem, 0.06em–0.08em): `FRAME 00N` readout and odometer, citation `doc_id p.N`, TRACE id, scores, timings, JSON dump.

### Named Rules
**The Mono-for-Measure Rule.** Azeret Mono is for counters, identifiers, and scores. Wordmark, mode keys, TRACE headings, and LOAD FRAME stay condensed sans. A mono headline is a defect.

## Layout

The reader is a full-viewport column: enamel top rail, then a three-pane `deck`. The deck is `minmax(17.5rem, 22vw) minmax(0, 1fr) minmax(16rem, 21vw)`. The center gate is the remaining width and must read as the largest pane. Catalog and TRACE pad `1rem 0.95rem 1.25rem`. The top rail pads `0.7rem 1rem` and is `1fr auto auto` (wordmark, thesis, frame readout).

The gate hood is a three-column film path: `18px` sprocket, page well, `18px` sprocket. Hood min-height is `28rem`. The page image may grow to `calc(100vh - 8.5rem)`. An enamel-dark meta strip under the hood holds the `doc_id` and a nested odometer.

Rhythm is tight instrument spacing: `0.35rem` between mode keys, `0.7rem` in the ask stack, `0.4rem` between citation plates. The catalog is a vertical stack (modes, strict, query well, LOAD FRAME, banners, answer, citations), not a toolbar.

At `960px` the top rail and the deck each collapse to one column. The gate well may release its desktop max-height. Stacking does not make the three panes equal cards; the gate still occupies the middle of the story.

### Named Rules
**The Gate Dominates Rule.** Catalog stays about a fifth of the width, TRACE about a fifth, gate takes the rest. If the three panes can be swapped without changing the page, the chassis is wrong.

## Elevation & Depth

Depth is cavity, not card lift. The hood is a dark flocked recess (`inset 0 30px 50px rgb(0 0 0 / 55%)`). Instrument windows are punched in (`inset 0 2px 6px` to `inset 0 3px 8px` at 55% black). Enamel bezels are top-glazed metal with a hairline `enamel-edge` seam. Catalog and TRACE shade inward toward the gate (`inset ±10px 0 18px`). Putty plates sit inset in the catalog, not raised off it.

The top enamel rail is the one place a drop shadow is structural: `0 8px 18px rgb(0 0 0 / 35%)` plus an inset highlight, so the rail sits on the hood. That is a bezel, not a floating card. Mode keys and LOAD FRAME use inset highlights at rest and inset crush when pressed (`translateY(2px)`).

The film well is a hard optical frame: `inset 0 0 0 1px #000` and `0 0 0 6px #111315`. The reticle is a finder drawn on the page, not a shadow.

### Shadow Vocabulary
- **Bezel rail** (`box-shadow: inset 0 1px 0 rgb(255 255 255 / 16%), 0 8px 18px rgb(0 0 0 / 35%)`): Top enamel bar only.
- **Hood cavity** (`box-shadow: inset 0 30px 50px rgb(0 0 0 / 55%)`): Flocked gate surround.
- **Well punch** (`box-shadow: inset 0 3px 8px rgb(0 0 0 / 55%)`): Query field; readout and odometer use the same family at 2px/6px.
- **Putty inset** (`box-shadow: inset 0 2px 8px rgb(0 0 0 / 28%)`): Answer well and citation plates (current citation plates use 2px/6px at 22%).
- **Key glaze** (`box-shadow: inset 0 1px 0 rgb(255 255 255 / 18%)`): Unpressed mode keys.
- **Key crush** (`box-shadow: inset 0 3px 6px rgb(0 0 0 / 55%)`): Pressed mode keys and busy LOAD FRAME.
- **Pane shade** (`box-shadow: inset -10px 0 18px rgb(0 0 0 / 22%)` catalog; mirrored on TRACE): Bezel edges toward the gate.

### Named Rules
**The Cavity Rule.** Recess the well; do not lift the plate. Offset drop shadows belong only to the top enamel rail sitting on the hood.

## Shapes

Corners are machined, almost square. Instrument wells, plates, banners, and LOAD FRAME use `2px`. Mode keys use `3px`. The STRICT track and thumb use `1px`. There are no pills, no 8–16px cards, no circular icon buttons.

Sprocket rails are a repeating rectangular perforation (`11px` black, `3px` gap implied in the 14/26 rhythm, then `#2a2d30` tooth). The reticle is a rectangle aligned to the citation bbox, not a rounded highlight. The film well is a hard-rect optical aperture.

Hairlines are `1px solid` `enamel-edge` on keys and LOAD FRAME, or `rgb(255 255 255 / 10%)` row rules in TRACE. TRACE is a collapsed data table, not a card list.

### Named Rules
**The Machined Corner Rule.** If a radius reads as a consumer control (pill, 8px+ card), it is out of world. Stay at 1–3px.

## Components

Hardware, not UI kit. Resting chrome is enamel grain. Operator text is an inset well. Evidence is putty. Proof is cadmium on the page.

### Buttons
- **Shape:** Machined rectangle (`2px` on LOAD FRAME, `3px` on mode keys), `1px` enamel-edge border, inset glaze.
- **Primary (LOAD FRAME):** Riveted enamel plate, min-height `3.15rem`, condensed 700 1.05rem, 0.12em, uppercase, `plate` body with `putty-ink`. Hover: brightness 1.04. Active/busy: `translateY(2px)` and inset crush. Disabled/busy: `opacity: 0.7`, wait cursor. Busy label in the build is `Advancing`.
- **Mode keys:** Three equal enamel keys (TEXT / VISUAL / HYBRID). Unpressed: vertical enamel gradient `#6b7068` to `#4f544c`. Pressed (`aria-pressed="true"`): `#2d322c` to `#1f221e` with inset crush. Hover: brightness 1.06.
- **Focus:** `2px` `focus` outline, `2px` offset, on all controls.

### Chips
Not used. Retrieval mode is three hardware keys, not a chip row. Verified is a raster stamp, not a chip.

### Cards / Containers
- **Corner Style:** `2px` on putty plates; bezels themselves have no radius.
- **Background:** Enamel grain on catalog and TRACE; putty grain on answer and citation plates; flock on the hood.
- **Shadow Strategy:** Inset only; see Elevation.
- **Border:** Enamel hairline on keys; cadmium 2px ring on the selected citation (`aria-current="true"`).
- **Internal Padding:** Putty wells `0.65rem 0.7rem`; citations `0.55rem 0.6rem`.

### Inputs / Fields
- **Style:** Query is a charcoal well, no border, `2px` radius, min-height `6rem`, LED type, placeholder `#9aa193`.
- **Focus:** The global `focus` ring. No glow.
- **STRICT:** An operator latch on the catalog bezel (condensed uppercase caption). The current track-and-thumb is a CSS stand-in, not the plate language to copy.
- **Error / Disabled:** Request failure is a fault slip in the catalog. Abstain is an abstain slip plus NO FRAME in the gate; the answer well is omitted.

### Navigation
There is one route. The top rail is identity and frame count, not a nav bar. TRACE is an index strip, not a menu.

### Frame readout
Tabular instrument in a punched well. Copy is `FRAME 00N` or `FRAME ---`, Azeret Mono ~0.95rem on the rail and ~0.78rem in the gate odometer. Zero-pad page numbers; do not invent a seven-segment font.

### Citation plate
Full-width putty button. Meta row is mono `doc_id p.N` plus either the VERIFIED stamp (`4.8rem × 1.55rem`, cropped to the inked word) or condensed `UNVERIFIED` in `fault`. Quote is Barlow 0.92rem. Selected plate gets the cadmium ring. Hover may lighten the putty to `#e7e0ce`.

### Cadmium reticle
Absolutely positioned on the page PNG from the citation bbox. `2px` inset cadmium, `2px` outline, `3px` offset, 16% cadmium wash. Enters in `220ms ease-out` from a center clip (`clip-path: inset(48%)`) to full. Pointer events none. This is the citation, not a tooltip.

### NO FRAME leader
Centered in the idle/abstain gate. The NO FRAME stamp (stencil condensed on flock) sits above a short abstain reason. Max width `22rem`. The catalog answer well stays empty.

### TRACE strip
Enamel-dark bezel. Condensed `TRACE` title, mono `trace {id}`, then captioned tables (Hits, Verify, Timings ms) with condensed uppercase headers and mono cells. Optional `Trace JSON` disclosure into a `0.68rem` mono well, max-height `18rem`. Empty copy: `The TRACE strip prints after /v1/answer returns.`

## Do's and Don'ts

### Do:
- **Do** keep the cited page PNG in the flocked gate with 18px sprocket rails, and draw the bbox as a cadmium reticle on that image.
- **Do** set machine lettering in Barlow Condensed uppercase on enamel, and measurements in Azeret Mono inside charcoal wells.
- **Do** put quotes and answers on putty plates with putty ink; put operator controls on the left enamel bezel.
- **Do** refuse in the gate with NO FRAME and keep the answer well unrendered when `abstain` is true.
- **Do** mark verified citations with the cadmium VERIFIED stamp raster, not with a color fill.

### Don't:
- **Don't** lay out chat, PDF, and sources as three equal cards.
- **Don't** use Azeret Mono for the wordmark, mode keys, TRACE headings, or LOAD FRAME.
- **Don't** introduce a green success token, a pill chip, or a glyph icon for verified / mode / strict.
- **Don't** lift catalog or TRACE as drop-shadowed cards, or round them past 3px.
- **Don't** write a fluent answer into the gate, or keep an answer well, when the system abstains.
- **Don't** spend cadmium on chrome, charts, or decorative rules; it is the finder.
