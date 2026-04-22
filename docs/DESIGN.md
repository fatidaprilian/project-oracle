# Frontend Design Architecture: Oracle Signals Dashboard

## 1. Design Intent and Product Personality
The Oracle Signals Dashboard is a real-time, terminal-inspired interface designed for rapid decision-making in stock trading. It abandons the bloated, multi-page SaaS structure in favor of a focused, high-density single-page application (SPA). The personality is authoritative, precise, and distinctly "Bloomberg-lite," prioritizing signal clarity over decorative aesthetics.

## 2. Audience and Use-Context Signals
- **Audience:** Sole trader (the user), operating with high context.
- **Context:** Quick glances to validate AI-synthesized stock signals. Decisions (BUY/IGNORE) must be made in seconds.
- **Environment:** Often viewed alongside other charts or via Telegram. The UI must feel like a mission-control center.

## 3. Visual Direction and Distinctive Moves
- **Dark Mode Default:** Extreme dark mode (`neutral-950`) to reduce eye strain during continuous monitoring.
- **Neon Accents:** Gradients (`emerald-400` to `cyan-500`) used strictly for the Oracle branding to create a distinct, authored tension against the stark background.
- **High-Contrast Signal Badges:** Immediate visual classification using `emerald-500` (BUY) and `rose-500` (IGNORE) with low-opacity backgrounds for readability.

## 4. Color Science and Semantic Roles
- **Background/Surface:** `neutral-950` (App background), `neutral-900` (Card surfaces), `neutral-800` (Borders/Dividers).
- **Text:** `neutral-100` (Primary), `neutral-400` (Secondary/Muted), `neutral-500` (Tertiary labels).
- **Semantics:**
  - *Positive/Action:* `emerald-500` (Buy actions, active tracking).
  - *Negative/Muted:* `rose-500` (Ignore actions, muted tracking).

## 5. Typographic Engineering and Hierarchy
- **Font:** Inter (or sans-serif default) prioritizing numbers and dense text.
- **Headers:** Heavy tracking, bold weights (`text-4xl font-extrabold tracking-tight`).
- **Metadata:** Uppercase, wide tracking, tiny sizes for labels (`text-xs uppercase tracking-wider`).
- **Body:** Relaxed line height (`leading-relaxed`) for AI reasoning blocks to improve scanning.

## 6. Spacing, Layout Rhythm, and Density Strategy
- **Base Grid:** 4px/8px Tailwind system.
- **Cards:** 24px padding (`p-6`), 16px gaps (`gap-4`), strict border radius (`rounded-2xl`) to contain complex information.
- **Density:** High density. Elements are grouped tightly by semantic relationship (e.g., Ticker + Bias Badge together).

## 7. Responsive Strategy and Cross-Viewport Adaptation Matrix
- **Mobile (`<768px`):** 1-column layout, full-width cards, stacked action buttons.
- **Tablet (`768px - 1024px`):** 2-column masonry or grid.
- **Desktop (`>1024px`):** 3-column grid (`grid-cols-3`) maximizing information density across wide screens.

## 8. Interaction, Motion, and Feedback Rules
- **Hover States:** Subtle border color transitions (`hover:border-neutral-700`) and slight background lightening on buttons.
- **Loading:** Skeleton pulses (`animate-pulse`) for the initial signal fetch.
- **Optimistic UI:** Clicking an action immediately updates the card state to "Tracking Active" or "Muted" without waiting for the network, providing instant perceived performance.

## 9. Component Language and Shared Patterns
Currently implemented as a monolithic architecture in `App.tsx` due to the hyper-focused scope of the pivot. If scaling is required:
- **`SignalCard`**: Contains the technical signal, reasoning, and action buttons.
- **`Badge`**: Reusable component for BUY/IGNORE visual identifiers.

## 10. Accessibility Non-Negotiables
- Minimum contrast ratios maintained (e.g., `emerald-400` on `emerald-500/10` over `neutral-900`).
- Clear focus outlines (Tailwind defaults) preserved for keyboard navigation.

## 11. Anti-Patterns to Avoid
- *No generic SaaS white-themes.*
- *No multi-page routing* for core actions (keep the user on the dashboard).
- *No hidden information behind tooltips* (AI reasoning must be fully visible).
