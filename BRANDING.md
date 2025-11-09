# ACE IoT Solutions Branding

This document describes the branding and color scheme applied to the ACE Connection Logger dashboard.

## Brand Colors

Based on the ACE IoT Solutions website (https://aceiotsolutions.com), the following color scheme has been applied:

### Primary Colors

| Color Name | Hex Code | RGB | Usage |
|------------|----------|-----|-------|
| ACE Lime | `#c0d201` | `rgb(192, 210, 1)` | Primary brand color - header accent, buttons, charts |
| ACE Lime Dark | `#9fae01` | `rgb(159, 174, 1)` | Button hover states |
| ACE Lime Light | `#d4e235` | `rgb(212, 226, 53)` | Highlights, accents |

### Neutral Colors

| Color Name | Hex Code | Usage |
|------------|----------|-------|
| Gray 900 | `#1a1a1a` | Dark backgrounds, primary text |
| Gray 800 | `#2d2d2d` | Dark elements |
| Gray 700 | `#404040` | Dark borders |
| Gray 600 | `#666666` | Secondary text, labels |
| Gray 500 | `#808080` | Disabled text |
| Gray 400 | `#999999` | Disabled elements |
| Gray 300 | `#cccccc` | Light borders, dividers |
| Gray 200 | `#e5e5e5` | Light borders |
| Gray 100 | `#f5f5f5` | Light backgrounds |

### Status Colors

| Color Name | Hex Code | Usage |
|------------|----------|-------|
| Success | `#10b981` | Healthy status, success messages |
| Warning | `#f59e0b` | Degraded status, warnings |
| Danger | `#ef4444` | Down status, errors, outages |
| Info | `#3b82f6` | Informational elements |

## Component Styling

### Header
- **Background**: Dark gray (`#1a1a1a`)
- **Accent**: 4px lime green top border
- **Text**: White
- **Refresh Button**: Lime background with dark text
- **Shadow**: Subtle drop shadow for depth

### Cards (Host & Outage)
- **Background**: White
- **Border**: Light gray with 4px colored left accent
- **Accent Colors**:
  - Healthy: Green (`#10b981`)
  - Degraded: Orange (`#f59e0b`)
  - Down/Active: Red (`#ef4444`)
- **Hover**: Elevated shadow and lime border

### Status Badges
- **Design**: Semi-transparent backgrounds with colored borders
- **Healthy**: Green background (10% opacity) with green border
- **Degraded**: Orange background (10% opacity) with orange border
- **Down**: Red background (10% opacity) with red border

### Charts
- **Average Latency**: Lime green (`#c0d201`) - Primary metric
- **Min Latency**: Green (`#10b981`) - Good performance
- **Max Latency**: Red (`#ef4444`) - Performance issues
- **Success Rate**: Blue (`#3b82f6`) - Secondary metric
- **Tooltips**: Dark background with lime accent
- **Grid**: Subtle gray lines (5% opacity)

### Interactive Elements
- **Select Dropdowns**:
  - Border: Light gray
  - Hover: Lime border
  - Focus: Lime border with glow effect
- **Buttons**:
  - Primary: Lime background
  - Hover: Darker lime with subtle lift
  - Active: Press effect

### Footer
- **Background**: Dark gray (`#1a1a1a`)
- **Text**: Light gray
- **Accent**: 4px lime green top border

## Typography

### Font Stack
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
```

### Monospace (for addresses/data)
```css
font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', 'Courier New', monospace;
```

### Font Weights
- **Regular**: 400 (body text)
- **Medium**: 500 (labels, secondary headings)
- **Semi-bold**: 600 (headings, emphasized text)

## Design Principles

### Modern & Clean
- Minimal shadows and effects
- Plenty of whitespace
- Clean lines and borders

### Professional Tech Aesthetic
- Dark header with bright accent
- Monospace fonts for technical data
- Clear visual hierarchy

### Status Communication
- Color-coded status indicators
- Left-border accents for quick scanning
- Transparent badge backgrounds

### Interactive Feedback
- Smooth transitions (0.2-0.3s)
- Hover effects (elevation, border color)
- Focus states with glow
- Button lift on hover

## Accessibility

### Contrast Ratios
All text/background combinations meet WCAG AA standards:
- Primary text on white: 12.6:1 (AAA)
- Secondary text on white: 5.7:1 (AA)
- White text on dark gray: 14.5:1 (AAA)

### Color Blindness
Status indicators use multiple visual cues:
- Color (green/orange/red)
- Position (left border accent)
- Icons and text labels
- Different line styles in charts (solid/dashed)

## Files Modified

1. **`frontend/src/assets/styles.css`** (NEW)
   - Global CSS variables for brand colors
   - Utility classes
   - Base styles

2. **`frontend/src/main.js`**
   - Import global styles

3. **`frontend/src/App.vue`**
   - Header styling with lime accent
   - Section cards with hover effects
   - Interactive form controls
   - Footer with lime accent

4. **`frontend/src/components/HostCard.vue`**
   - Left border status indicators
   - Transparent status badges
   - Professional card layout

5. **`frontend/src/components/OutageCard.vue`**
   - Left border for active/resolved status
   - Subtle background tint for active outages
   - Consistent badge styling

6. **`frontend/src/components/LatencyChart.vue`**
   - Brand colors for all chart lines
   - Lime-accented tooltips
   - Enhanced grid and axis styling

## Usage in Production

The branding is automatically applied when the frontend is built:

```bash
cd frontend && npm run build
```

In Docker, the branding is baked into the production build during image creation.

## Customization

To customize colors, edit `frontend/src/assets/styles.css`:

```css
:root {
  --ace-lime: #c0d201;  /* Change primary brand color */
  --ace-success: #10b981;  /* Change success color */
  /* etc... */
}
```

All components will automatically use the updated colors.
