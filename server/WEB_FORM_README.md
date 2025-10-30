# Campaign Brief Web Form

## Overview

A complete web-based interface for uploading campaign briefs with product images. The form provides an intuitive, user-friendly way to create campaign briefs without needing to manually construct JSON or use command-line tools.

## Features

### Upload Form (`/upload-brief.html`)

**Key Features:**
- ✅ Dynamic product management (add/remove products)
- ✅ Automatic locale field generation
- ✅ Real-time image preview
- ✅ File size validation (10MB max)
- ✅ Form validation with helpful error messages
- ✅ Color picker for brand identity
- ✅ Responsive design
- ✅ Beautiful gradient UI

**Form Sections:**

1. **Campaign Details**
   - Campaign ID (unique identifier)
   - Target Region
   - Target Audience
   - Template Version
   - Aspect Ratios (checkboxes for 1:1, 9:16, 16:9)

2. **Locales & Messaging**
   - Dynamic locale input (comma-separated)
   - Auto-generates message and CTA fields for each locale
   - Supports multiple languages

3. **Products**
   - Add/remove products dynamically
   - Minimum 2 products required
   - Each product includes:
     - Product ID
     - Product Name
     - Generation Prompt
     - Negative Prompt (optional)
     - Product Image (required)
   - Real-time image preview
   - File size validation

4. **Brand Identity**
   - Color picker with hex input
   - Logo path in brand library
   - Real-time color preview

### Briefs List (`/briefs.html`)

**Key Features:**
- ✅ Grid view of all campaign briefs
- ✅ Status badges (pending, processing, completed, failed)
- ✅ Click to view full brief details
- ✅ Auto-refresh every 30 seconds
- ✅ Modal popup for detailed view
- ✅ JSON viewer
- ✅ Empty state for new users

**Brief Cards Show:**
- Campaign ID
- Status badge
- Target region
- Product count
- Locale count
- Target audience
- Upload timestamp

**Detail Modal Shows:**
- Complete campaign details
- Brand identity
- All localized messages
- Product details with image paths
- Raw JSON for debugging

## Setup

The web form is automatically served by the FastAPI application.

### File Structure
```
server/
├── static/
│   ├── upload-brief.html    # Upload form
│   └── briefs.html          # List view
└── src/
    └── app.py               # Serves static files
```

### Starting the Server

```bash
cd creative-gen-pipeline/server
source .venv/bin/activate
make run
```

The server starts on `http://localhost:1854`

## URLs

- **Upload Form**: http://localhost:1854/upload-brief.html
- **Briefs List**: http://localhost:1854/briefs.html
- **Root**: http://localhost:1854/ (redirects to upload form)

## Using the Upload Form

### Step 1: Fill Campaign Details

1. Enter a unique **Campaign ID** (e.g., `summer-2025-promo`)
2. Specify **Target Region** (e.g., `North America`)
3. Enter **Target Audience** description
4. Set **Template Version** (format: `name@1.0.0`)
5. Select **Aspect Ratios** (at least one required)

### Step 2: Configure Locales

1. Enter locale codes separated by commas: `en-US, es-MX, fr-CA`
2. Click **"Generate Locale Fields"**
3. Fill in message and CTA for each locale

Example:
- **en-US Message**: "Summer savings are here!"
- **en-US CTA**: "Shop Now"
- **es-MX Message**: "¡Llegaron los ahorros de verano!"
- **es-MX CTA**: "Comprar Ahora"

### Step 3: Add Products

The form starts with 2 products. You can add more or remove extras.

For each product:
1. Enter **Product ID** (must match image filename)
2. Enter **Product Name**
3. Write **Generation Prompt** (describe desired image)
4. Optionally add **Negative Prompt** (what to avoid)
5. **Upload Product Image**:
   - Click "Choose Image"
   - Select JPEG, PNG, or WEBP file
   - Max 10MB
   - Preview appears automatically

**Important**: The image filename (without extension) should match the Product ID.
- Product ID: `wh-9000` → Image: `wh-9000.jpg` ✅
- Product ID: `wh-9000` → Image: `headphones.jpg` ⚠️ (will still work but renamed)

### Step 4: Set Brand Identity

1. Use color picker or enter hex code for **Primary Brand Color**
2. Enter **Logo Path** in brand library (e.g., `/brandlib/acme/logo.png`)

### Step 5: Submit

1. Click **"Upload Campaign Brief"**
2. Wait for upload to complete
3. Success message appears with campaign ID
4. Automatically redirects to briefs list

## Viewing Briefs

Navigate to http://localhost:1854/briefs.html

**Grid View:**
- All briefs displayed as cards
- Color-coded status badges
- Click any card to view details

**Detail View:**
- Click a brief card
- Modal opens with complete details
- Shows all products, locales, and settings
- Includes raw JSON for API reference

## Validation

The form validates:

- ✅ Required fields are filled
- ✅ At least one aspect ratio selected
- ✅ At least 2 products added
- ✅ All products have images
- ✅ Image files under 10MB
- ✅ Template follows semver pattern (`name@x.y.z`)
- ✅ Brand color is valid hex (`#RRGGBB`)
- ✅ All locales have message and CTA translations

## Error Messages

**Common Errors:**

| Error | Cause | Solution |
|-------|-------|----------|
| "Please select at least one aspect ratio" | No ratios checked | Check at least one ratio |
| "Please generate locale fields first" | Locales not generated | Click "Generate Locale Fields" |
| "Product X is missing an image" | Image not uploaded | Upload image for that product |
| "Minimum 2 products required" | Less than 2 products | Add more products |
| "Image must be less than 10MB" | File too large | Compress or resize image |

## Technical Details

### Form Submission

The form uses `multipart/form-data` encoding:

```javascript
FormData structure:
- brief_json: JSON string with campaign data
- product_images: File (one per product)
- product_images: File (one per product)
- ...
```

### API Integration

**Endpoint**: `POST /briefs`

**Process:**
1. Form collects all data
2. Builds JSON brief object
3. Creates FormData with brief_json + images
4. POSTs to `/briefs` endpoint
5. Displays success/error message
6. Redirects to briefs list on success

### Browser Support

Tested on:
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

### Responsive Design

- Desktop: Full form layout
- Tablet: Adjusted grid columns
- Mobile: Stacked layout (works but better on desktop)

## Customization

### Colors

Main gradient in both pages:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

To change, edit the CSS in the `<style>` section of each HTML file.

### Default Values

Edit in `upload-brief.html`:

```javascript
// Default brand color
value="#FF5733"

// Default template
placeholder="e.g., bottom-cta@1.3.0"
```

## Screenshots

### Upload Form
- Clean, modern interface
- Purple gradient header
- White content cards
- Dynamic product cards
- Image previews
- Color picker

### Briefs List
- Grid of brief cards
- Status badges
- Hover effects
- Modal detail view
- JSON viewer

## Development

### Adding Features

**Add a new field to the form:**

1. Add HTML input in `upload-brief.html`:
```html
<div class="form-group">
    <label>New Field</label>
    <input type="text" id="newField">
</div>
```

2. Update form submission in JavaScript:
```javascript
const brief = {
    // ... existing fields
    new_field: document.getElementById('newField').value
};
```

3. Update the model in `src/models.py` to accept the new field

### Styling

Both pages use inline CSS for simplicity. Key classes:

- `.form-group` - Form field wrapper
- `.product-card` - Product section
- `.btn-primary` - Purple gradient button
- `.status-badge` - Colored status indicator
- `.modal` - Popup detail view

## Troubleshooting

**Form doesn't submit:**
- Check browser console for errors
- Verify all required fields are filled
- Ensure images are selected for all products

**Images not uploading:**
- Check file size (must be < 10MB)
- Verify file format (JPEG, PNG, WEBP only)
- Check network tab for upload progress

**Briefs list is empty:**
- Verify server is running
- Check `/briefs` API endpoint works
- Look for errors in browser console

**Modal won't close:**
- Click outside the modal
- Click the × button
- Press ESC key (if implemented)

## Next Steps

**Potential Enhancements:**

1. **File Upload via Drag & Drop**
   - Drag images directly onto product cards
   - Visual drop zones

2. **Template Selector**
   - Dropdown with available templates
   - Preview template layouts

3. **JSON Import/Export**
   - Upload existing brief JSON
   - Export form data as JSON

4. **Image Cropping**
   - Built-in image editor
   - Crop to recommended dimensions

5. **Progress Tracking**
   - Upload progress bars
   - Multi-step wizard

6. **Favorites & History**
   - Save form drafts
   - Reuse previous briefs

## Files

1. **`static/upload-brief.html`** (650+ lines)
   - Complete upload form
   - JavaScript for dynamic behavior
   - Inline CSS styling

2. **`static/briefs.html`** (450+ lines)
   - Briefs list view
   - Detail modal
   - Auto-refresh functionality

3. **`src/app.py`** (modified)
   - Static file serving
   - Route handlers for HTML pages

## Summary

The web form provides a **production-ready interface** for uploading campaign briefs with product images. It handles all validation, provides excellent UX feedback, and integrates seamlessly with the FastAPI backend.

**Quick Start:**
```bash
make run
# Navigate to http://localhost:1854/upload-brief.html
```
