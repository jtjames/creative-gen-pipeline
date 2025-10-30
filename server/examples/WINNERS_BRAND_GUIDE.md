# Winners Sports Brand - Campaign Brief Guide

## Brand Overview

**Winners** is a North American sports brand focused on high-performance athletic gear and apparel. The brand embodies power, speed, and championship-level performance.

## Brand Identity

### Logo
- **Symbol**: Lightning bolt (⚡)
- **Style**: Bold, angular, dynamic
- **Colors**: Black primary
- **File**: `examples/assets/winners.png`

### Brand Values
- **Power**: Unleashing athletic potential
- **Performance**: Elite-level quality
- **Victory**: Championship mentality
- **Energy**: Dynamic and unstoppable

## Campaign: Spring Performance 2025

### Overview
**Campaign ID**: `winners-spring-performance-2025`

A seasonal campaign targeting North American athletes and fitness enthusiasts, promoting Winners' new line of performance gear for spring training season.

### Target Market

**Geographic Focus**: North America
- United States
- Canada
- Mexico

**Demographics**:
- Age: 18-45 years old
- Active lifestyle, fitness-focused
- Amateur to professional athletes
- Urban and suburban markets

**Psychographics**:
- Performance-driven
- Quality-conscious
- Brand-aware
- Social media active
- Competitive mindset

### Products Featured

#### 1. Bolt Runner Pro - Performance Running Shoes
**Product ID**: `bolt-runner-pro`

**Key Features**:
- Carbon fiber performance plate
- Advanced cushioning system
- Lightning bolt logo design
- Black and electric blue colorway
- Professional athlete-endorsed

**Price Point**: Premium ($150-200)

**Image Direction**:
- Dynamic action shot on professional track
- Runner in mid-stride, motion blur for speed
- Dramatic lighting, high contrast
- Focus on shoe technology and Winners logo

#### 2. Lightning Compression Athletic Wear
**Product ID**: `lightning-compression`

**Key Features**:
- Moisture-wicking performance fabric
- Compression technology for muscle support
- Lightning bolt accent design
- Form-fitting athletic cut
- Temperature-regulating

**Price Point**: Mid-premium ($80-120)

**Image Direction**:
- Athlete during intense workout
- Gym or training facility setting
- Show fabric detail and fit
- Energy and movement
- Winners logo prominent on chest

#### 3. Power Training Performance Bag
**Product ID**: `power-training-gear`

**Key Features**:
- Durable water-resistant material
- Multiple compartments for gear organization
- Embossed lightning bolt logo
- Shoe compartment with ventilation
- Laptop sleeve for gym-to-work lifestyle

**Price Point**: Mid-range ($90-130)

**Image Direction**:
- Professional product photography
- Locker room or gym environment
- Show quality materials and construction
- Training equipment visible (aspirational)
- Premium sports bag aesthetic

## Messaging Strategy

### Headline Themes
- **Power**: "Unleash Your Power"
- **Performance**: "Built for Champions"
- **Victory**: "Train Like a Winner"
- **Spring Focus**: Seasonal training, new goals

### Call-to-Action Strategy
- **Direct**: "Shop Performance", "Shop Now"
- **Urgency**: Spring limited edition
- **Value**: Championship-level gear

### Localization Notes

**en-US (United States)**:
- Focus on performance and competitive edge
- Reference professional sports culture
- Emphasize individual achievement

**en-CA (Canada)**:
- Balance performance with accessibility
- Hockey and winter sports crossover appeal
- Community and team spirit

**es-MX (Mexico)**:
- Passionate, energetic messaging
- Soccer/football cultural references
- Family and community fitness focus

## Creative Direction

### Visual Style
- **Photography**: High-energy action shots
- **Color Palette**:
  - Primary: Black (#000000)
  - Accent: Electric Blue (#0080FF)
  - Supporting: Charcoal Gray, White
- **Typography**: Bold, athletic, modern
- **Mood**: Powerful, dynamic, victorious

### Composition Guidelines
- Dynamic angles and perspectives
- Motion blur for speed/energy
- High contrast lighting
- Clean, uncluttered backgrounds
- Product and logo clearly visible

### Asset Requirements
- **Formats**: JPEG, PNG
- **Sizes**: High resolution (1200x1200px minimum)
- **Aspect Ratios**: 1:1 (Instagram), 9:16 (Stories), 16:9 (Display)

## Brand Assets

### Logo Placement
- **File**: `/brandlib/winners/winners.png`
- **Usage**: Always maintain clear space around logo
- **Minimum Size**: 40px height for digital
- **Acceptable Backgrounds**: Light colors, ensure contrast

### Color Usage
- **Primary Black**: Use for backgrounds, text, logo
- **Electric Blue Accent**: Use sparingly for energy/highlights
- **White**: Use for contrast and breathing room

## Campaign Channels

### Primary Channels
1. **Instagram** (1:1, 9:16 Stories)
2. **Facebook** (1:1, 16:9)
3. **YouTube** (16:9 pre-roll)
4. **Digital Display** (16:9 banner ads)
5. **Email Marketing** (responsive layouts)

### Secondary Channels
- TikTok (9:16)
- Twitter/X (16:9)
- Pinterest (1:1, vertical)
- In-store digital displays

## Success Metrics

### KPIs
- Click-through rate (CTR)
- Conversion rate
- Engagement rate (likes, shares, comments)
- Brand awareness lift
- Revenue per product

### Target Performance
- CTR: 3-5% (above industry average)
- Conversion: 8-12%
- ROAS: 4:1 minimum

## Technical Specifications

### Brief Upload
- **Format**: JSON
- **Image Requirements**:
  - Max 10MB per image
  - JPEG, PNG, or WEBP
  - High resolution recommended

### Template
- **Version**: `bottom-cta@1.3.0`
- **Elements**: Headline, CTA button, logo, product image
- **Safe Zones**: Maintain margins for mobile viewing

## Usage Instructions

### Upload via Web Form

1. Navigate to `http://localhost:1854/upload-brief.html`
2. Fill in campaign details from this brief
3. Upload product images:
   - `bolt-runner-pro.jpg`
   - `lightning-compression.jpg`
   - `power-training-gear.jpg`
4. Verify all locales and products are complete
5. Submit and track via briefs dashboard

### Upload via API

```bash
curl -X POST http://localhost:1854/briefs \
  -F "brief_json=@examples/winners-spring-performance-brief.json" \
  -F "product_images=@examples/assets/bolt-runner-pro.jpg" \
  -F "product_images=@examples/assets/lightning-compression.jpg" \
  -F "product_images=@examples/assets/power-training-gear.jpg"
```

### Upload via Python Script

```python
python examples/upload_winners_brief.py
```

## Notes

- Ensure all product images emphasize Winners lightning bolt logo
- Maintain consistent black/blue color scheme across all assets
- Focus on action, movement, and energy in all creative
- Test creatives across all aspect ratios for optimal display
- Monitor performance and adjust messaging per locale

## Contact

For questions about this campaign brief or Winners brand guidelines, contact the creative team.

---

**Campaign**: Winners Spring Performance 2025
**Version**: 1.0
**Date**: October 2025
**Brand**: Winners Sports
