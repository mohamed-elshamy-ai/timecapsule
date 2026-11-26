# timecapsule design system

Read this before changing the site's UI. Do not introduce a new direction; extend this one. English only. Values below come from `docs/index.html` as of this commit.

## Concept

A timeline ruler: dated rows on a ruled sheet, with a highlight scanning down the events.

Theme: light.

## Color tokens

| Token | Value | Role |
|---|---|---|
| `--bg` | `#eef3f8` | page background |
| `--fg` | `#101a2e` | body text |
| `--mut` | `#45577a` | secondary text (AA on bg) |
| `--card` | `#ffffff` | card and panel surface |
| `--line` | `#cbd8e8` | borders and dividers |
| `--acc` | `#1d4ed8` | primary action, links, focus ring |
| `--accfg` | `#ffffff` | text on accent |
| `--code` | `#101a2e` | code block background |
| `--codefg` | `#dbe7ff` | code block text |
| `--warn` | `#b45309` | warning border and limits |

Contrast: every text node on the page is checked against WCAG AA (4.5:1, 3:1 for large text) with a script in the repo owner's QA harness. Keep it passing when you change a color.

## Type

| Token | Stack | Role |
|---|---|---|
| `--arabic` | `'Readex Pro',sans-serif` | Arabic font stack |
| `--body` | `'Public Sans','Readex Pro',system-ui,sans-serif` | body font stack |
| `--head` | `'Unbounded','Readex Pro',system-ui,sans-serif` | heading font stack |

Font sizes in use: `.86rem`, `1.5rem`, `1rem`, `.9rem`, `.72rem`, `clamp(2.1rem,8.5vw,3.2rem)`, `1.2rem`, `clamp(2rem,6.4vw,3.3rem)`, `1.25rem`.

## Spacing, radius, elevation

- Spacing values in use: `2px`, `4px`, `6px`, `8px`, `9px`, `10px`, `11px`, `12px`, `14px`, `16px`, `26px`, `30px`. Prefer these; do not add new ones.
- Radius: `--r` (16px). Use the token, not literals.
- Elevation: `4px 4px 0 var(--acc)`, `6px 6px 0 var(--acc)`

## Motion

- Durations in use: `.05s`, `.15s`, `.25s`, `.2s`, `.34s`, `.42s`, `0s`, `2s`, `4s`, `6s`, `8s`.
- Curves: `cubic-bezier(.16,1,.3,1)`, `cubic-bezier(.2,.8,.2,1)`, `cubic-bezier(.22,1.36,.32,1)`.
- Every animation sits behind `prefers-reduced-motion: reduce`, which turns animation and transition off.
- Motion shows state or order. It is never decoration.

## Components and states

- Button `.btn` (filled) and `.btn.alt` (outline): min height 44px, visible `:focus-visible` outline (2px accent), hover and active states.
- Card `.card`, warning card `.card.warn` (left border in `--warn`).
- Language toggle `.langtoggle` with `aria-pressed`.
- Code block `pre`: always LTR, monospace.
- Status words use `.ok b` and `.no b` colors (AA checked).

## RTL rules

- The language toggle sets `dir` and `lang` on `<html>`. Arabic text uses the `--arabic` font and line-height 1.75.
- Use logical CSS (`margin-inline`, `inset-inline-start`, `text-align:start`). No `left` or `right` for layout.
- Letter-spacing is 0 and text-transform none in Arabic.
- Code, terminal output and demo panels stay LTR (`direction:ltr`). Install and demo output stay English.
- Arabic is Egyptian-leaning plain language. Brand names and commands stay Latin.

## Microcopy voice

Plain, specific, honest about limits. Say what it does and what it does not. No hype, no invented numbers.

Examples from the site:

1. What was I working on?
2. Created Graduation_Project.pdf
3. Nothing is recorded until you add a folder.
4. No contents stored.
5. It sees file changes only.

## Do / Don't

| Do | Don't |
|---|---|
| State what is never stored | Hint at tracking |
| Show real demo output | Invent a busy week |
| Ruled lines at 32px | Free-form spacing |
| Blue for the active row and action | Blue for decoration |
| Say it does not see apps or websites | Imply full activity tracking |

## Known hard-coded values (should become tokens)

These literal colors appear in the CSS outside `:root`: `#17703f`, `#2e9e5b`, `#6ee7ff`, `#a8281b`, `#b794ff`, `#c0392b`, `#dde6f1`, `#e8efff`, `#fff`.
Also: status colors in `.ok b` and `.no b`, and several literal pixel sizes in component CSS. Move them into tokens next time that block is touched.
