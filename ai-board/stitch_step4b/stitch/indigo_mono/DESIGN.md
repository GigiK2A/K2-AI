# Design System Document: The Intelligent Canvas

## 1. Overview & Creative North Star
**Creative North Star: "The Digital Curator"**
This design system moves beyond the utility of a standard dashboard to create an environment that feels like a high-end editorial workspace. Drawing inspiration from the precision of Linear and the spatial clarity of Vercel, "The Digital Curator" focuses on extreme intentionality. 

We reject the "boxy" nature of traditional SaaS. Instead of trapping content inside rigid containers, we allow information to breathe. The system breaks the template look through **intentional asymmetry**—where the 220px sidebar acts as a heavy anchor to a light, fluid stage—and **tonal depth**, where hierarchy is communicated through light and shadow rather than lines and boxes.

---

## 2. Colors & Surface Philosophy
The palette is a sophisticated study in neutrals, punctuated by a singular, authoritative Indigo accent.

### The "No-Line" Rule
Traditional 1px borders are a crutch. In this system, **sectioning is prohibited from using solid borders.** Instead, boundaries are defined by background shifts. Use `surface-container-low` for secondary content areas sitting on a `surface` background. This creates a "molded" look rather than a "drawn" one.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers of fine paper.
- **Base Layer:** `surface` (#f8f9fa) — The infinite canvas.
- **Secondary Anchors:** `surface-container-low` (#f1f4f6) — Used for the 220px sidebar or utility panels.
- **Interactive Elevated Elements:** `surface-container-lowest` (#ffffff) — Used for active workspace items to provide maximum "lift."

### Glass & Gradient Transitions
To avoid a flat, "Bootstrap" feel, floating elements (modals, popovers) must use **Glassmorphism**:
- **Background:** `surface` at 80% opacity.
- **Backdrop-blur:** 12px to 20px.
- **CTA Soul:** Main buttons should use a subtle linear gradient from `primary` (#4d44e3) to `primary_dim` (#4034d7) at a 145-degree angle. This adds a microscopic sense of curvature and "clickability."

---

## 3. Typography: Editorial Authority
We use **Inter** not just for legibility, but as a structural element. 

- **Display & Headlines:** Use `display-md` and `headline-sm` with tight letter-spacing (-0.02em). These should feel like titles in a premium architectural magazine—authoritative and sparse.
- **The Contrast Play:** Pair a `title-lg` (bold, dark `on_surface`) with `label-sm` (uppercase, tracking +5%, `on_surface_variant`). This high-contrast pairing creates an "internal hierarchy" within components that feels custom-built.
- **Body:** `body-md` is our workhorse. Ensure a line height of 1.5 to maintain the "Light and Clean" requirement.

---

## 4. Elevation & Depth: Tonal Layering
We move away from structural lines by using light physics.

- **The Layering Principle:** Depth is achieved by stacking tiers. Place a `surface-container-lowest` card on top of a `surface-container` section. The contrast between #ffffff and #eaeff1 is enough for the human eye to perceive depth without a border.
- **Ambient Shadows:** For floating elements that require a shadow (like a command menu), use:
  - `box-shadow: 0 20px 40px rgba(43, 52, 55, 0.05);`
  - The shadow color is a 5% opacity version of `on_surface`, creating a natural occlusion effect rather than a "dirty" grey blur.
- **The "Ghost Border" Fallback:** If a border is required for accessibility, it must be a **Ghost Border**: `outline-variant` (#abb3b7) at 20% opacity. 

---

## 5. Components

### Buttons
- **Primary:** Gradient from `primary` to `primary_dim`. Text is `on_primary`. Radius: `md` (0.375rem).
- **Secondary:** Surface `surface-container-highest` with `on_surface` text. No border.
- **Tertiary:** Ghost style. `on_surface_variant` text, shifting to `on_surface` and a subtle `surface-container-low` background on hover.

### Inputs & Fields
- **Search/Inputs:** Background `surface-container-lowest`, 1px Ghost Border. On focus, the border transitions to `primary` at 50% opacity with a 2px "glow" (spread) of the same color.
- **Labels:** Always use `label-md` in `on_surface_variant`.

### Lists & Navigation
- **The "No-Divider" Rule:** Lists in the 220px sidebar must not use horizontal dividers. Use 8px of vertical spacing (`margin-bottom`) and a `surface-container-high` background pill for the active state.
- **Sidebar Items:** `body-sm` typography with an 8px icon gap. Icons should be 18px, using the `outline` color.

### AI Board Specifics: The "Intelligence" Card
Instead of a standard card, use a "Bleed Card." It has no border and no shadow. It uses a slight background shift (`surface-container-low`) and a 4px left-accent border of `primary` only when the item is "Active" or "Processing."

---

## 6. Do’s and Don’ts

### Do:
- **Do** use whitespace as a separator. If you feel the urge to add a line, add 16px of space instead.
- **Do** use `primary_container` (#e2dfff) for subtle highlights in AI-generated text to signify "machine-learning" origins.
- **Do** stick to the 220px sidebar width strictly to maintain the "Linear-esque" slim profile.

### Don’t:
- **Don’t** use pure black (#000000). Always use `on_surface` (#2b3437) for text to keep the "Soft Professional" vibe.
- **Don’t** use `xl` (0.75rem) border radius for everything. Keep it to `md` (0.375rem) for a more precise, engineered feel.
- **Don’t** use heavy drop shadows. If it looks like it's "popping" off the screen, the shadow is too dark. It should feel like it's "resting" on the screen.