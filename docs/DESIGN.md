# Frontend Design Architecture: Oracle Ruang Kendali Bursa

## 1. Design Intent and Product Personality
The redesigned Oracle dashboard is an Indonesian-language market operations surface for one operator who needs to decide fast, not a generic analytics SaaS. The product should feel like a trading desk board: disciplined, direct, and slightly theatrical when a real signal appears.

## 2. Audience and Use-Context Signals
- Primary user: one high-context operator monitoring Indonesian equities.
- Core tasks: review screener anomalies, validate pending signals, monitor active positions, and inspect resolved outcomes.
- Usage pattern: desktop-first during market routines, but still fully usable on mobile for quick checks and manual actions.

## 3. Visual Direction and Distinctive Moves
- Default surface: deep graphite background with copper, emerald, and ice-blue semantic accents.
- Signature move: a "market tape" framing system with horizontal separators, compact chips, and a strong command-board header instead of a generic hero.
- Product tone: Indonesian copy everywhere on user-facing surfaces, with market language that clarifies watchlist versus execution.

## 4. Color Science and Semantic Roles
- Base: charcoal, graphite, and smoke neutrals for low-glare operation.
- Positive/action: emerald for confirmed upside and healthy positions.
- Risk/critical: ember red for stop-loss, emergency alerts, and negative outcomes.
- Analysis/accent: copper and ice-blue for scanner context, timestamps, and structural market metadata.

## 5. Typographic Engineering and Hierarchy
- Display family: serif-led headline stack to make the dashboard feel authored instead of template-like.
- Interface family: dense sans stack for tables, chips, and numeric data.
- Hierarchy rule: uppercase micro-labels for metadata, medium-weight body text for analysis, and oversized numerics for market stats.

## 6. Spacing, Layout Rhythm, and Density Strategy
- Base grid: 8px.
- Rhythm: dense horizontal sections with tight internal grouping and larger vertical breaks between operational zones.
- Density target: high-density desktop layout, recomposed into stacked narrative panels on tablet and mobile.

## 7. Token Architecture and Alias Strategy
- Primitive tokens store raw color, spacing, radius, and motion values.
- Semantic tokens map those primitives into intent such as background, panel, accent, positive, danger, muted, and focus.
- Component tokens consume semantic aliases for shells, chips, cards, and buttons so future copy or theme changes do not require component rewrites.

## 8. Responsive Strategy and Cross-Viewport Adaptation Matrix
- Mobile: stack sections into a single vertical command flow; actions become full-width; tables collapse into cards.
- Tablet: maintain two-column density where possible, but move portfolio and history below signal review.
- Desktop: use an editorial command-board grid where radar and controls support the main signal review surface.

## 9. Interaction, Motion, and Feedback Rules
- Motion should be purposeful: soft reveal on load, border glow on actionable cards, and ticker tape drift for ambient status only.
- Reduced-motion mode must disable ambient movement while preserving state feedback.
- Refresh, scan, and action states should confirm immediately with clear Indonesian feedback.

## 10. Component Language, Morphology, and Shared Patterns
- Shared section shell with title, context line, and optional side action.
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
- No hidden critical reasoning behind tooltips or expandable-only affordances.
- No implication that the daily screener list is a one-day profit target.

## 14. Implementation Notes for Future UI Tasks
- Preserve every current data surface: stats, anomalies, manual watchlist, pending signals, active portfolio, history, reasoning, source tags, timestamps, expiry, and price levels.
- Treat "daily radar" and "execution signal" as separate content types with separate copy rules.
- Estimated target duration is expressed in trading days, never in exact hours.
- Tracking reviews may happen hourly for risk detection, but target timing should remain day-based in the UI.
