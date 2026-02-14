# Front-End Design System

Codified design rules for generated WAT system front-ends. Read by `generate_frontend.py` to produce consistent, professional UIs.

## v1 Archetype: Professional SaaS

A clean, modern SaaS aesthetic for developer-facing and business tools. Prioritizes clarity, information density, and fast task completion.

---

## Typography

### Font Pairing

- **Headings**: Space Grotesk (Google Fonts) — geometric, technical, modern
- **Body**: DM Sans (Google Fonts) — clean, readable, pairs well with Space Grotesk
- **Monospace** (code/data): JetBrains Mono (Google Fonts) — for JSON viewers, code output, terminal-style displays

### Scale (rem, base 16px)

| Token       | Size    | Weight | Use                        |
|-------------|---------|--------|----------------------------|
| `display`   | 3rem    | 700    | Landing hero headline      |
| `h1`        | 2.25rem | 700    | Page titles                |
| `h2`        | 1.75rem | 600    | Section headings           |
| `h3`        | 1.25rem | 600    | Card/panel headings        |
| `body`      | 1rem    | 400    | Paragraph text             |
| `body-sm`   | 0.875rem| 400    | Secondary text, captions   |
| `caption`   | 0.75rem | 400    | Labels, timestamps         |
| `mono`      | 0.875rem| 400    | Code, data, terminal       |

### Rules

- Line height: 1.5 for body, 1.2 for headings
- Max line length: 65ch for body text
- No underlined text except links
- Headings use Space Grotesk; everything else uses DM Sans

---

## Color Palette

### Cool-Tech (Default)

| Token             | Light Mode    | Dark Mode     | Use                      |
|-------------------|---------------|---------------|--------------------------|
| `--bg-primary`    | `#FAFBFC`     | `#0F1117`     | Page background          |
| `--bg-secondary`  | `#F0F2F5`     | `#1A1D27`     | Card/panel background    |
| `--bg-tertiary`   | `#E4E7EB`     | `#252830`     | Hover states, borders    |
| `--text-primary`  | `#111827`     | `#F9FAFB`     | Headings, primary text   |
| `--text-secondary`| `#6B7280`     | `#9CA3AF`     | Secondary text, labels   |
| `--text-muted`    | `#9CA3AF`     | `#6B7280`     | Placeholders, disabled   |
| `--accent`        | `#3B82F6`     | `#60A5FA`     | Primary buttons, links   |
| `--accent-hover`  | `#2563EB`     | `#93C5FD`     | Button hover             |
| `--accent-subtle` | `#EFF6FF`     | `#1E3A5F`     | Badge backgrounds, chips |
| `--success`       | `#10B981`     | `#34D399`     | Success states           |
| `--warning`       | `#F59E0B`     | `#FBBF24`     | Warning states           |
| `--error`         | `#EF4444`     | `#F87171`     | Error states, destructive|
| `--border`        | `#E5E7EB`     | `#2D3039`     | Borders, dividers        |

### Contrast Requirements

- All text must meet WCAG AA (4.5:1 for normal text, 3:1 for large text)
- Interactive elements must have 3:1 contrast against adjacent colors
- Focus rings use `--accent` with 2px offset

---

## Spacing

### Grid System

- Base unit: 8px
- Spacing scale: 4, 8, 12, 16, 24, 32, 48, 64, 96
- Tailwind mapping: `space-1` (4px) through `space-24` (96px)

### Layout Spacing

| Context            | Value   | Tailwind  |
|--------------------|---------|-----------|
| Page padding       | 24-32px | `p-6`/`p-8` |
| Section gap        | 48px    | `gap-12`  |
| Card padding       | 24px    | `p-6`     |
| Form field gap     | 16px    | `gap-4`   |
| Button padding     | 12px 24px | `px-6 py-3` |
| Inline element gap | 8px     | `gap-2`   |

---

## Layout

### Responsive Breakpoints

| Breakpoint | Width    | Layout                     |
|------------|----------|----------------------------|
| `sm`       | 640px    | Single column, compact     |
| `md`       | 768px    | Two-column forms possible  |
| `lg`       | 1024px   | Sidebar + main content     |
| `xl`       | 1280px   | Full dashboard layout      |

### Page Structure

- **Marketing pages** (`(marketing)/`): Full-width, centered content, max-w-6xl
- **Dashboard pages** (`(dashboard)/`): Sidebar navigation (240px) + main content area
- Mobile: sidebar collapses to bottom nav or hamburger menu

### Asymmetric Layouts

- Hero sections: 60/40 or 55/45 text/visual split
- Dashboard: sidebar (240px fixed) + fluid main
- Form pages: form (max-w-2xl) + result panel (fluid)
- Avoid perfectly centered, symmetric layouts — slight asymmetry feels modern

---

## Components

### Cards

- Background: `--bg-secondary`
- Border: 1px solid `--border`
- Border radius: 12px (`rounded-xl`)
- Shadow: `shadow-sm` (light mode), no shadow (dark mode)
- Hover: `shadow-md` transition for interactive cards

### Buttons

| Variant    | Background      | Text            | Border          |
|------------|-----------------|-----------------|-----------------|
| Primary    | `--accent`      | white           | none            |
| Secondary  | transparent     | `--accent`      | 1px `--accent`  |
| Ghost      | transparent     | `--text-secondary` | none         |
| Destructive| `--error`       | white           | none            |

- Border radius: 8px (`rounded-lg`)
- Height: 40px (default), 32px (sm), 48px (lg)
- Transition: 150ms ease for background and shadow
- Disabled: 50% opacity, cursor-not-allowed
- Loading: spinner icon replaces text

### Form Fields

- Height: 40px
- Border: 1px solid `--border`
- Border radius: 8px
- Focus: 2px ring `--accent` with 2px offset
- Error: border `--error`, error message below in `--error` color
- Label: `body-sm` weight 500, `--text-primary`, 4px margin-bottom
- Placeholder: `--text-muted`

### Badges/Chips

- Background: `--accent-subtle`
- Text: `--accent`
- Border radius: 9999px (pill)
- Padding: 4px 12px
- Font size: `caption`

---

## Motion

### Framer Motion Defaults

```
// Page transitions
{ initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.3, ease: "easeOut" } }

// Staggered lists
{ parent: { staggerChildren: 0.05 }, child: { initial: { opacity: 0, y: 4 }, animate: { opacity: 1, y: 0 } } }

// Card hover
{ whileHover: { y: -2, shadow: "lg" }, transition: { duration: 0.15 } }

// Loading skeleton
{ animate: { opacity: [0.5, 1, 0.5] }, transition: { duration: 1.5, repeat: Infinity } }
```

### Rules

- Never animate layout shifts (no animating width/height of containers)
- Keep durations under 400ms — snappy, not cinematic
- Use `ease-out` for entrances, `ease-in` for exits
- Reduce motion: wrap animations in `useReducedMotion()` check
- No animations on first paint — only on interaction or route change

---

## Icons

- Library: Lucide React (`lucide-react`)
- Size: 16px (inline), 20px (buttons), 24px (standalone)
- Stroke width: 1.5 (default Lucide)
- Color: inherit from parent text color

### Common Mappings

| Action          | Icon              |
|-----------------|-------------------|
| Submit/Run      | `Play`            |
| Download        | `Download`        |
| Upload          | `Upload`          |
| Settings        | `Settings`        |
| Back/Cancel     | `ArrowLeft`       |
| Success         | `CheckCircle`     |
| Error           | `AlertCircle`     |
| Warning         | `AlertTriangle`   |
| Info            | `Info`            |
| Pipeline/Flow   | `Workflow`        |
| Tool            | `Wrench`          |
| File            | `FileText`        |
| JSON            | `Braces`          |
| PDF             | `FileText`        |
| CSV/Table       | `Table`           |
| Delete          | `Trash2`          |
| Edit            | `Pencil`          |
| Copy            | `Copy`            |
| External Link   | `ExternalLink`    |

---

## Result Viewers

### JSON Viewer

- Use monospace font (`JetBrains Mono`)
- Syntax highlighting with accent colors
- Collapsible nested objects (default: expand 2 levels)
- Copy-to-clipboard button

### PDF Viewer

- Inline preview using `<iframe>` or `<embed>` for the PDF blob URL
- Download button below the viewer
- Fallback: direct download link if inline preview fails

### CSV/Table Viewer

- Responsive table with horizontal scroll
- Sticky header row
- Alternating row backgrounds (`--bg-primary` / `--bg-secondary`)
- Download as CSV button

### File Download

- Card with file icon, filename, size, and download button
- Progress indicator during generation

---

## Accessibility

### Requirements

- All interactive elements must be keyboard-navigable
- Tab order follows visual order
- Focus ring: 2px solid `--accent`, 2px offset
- Skip-to-content link (visually hidden, visible on focus)
- ARIA labels on icon-only buttons
- Form error messages linked via `aria-describedby`
- Loading states announced via `aria-live="polite"`
- Color is never the only indicator — always pair with text or icon

### Heading Hierarchy

- One `<h1>` per page (page title)
- Sections use `<h2>`, subsections use `<h3>`
- Never skip heading levels

---

## Dark Mode

- Default: respect system preference via `prefers-color-scheme`
- Toggle: manual override stored in `localStorage`
- Implementation: CSS custom properties toggled by `[data-theme="dark"]` on `<html>`
- Tailwind: use `dark:` variants
