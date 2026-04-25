# Frontend Design Architecture: Oracle Risk Console 2026

## 1. Design Intent and Product Personality
The redesigned Oracle dashboard is an Indonesian-language capital protection console for one operator who needs fewer, better decisions. The product should feel like a defensive market instrument panel: calm under noise, strict about entry quality, and explicit when the system is refusing to chase.

## 2. Audience and Use-Context Signals
- Primary user: one high-context operator monitoring Indonesian equities.
- Core tasks: review screener anomalies, validate only quant-confirmed pending signals, monitor active positions, and inspect resolved outcomes.
- Usage pattern: desktop-first during market routines, but still fully usable on mobile for quick checks and manual actions.

## 3. Visual Direction and Distinctive Moves
- Default surface: dark instrument-grid background with emerald risk rails, copper caution accents, ice-blue analysis markers, and ember danger states.
- Signature move: a "risk console" band above the stats that names the current selection mode before the operator sees any ticker count.
- Product tone: Indonesian copy everywhere on user-facing surfaces, with direct language that separates radar noise from actionable execution.

## 4. Color Science and Semantic Roles
- Base: ink, graphite, and smoke neutrals for low-glare operation.
- Positive/action: emerald for confirmed upside and healthy positions.
- Risk/critical: ember red for stop-loss, emergency alerts, and negative outcomes.
- Analysis/accent: copper for caution and ice-blue for analysis metadata.

## 5. Typographic Engineering and Hierarchy
- Display family: serif-led headline stack to make the dashboard feel authored instead of template-like.
- Interface family: dense sans stack for tables, chips, and numeric data.
- Hierarchy rule: uppercase micro-labels for metadata, medium-weight body text for analysis, and oversized numerics for market stats.

## 6. Spacing, Layout Rhythm, and Density Strategy
- Base grid: 8px.
- Rhythm: squared instrument sections with tight internal grouping and larger vertical breaks between operational zones.
- Density target: high-density desktop layout, recomposed into stacked narrative panels on tablet and mobile.

## 7. Token Architecture and Alias Strategy
- Primitive tokens store raw color, spacing, radius, and motion values.
- Semantic tokens map those primitives into intent such as background, panel, accent, positive, danger, muted, and focus.
- Component tokens consume semantic aliases for shells, chips, cards, and buttons so future copy or theme changes do not require component rewrites.

## 8. Responsive Strategy and Cross-Viewport Adaptation Matrix
- Mobile: put risk mode, pending action, and active positions first; radar becomes secondary context.
- Tablet: maintain two-column grouping for radar and signals, but keep the risk console as a full-width status band.
- Desktop: expose the full console grid with the risk band, radar, signal review, portfolio, and history visible without tab switching.

## 9. Interaction, Motion, and Feedback Rules
- Motion should be purposeful: fast instrument reveals, border emphasis on actionable cards, and no ambient motion that makes defensive waiting feel noisy.
- Reduced-motion mode must disable ambient movement while preserving state feedback.
- Refresh, scan, and action states should confirm immediately with clear Indonesian feedback.

## 10. Component Language, Morphology, and Shared Patterns
- Shared section shell with title, context line, and optional side action.
- Risk console banner exposes defensive/normal mode from win-rate and average PnL before the operator sees scanner counts.
- Signal cards combine ticker identity, source, expiry, duration window, price plan, embedded chart, reasoning, and action row.
- Portfolio cards and tables must expose entry, current price, target, stop-loss, PnL, tracking age, review cadence, and estimated duration.
- History surfaces must preserve outcome context and source attribution without hiding reasoning.

## 11. Context Hygiene and Approved Reference Boundaries
- Valid style context comes only from the current Oracle repository, the Indonesian equity workflow, and the current brief.
- Old generic dashboard memory and unrelated SaaS patterns are invalid context.
- Visual continuity is with Oracle product behavior, not with the previous monolithic UI skin.

## 12. Accessibility Non-Negotiables
- WCAG 2.2 AA is the blocking floor.
- Focus states must be visible on all buttons, pills, and card actions.
- Tables that collapse on small screens must preserve label-to-value clarity.
- Status, risk, and scanner source cannot rely on color alone; they need text labels and icon support.

## 13. Anti-Patterns to Avoid
- No mixed-language user-facing copy.
- No generic KPI cards floating over a startup gradient.
- No AI override copy that implies a rejected quant setup can become a BUY because of hype or volume alone.
- No hidden critical reasoning behind tooltips or expandable-only affordances.
- No implication that the daily screener list is a one-day profit target.

## 14. Implementation Notes for Future UI Tasks
- Preserve every current data surface: stats, anomalies, manual watchlist, pending signals, active portfolio, history, reasoning, source tags, timestamps, expiry, and price levels.
- Treat "daily radar" and "execution signal" as separate content types with separate copy rules.
- When recent performance is weak, the UI should make selectivity visible rather than celebrating scan volume.
- Estimated target duration is expressed in trading days, never in exact hours.
- Tracking reviews may happen hourly for risk detection, but target timing should remain day-based in the UI.
