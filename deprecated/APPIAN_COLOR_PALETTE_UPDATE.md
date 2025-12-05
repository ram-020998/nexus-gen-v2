# Appian Color Palette Update - Light Theme

## Overview
Updated the NexusGen application's light theme to use the official Appian Solutions Design System color palette from: https://workshop.appiancloud.com/suite/sites/appian-solutions-design-system/group/branding/page/colors

## Changes Made

### 1. Color Variables Added
Added comprehensive Appian color variables to the light theme in `static/css/docflow.css`:

#### Branding Colors
- `--appian-blue: #2322F0`
- `--appian-navy: #020A50`
- `--appian-light-blue: #E7F1FF`
- `--appian-background: #FAFAFC`
- `--appian-white: #FFFFFF`

#### Gray Palette
- `--gray-0: #F5F5F7`
- `--gray-1: #EDEDF2`
- `--gray-2: #DCDCE5`
- `--gray-3: #6C6C75`
- `--gray-4: #2E2E35`
- `--black: #0F0F16`

#### Semantic Colors (4 shades each)
**Red:** `#FFE7E7`, `#FDADAD`, `#DE0037`, `#9F0019`
**Yellow:** `#FFF6C9`, `#FDEB93`, `#FFD948`, `#856C00`
**Green:** `#E3FBDF`, `#B2EAB1`, `#1CC101`, `#117C00`
**Blue:** `#E9EDFC`, `#AFBFF8`, `#2322F0`, `#08088D`
**Orange:** `#FFEED3`, `#FFDCA3`, `#FAA92F`, `#995C00`
**Purple:** `#F2E9FF`, `#D9AEFF`, `#B561FF`, `#790DA1`
**Teal:** `#E2FAF9`, `#A5E8E8`, `#56ADC0`, `#2C6770`
**Pink:** `#FFDEF3`, `#F7A7DA`, `#E21496`, `#8C1565`

### 2. Application Variables Updated
- `--bg-primary: #FAFAFC` (Appian Background)
- `--bg-secondary: #FFFFFF` (Appian White)
- `--text-primary: #0F0F16` (Black)
- `--text-secondary: #6C6C75` (Gray 3)
- `--border-color: #DCDCE5` (Gray 2)
- `--purple: #B561FF` (Purple 3)
- `--teal: #56ADC0` (Teal 3)
- `--pink: #E21496` (Pink 3)
- `--green: #1CC101` (Green 3)

### 3. Component Updates

#### Action Cards
- Updated all card gradients to use Appian colors
- Upload: Blue 3 → Purple 3
- Verify: Teal 3 → Teal 4
- Create: Purple 3 → Purple 4
- Chat: Pink 3 → Pink 4
- Convert: Orange 3 → Orange 4
- Analyzer: Green 3 → Green 4

#### Badges & Status Indicators
- Success badges: Green 1 background, Green 4 text
- Warning badges: Yellow 1 background, Yellow 4 text
- Error badges: Red 1 background, Red 4 text
- Info badges: Teal 1 background, Teal 4 text

#### Classification Badges
- No Conflict: Green palette
- Conflict: Red palette
- New: Teal palette
- Deleted: Yellow palette

#### Buttons
- Primary: Purple 3 → Purple 4 gradient
- Success: Green 3 → Green 4 gradient
- Warning: Orange 3 → Orange 4 gradient
- Danger: Red 3 → Red 4

#### Notifications & Toasts
- Updated border colors to use semantic color level 3
- Updated icon colors to match

#### Form Controls
- Background: Gray 0
- File selector buttons: Purple 1 background

### 4. Shadow & Hover Effects
- Updated box shadows to use Appian Blue with low opacity
- Hover effects use appropriate color palette shades

## Color Usage Guidelines (from Appian)

### Semantic Colors
Use sparingly and aligned with meaning:
- **Level 1:** Backgrounds
- **Level 2:** Borders or charts
- **Level 3:** Decorative components
- **Level 4:** Text

### Primary Colors
- Green, Red, Yellow, Blue: Use for success/fail indicators
- Secondary colors (Orange, Purple, Teal, Pink): Use when no semantic meaning needed

## Testing
Verified on:
- ✅ Dashboard page
- ✅ Merge Sessions page
- ✅ Settings page
- ✅ All action cards
- ✅ Buttons and badges
- ✅ Form controls

## Notes
- Dark theme remains unchanged (only light theme updated)
- All colors follow Appian Solutions Design System specifications
- Color variables are now centralized for easy maintenance
- Maintains accessibility and contrast ratios

## Files Modified
- `static/css/docflow.css` - Complete light theme color palette update

---
**Date:** December 2, 2025
**Reference:** Appian Solutions Design System - Colors
