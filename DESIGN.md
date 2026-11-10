---
name: North Georgia Holiday Events
description: A warm, understated holiday field guide for a local calendar.
colors:
  evergreen: "#183e32"
  cranberry: "#9b3345"
  gold: "#ae7935"
  cream: "#f8f5ee"
  paper: "#fffefa"
  ink: "#233d34"
  muted: "#606b60"
  border: "#dcded3"
  field-border: "#b7bfb2"
  quiet-surface: "#eeeee4"
  selected-surface: "#e8efdf"
  selected-border: "#527063"
  verified-ink: "#2e5c3c"
  verified-surface: "#e8eddf"
  unverified-ink: "#785823"
  unverified-surface: "#f6eed9"
  primary-hover: "#2c5843"
typography:
  display:
    fontFamily: "Lora, serif"
    fontSize: "clamp(28px, 3.4vw, 45px)"
    fontWeight: 400
    lineHeight: 1.22
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "Lora, serif"
    fontSize: "23px"
    fontWeight: 400
    lineHeight: 1.35
  title:
    fontFamily: "Lora, serif"
    fontSize: "20px"
    fontWeight: 400
    lineHeight: 1.3
    letterSpacing: "-0.01em"
  body:
    fontFamily: '"Source Sans 3", sans-serif'
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: '"Source Sans 3", sans-serif'
    fontSize: "14px"
    fontWeight: 600
    lineHeight: 1.5
  category:
    fontFamily: '"Source Sans 3", sans-serif'
    fontSize: "11px"
    fontWeight: 600
    lineHeight: 1.5
    letterSpacing: "0.075em"
rounded:
  badge: "4px"
  field: "6px"
  control: "7px"
  fieldset: "8px"
  surface: "12px"
  chip: "18px"
spacing:
  inline: "8px"
  compact: "12px"
  field-gap: "16px"
  panel: "20px"
  generous: "24px"
  desktop-gutter: "40px"
components:
  button-primary:
    backgroundColor: "{colors.evergreen}"
    textColor: "{colors.paper}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "8px 14px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-secondary:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.evergreen}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "8px 14px"
  field:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.evergreen}"
    rounded: "{rounded.field}"
    padding: "9px 11px"
  event-card:
    backgroundColor: "{colors.paper}"
    rounded: "{rounded.surface}"
    padding: "21px"
  event-card-selected:
    backgroundColor: "{colors.selected-surface}"
  filter-chip:
    textColor: "{colors.evergreen}"
    rounded: "{rounded.chip}"
    padding: "3px 12px"
  view-navigation:
    textColor: "{colors.muted}"
    typography: "{typography.label}"
    padding: "12px 3px 15px"
  verification-badge:
    backgroundColor: "{colors.verified-surface}"
    textColor: "{colors.verified-ink}"
    rounded: "{rounded.badge}"
    padding: "2px 6px"
  unverified-badge:
    backgroundColor: "{colors.unverified-surface}"
    textColor: "{colors.unverified-ink}"
    rounded: "{rounded.badge}"
    padding: "2px 6px"
---

# Design System: North Georgia Holiday Events

## Overview

**Creative North Star: “The Local Holiday Field Guide”**

A warm, understated guide whose holiday character comes from cream, evergreen, cranberry, locally bundled type, and small outline icons. It is a working calendar with readable records, rather than an image-led promotional surface. The approved identity is retained from the original design note; this document captures the implemented system in `frontend/src/style.css`.

**Key Characteristics:**
- Warm paper surfaces with restrained borders and gently rounded corners.
- Literary serif headings paired with practical sans-serif controls.
- Dense enough to compare outings, with visibly labeled verification status.
- Quiet interaction feedback and clearly visible keyboard focus.

## Colors

The palette combines evergreen structure, cranberry emphasis, warm cream surroundings, and paper record surfaces. Frontmatter contains normative reusable values.

### Primary
- **Evergreen:** masthead, primary actions, selected filters, map pins, and control text.

### Secondary
- **Cranberry:** category labels, month labels, active navigation underline, small icon accents, and link hover.

### Tertiary
- **Muted Gold:** keyboard focus outlines; it is a functional accent.

### Neutral
- **Cream / Paper:** page canvas and contained working surfaces respectively.
- **Ink / Muted:** main text and supporting descriptions or metadata.
- **Border / Field Border:** quiet section divisions and stronger editable field outlines.
- **Quiet Surface / Selected Surface / Selected Border:** secondary grouping and synchronized record selection.
- **Verified Ink / Verified Surface:** green verification label pairing.
- **Unverified Ink / Unverified Surface:** amber uncertainty label pairing.

**The Visible Certainty Rule.** Pair status color with explicit “Verified” or “Unverified” text. Preserve that distinction in list records and calendar entries.

## Typography

**Display Font:** locally bundled Lora, with serif fallback.
**Body Font:** locally bundled Source Sans 3, with sans-serif fallback.

Lora brings the restrained holiday identity; Source Sans 3 keeps dates, filters, labels, and operational details easy to scan. Headings use balanced wrapping and regular weight. The hierarchy is contextual rather than a mathematical scale.

- **Display:** page title; the mobile intro settles at (29px). Detail titles use (clamp(28px, 3.5vw, 42px)).
- **Headline:** section headings; compact result headings use (22px), map headings (21px).
- **Title:** event names; medium widths use (18px), mobile restores (20px).
- **Body:** base reading text; detail descriptions use (19px) with (1.65) line-height. Detail paragraphs cap at (72ch).
- **Label:** form labels and control emphasis. Metadata uses (12–13px); verification labels use (11px).
- **Category:** uppercase, spaced cranberry text. Month stamps use (0.08em) tracking and a Lora date numeral (33px/1.25).

**The Scan Rule.** Use tabular numerals for dates, times, counts, and calendar day numbers.

## Layout

The shared shell caps at (1424px), centered with desktop side gutters from the spacing tokens. At (1100px) or narrower, main gutters become (24px); at (760px) or narrower they become (18px). The masthead remains full width around the centered shell.

The discovery surface uses adjacent list and map columns (1.03fr / 1fr), separated by (26px), then (18px) at medium widths. The list has (12px) record gaps and a desktop scroll cap (950px); the map is sticky (20px) from the viewport top. The map starts at (440px) tall and grows to (510px) above (1500px). Map-first mode uses (0.7fr / 1.4fr) and a (600px) canvas. These are discovery compositions, not mandatory templates for other screens.

Below the mobile breakpoint, list and map stack, the map loses stickiness, and its height becomes (360px). Search spans the filter grid; remaining fields use two columns with the filter disclosure below. Detail and editor columns become single-column. Keep the page within the viewport. The seven-column month calendar deliberately scrolls inside its own wrapper with a (700px) minimum grid width; the week calendar becomes a vertical day list.

Spacing is contextual: controls use compact gaps, panels use generous padding, and major sections have clear border-separated breathing room. Preserve actual component spacing rather than imposing an invented universal scale.

## Elevation & Depth

Surfaces are flat at rest. Tone, thin borders, and spacing convey hierarchy; event records do not carry decorative shadows. The floating filter popover has a structural shadow (`0 8px 25px #183e321c`), while map pins use a small legibility shadow (`0 2px 6px #183e3244`). These are the only authored shadow roles.

**The Flat Surface Rule.** Reserve shadows for floating controls and geographic markers; preserve quiet record and panel surfaces.

## Shapes

Panels, map frames, records, and editor surfaces share the surface radius. Buttons have a smaller control radius; fields are slightly tighter. Verification badges use small corners and quick filters use pill-like ends. Borders are generally (1px). Navigation tabs are square-edged with a (3px) active underline. Geographic markers are circular with a (2px) white stroke.

## Components

### Buttons

Compact, clear actions. Secondary buttons use paper, evergreen text, and the quiet border; primary buttons fill with evergreen. Base minimum height is (40px), gap (8px), and weight (600). Secondary hover uses Quiet Surface; primary hover uses Primary Hover. Disabled controls reduce opacity to (0.55) and use a wait cursor. Text actions have no border, (28px) minimum height, and an underlined cranberry hover.

All keyboard targets use a gold outline (3px) with offset (4px). Preserve this on buttons, links, fields, and disclosures.

### Chips and Verification Badges

Quick filters use (12px) text, (30px) minimum height, and outlined transparent resting surfaces. Active filters fill evergreen with white text. Verification badges pair explicit text with their semantic foreground/background and compact badge radius. Never substitute an unlabeled colored dot for certainty.

### Cards / Containers

Event records use paper, a quiet (1px) border, surface corners, and a horizontal date stamp plus body. Selected records use Selected Surface and Selected Border. Their background transition is (0.2s ease-out). Titles underline on hover. Calendar, login, and editor panels reuse the surface language. Empty/loading containers keep the same borders and corners with centered content; error and notice banners use restrained tinted surfaces.

### Inputs / Fields

Paper fields use evergreen text, Field Border, field corners, and a (42px) minimum height. Discovery filters strengthen the height to (45px) and use the quieter Border. Carets use cranberry. Textareas resize vertically with a (90px) minimum height. Form labels sit above fields with (5px) gaps. Do not remove focus outlines.

### Navigation

The evergreen masthead holds the Lora identity and understated supporting copy. The view navigation uses (25px) gaps, muted resting labels, evergreen active text, and cranberry active underline. Tabs retain transparent backgrounds. On mobile the header note and admin text label hide, retaining the admin icon action.

### Event Map and Calendar

The map is a bordered, clipped paper panel with heading, canvas, legend, and note. Circular markers use category colors and accessible record synchronization. Category marker variants include cranberry concerts, brown parades, teal markets, and purple lights; these are map semantics, not new global brand accents. Calendar cells retain quiet grid borders, tabular day numbers, and compact event buttons; uncertain entries use amber treatment and supporting information.

## Do's and Don'ts

### Do:
- **Do** preserve the approved cream, evergreen, and cranberry identity across discovery, calendar, detail, and admin views.
- **Do** use locally bundled Lora and Source Sans 3 with the established hierarchy.
- **Do** keep verification labels, keyboard focus, and selected records explicit.
- **Do** honor reduced-motion preferences by disabling transitions, animation, and smooth scrolling.
- **Do** preserve localized month-calendar scrolling while keeping the main page within the viewport.

### Don't:
- **Don't** add decorative card shadows or replace quiet paper surfaces with glossy treatments.
- **Don't** introduce synthetic photography as a substitute for the established typographic and icon identity.
- **Don't** convey verification or selection solely through color.
- **Don't** promote a discovery-specific list/map composition into a requirement for every screen.
