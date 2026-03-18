Generate an HTML page following TrendAI™ Brand Guidelines.

## Brand Guidelines Summary

### Colors
- **Primary**: TrendAI™ Red `#D71920`, Black `#000000`, White `#FFFFFF`
- **Secondary**: Amber `#FF9500`, Signal `#2E0FE4`
- **Default mode**: Dark (black background). Light mode for text-heavy/long-form content.

### Color ratios (dark mode example)
- 50% Black + 40% Red + 10% Amber
- Or: 60% Black + 30% Red + 10% Accent

### Typography
- **Headlines**: Gotham Bold (fallback: `'Gotham', 'Aptos', Arial, sans-serif`)
- **Body**: Work Sans Regular (fallback: `'Work Sans', 'Aptos', Arial, sans-serif`)
- **Product UI dashboards**: Inter
- Load from Google Fonts: Work Sans, Inter

### Typography rules
- Headlines: bold, 2–3 lines max, sentence case (not ALL CAPS)
- Body: sentence case, left-aligned (80% of content)
- Center-align only for intro/hero copy
- No justified or right-aligned text
- Gradient on headlines (key word/phrase only, dark background only): left-to-right, `#D71920` at 0%–40%, `#FF9500` at 100%
  ```css
  background: linear-gradient(90deg, #D71920 0%, #D71920 40%, #FF9500 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  ```

### ADA / WCAG 2.1 AA compliance
- White text on Black ✓
- White text on Red ✓ (only bold 18.66px+ or regular 24px+)
- White text on Signal ✓
- Amber text on Black ✓
- Amber text on Signal ✓
- Do NOT use unapproved color combinations

### Layout & style
- Clean, minimal, modern
- Prefer dark backgrounds for heroes/banners
- Light backgrounds for long-form/text-heavy sections
- Brand line: **"AI Fearlessly"**

---

## Task

The user wants to generate an HTML page. Their request:

$ARGUMENTS

Generate a complete, self-contained HTML page:
- Use `<style>` block with Google Fonts import for Work Sans and Inter
- Gotham fallback in font-family stack
- Follow dark/light mode guidance based on content type
- Apply brand colors, typography rules, and ADA-compliant color combinations
- Include gradient headline if appropriate
- Output only the HTML, no explanation
