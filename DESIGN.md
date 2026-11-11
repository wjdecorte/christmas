---
name: North Georgia Holiday Events
description: A colorful Christmas field guide in red, green, silver and gold.
colors:
  evergreen: "#0f5138"
  cranberry: "#b32339"
  gold: "#8a6419"
  cream: "#f7f7f4"
  paper: "#ffffff"
  ink: "#183b2a"
  muted: "#56665f"
  border: "#d6dde1"
  field-border: "#a8b6b1"
  quiet-surface: "#edf1f4"
  selected-surface: "#e5f0e9"
  selected-border: "#0f5138"
  verified-ink: "#2e5c3c"
  verified-surface: "#e8eddf"
  unverified-ink: "#785823"
  unverified-surface: "#f6eed9"
  masthead-red: "#a91f35"
  gold-bright: "#edc96c"
  gold-surface: "#fbf2da"
  silver: "#d8e0e8"
  silver-surface: "#edf1f4"
  red-surface: "#fbecef"
  green-surface: "#e5f0e9"
  category-gold: "#855b11"
  category-silver: "#405769"
  category-green: "#175136"
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
  intro: "14px"
  brand: "11px"
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

A colorful Christmas guide whose identity comes from a Christmas-red masthead, evergreen seasonal panels, silver quiet surfaces and gold highlights. Jason's November 11, 2026 request supersedes the earlier understated palette while retaining the local field-guide character, typography, layouts and functionality. This document captures the implemented visual system in `frontend/src/style.css` and the shared icon in `frontend/public/favicon.svg`.

**Key Characteristics:**
- Red identity, green wayfinding, silver support surfaces and gold highlights.
- Literary serif headings paired with practical sans-serif controls.
- Flat white event records with colored date and category chips.
- Clearly labeled verification status and visible keyboard focus.
- A Christmas tree-and-star icon shared by the masthead, footer and browser favicon.

## Colors

The festive palette uses red and green for structure and emphasis, silver for quiet surfaces and gold for highlights. Frontmatter contains normative reusable values; the `cream` token name remains for the now pale neutral page canvas.

### Primary
- **Evergreen:** seasonal intro, map heading, primary actions, selected filters, selected date stamps and control text.
- **Christmas Red / Cranberry:** masthead identity (`masthead-red`), date stamps, default category chips, active navigation text, counts and link hover (`cranberry`).

### Secondary
- **Gold / Bright Gold / Gold Surface:** dark gold keyboard focus and active navigation underline; bright gold masthead rule, map-heading icon and tree star; pale gold highlights and today's calendar cell.
- **Silver / Silver Surface:** quiet category chips, browse controls, map legend and map note. Silver is a supporting surface and icon detail, not body text on white.
- **Red Surface / Green Surface:** seasonal summary tiles and category chips; green also marks selected records and venue panels.

### Neutral
- **Cream / Paper:** pale neutral page canvas and white contained working surfaces respectively.
- **Ink / Muted:** main text and supporting descriptions or metadata.
- **Border / Field Border:** silver section divisions and stronger editable field outlines.
- **Quiet Surface / Selected Surface / Selected Border:** silver secondary grouping and green synchronized record selection.
- **Verified Ink / Verified Surface:** green verification label pairing.
- **Unverified Ink / Unverified Surface:** amber uncertainty label pairing, distinct from decorative category chips.

**The Visible Certainty Rule.** Pair status color with explicit “Verified” or “Unverified” text. Preserve that distinction in list records and calendar entries.

## Typography

**Display Font:** locally bundled Lora, with serif fallback.
**Body Font:** locally bundled Source Sans 3, with sans-serif fallback.

Lora brings the literary holiday identity; Source Sans 3 keeps dates, filters, labels, and operational details easy to scan. Headings use balanced wrapping and regular weight. The hierarchy is contextual rather than a mathematical scale.

- **Display:** page title; the mobile intro settles at (29px). Detail titles use (clamp(28px, 3.5vw, 42px)).
- **Headline:** section headings; compact result headings use (22px), map headings (21px).
- **Title:** event names; medium widths use (18px), mobile restores (20px).
- **Body:** base reading text; detail descriptions use (19px) with (1.65) line-height. Detail paragraphs cap at (72ch).
- **Label:** form labels and control emphasis. Metadata uses (12–13px); verification labels use (11px).
- **Category:** uppercase, spaced category text on colored chips. Month stamps use (0.08em) tracking and a Lora date numeral (33px/1.25).

**The Scan Rule.** Use tabular numerals for dates, times, counts, and calendar day numbers.

## Layout

The shared shell caps at (1424px), centered with desktop side gutters from the spacing tokens. At (1100px) or narrower, main gutters become (24px); at (760px) or narrower they become (18px). The masthead remains full width around the centered shell.

The discovery surface uses adjacent list and map columns (1.03fr / 1fr), separated by (26px), then (18px) at medium widths. The list has (12px) record gaps and a desktop scroll cap (950px); the map is sticky (20px) from the viewport top. The map starts at (440px) tall and grows to (510px) above (1500px). Map-first mode uses (0.7fr / 1.4fr) and a (600px) canvas. These are discovery compositions, not mandatory templates for other screens.

Below the mobile breakpoint, list and map stack, the map loses stickiness, and its height becomes (360px). Search spans the filter grid; remaining fields use two columns with the filter disclosure below. Detail and editor columns become single-column. Keep the page within the viewport. The seven-column month calendar deliberately scrolls inside its own wrapper with a (700px) minimum grid width; the week calendar becomes a vertical day list.

Spacing is contextual: controls use compact gaps, panels use generous padding, and major sections have clear border-separated breathing room. Preserve actual component spacing rather than imposing an invented universal scale.

## Elevation & Depth

Surfaces are flat at rest. Tone, thin borders, and spacing convey hierarchy; event records do not carry decorative shadows. The floating filter popover has a structural shadow (`0 8px 25px #0f51381c`), while map pins use a small legibility shadow (`0 2px 6px #0f513844`). These are the only authored shadow roles.

**The Flat Surface Rule.** Reserve shadows for floating controls and geographic markers; preserve quiet record and panel surfaces.

## Shapes

Panels, map frames, records, and editor surfaces share the surface radius. Buttons have a smaller control radius; fields are slightly tighter. Verification badges use small corners and quick filters use pill-like ends. Borders are generally (1px). Navigation tabs are square-edged with a (3px) active underline. Geographic markers are circular with a (2px) white stroke.

## Components

### Buttons

Compact, clear actions. Secondary buttons use paper, evergreen text, and the quiet border; primary buttons fill with evergreen. Base minimum height is (40px), gap (8px), and weight (600). Secondary hover uses Quiet Surface; primary hover uses Primary Hover. Disabled controls reduce opacity to (0.55) and use a wait cursor. Text actions have no border, (28px) minimum height, and an underlined cranberry hover.

All keyboard targets use a gold outline (3px) with offset (4px). Preserve this on buttons, links, fields, and disclosures.

### Chips and Verification Badges

Quick filters use (12px) text, (30px) minimum height, and outlined transparent resting surfaces. Active filters fill evergreen with white text. Category chips default to red on pale red; concerts/theatre use gold, lights/ice skating silver, and markets/festivals green. Date stamps fill red with white month/day text and switch to evergreen when the record is selected. Verification badges pair explicit text with their semantic foreground/background and compact badge radius. Never substitute an unlabeled colored dot for certainty.

### Cards / Containers

Event records use paper, a quiet (1px) border, surface corners, and a horizontal date stamp plus body. Selected records use Selected Surface and Selected Border. Their background transition is (0.2s ease-out). Titles underline on hover. Calendar, login, and editor panels reuse the surface language. Empty/loading containers keep the same borders and corners with centered content; error and notice banners use restrained tinted surfaces.

### Inputs / Fields

Paper fields use evergreen text, Field Border, field corners, and a (42px) minimum height. Discovery filters strengthen the height to (45px) and use the quieter Border. Carets use cranberry. Textareas resize vertically with a (90px) minimum height. Form labels sit above fields with (5px) gaps. Do not remove focus outlines.

### Navigation

The Christmas-red masthead has a (3px) bright-gold bottom rule and holds the Lora identity with pale supporting copy. The view navigation uses (25px) gaps, muted resting labels, cranberry active text, and a dark-gold active underline. Tabs retain transparent backgrounds. On mobile the header note and admin text label hide, retaining the admin icon action.

### Event Map and Calendar

The map is a bordered, clipped white panel with an evergreen heading, white title, bright-gold icon, and silver legend and note. Circular markers use category colors and accessible record synchronization. Category marker variants include red concerts and parades, green markets, and gold lights; these are map semantics, not new global brand accents. Calendar cells retain quiet grid borders, tabular day numbers, and compact event buttons. Weekday headings fill evergreen with white labels; today uses pale gold. Event buttons use pale green, while uncertain entries use gold treatment and supporting information.

### Seasonal Identity

Use the same tree-and-star SVG for the browser favicon and the masthead/footer marks: evergreen rounded tile, white tree, gold star and trunk, red and silver ornaments. The masthead mark is (46px), (40px) on mobile, with a thin bright-gold border. Keep the SVG silhouette legible at favicon size. The seasonal intro uses evergreen with pale text and subtle decorative snowflake/star linework; summary shortcuts use pale red, green and gold tiles with explicit labels.

## Do's and Don'ts

### Do:
- **Do** preserve the approved Christmas red, green, silver and gold identity across discovery, calendar, detail, and admin views.
- **Do** use locally bundled Lora and Source Sans 3 with the established hierarchy.
- **Do** keep verification labels, keyboard focus, and selected records explicit.
- **Do** honor reduced-motion preferences by disabling transitions, animation, and smooth scrolling.
- **Do** preserve localized month-calendar scrolling while keeping the main page within the viewport.

### Don't:
- **Don't** add decorative card shadows or replace quiet paper surfaces with glossy treatments.
- **Don't** introduce synthetic photography as a substitute for the established typographic and icon identity.
- **Don't** convey verification or selection solely through color.
- **Don't** promote a discovery-specific list/map composition into a requirement for every screen.


### Discovery review

Admin → Review uses the existing evergreen, cream and gold tokens. Published/source comparisons highlight proposed values in pale gold; source evidence remains a separate link and expandable excerpt. Review fields preserve manual edits while typing, expose conflict recovery, and keep verification opt-in. Narrow screens contain horizontal comparison scrolling within the table; editable controls use at least 16px text. Public cancellation/postponement labels accompany verification labels.
