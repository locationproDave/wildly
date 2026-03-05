# PetPulse Sourcing Agent - Product Requirements Document

## Original Problem Statement
Build a specialist product sourcing agent for a premium pet wellness dropshipping business. The app helps identify winning products that meet strict sourcing quality standards with AI-powered analysis using Claude Opus 4.6.

## User Personas
1. **Dropshipping Entrepreneurs** - Looking to source premium pet wellness products
2. **Pet Product Store Owners** - Need verified supplier analysis and margin calculations
3. **E-commerce Business Owners** - Seeking trending pet wellness items with good ROI

## Core Requirements (Static)
- AI-powered product research with Claude Opus 4.6
- Product evaluation scoring (7 criteria: demand signal, emotional hook, visual appeal, supplier reliability, margin math, return risk, repeat purchase potential)
- Supplier verification from CJdropshipping, Zendrop, Spocket
- Product recommendation pipeline with RECOMMEND/INVESTIGATE/SKIP verdicts
- User authentication with signup discount codes (15% off first month)
- Search history and saved product evaluations

## What's Been Implemented (March 5, 2026)

### Backend (FastAPI + MongoDB)
- [x] User authentication (JWT-based) with registration and login
- [x] Discount code generation on signup (PETPULSEXXXXXXXX format)
- [x] Claude Opus 4.6 integration via emergentintegrations library
- [x] AI fallback system (Claude Opus → Claude Sonnet → GPT-5.2)
- [x] Chat sessions with conversation history
- [x] Product saving and management
- [x] Search history tracking
- [x] User statistics dashboard

### Frontend (React + Tailwind + Shadcn UI)
- [x] Landing page with hero, stats, features sections
- [x] Research page with AI chat interface
- [x] Pipeline page for saved products (protected route)
- [x] History page for search queries (protected route)
- [x] Authentication modal with login/register toggle
- [x] Responsive navigation with user menu
- [x] Warm, friendly design ("Scientific Naturalist" theme)

### Design System
- Primary: Deep Forest Green (#2F3E32)
- Secondary: Terracotta (#D4A373)
- Background: Warm Cream (#FDFCF8)
- Typography: Fraunces (headings) + Manrope (body)

## Known Issues
- **EMERGENT LLM Key Budget**: May need balance top-up for continued AI usage
- Error message added to guide users to Profile → Universal Key → Add Balance

## Prioritized Backlog

### P0 (Critical)
- None currently

### P1 (High Priority)
- [ ] **Supplier Due Diligence Agent** - 5-step verification system:
  - Supplier reliability check (rating, order volume, processing time, US warehouse)
  - Product safety check (CPSC recalls, FDA, Amazon reviews, Reddit complaints)
  - Claims compliance (medical claims, certifications, COA for CBD)
  - Shipping & customs risk assessment
  - Brand conflict/trademark check
- [ ] Web scraping integration for real-time supplier verification
- [ ] Product image previews in pipeline
- [ ] Export products to CSV

### P2 (Medium Priority)
- [ ] Email notifications for saved products
- [ ] Team collaboration features
- [ ] Supplier comparison tool

## Next Tasks
1. Add balance to Universal Key for continued AI functionality
2. Implement real-time supplier verification from CJdropshipping/Zendrop APIs
3. Add product image previews and supplier links
4. Consider Redis caching for improved performance

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Shadcn UI, React Router
- **Backend**: FastAPI, Motor (async MongoDB), JWT auth
- **AI**: Claude Opus 4.6 via emergentintegrations
- **Database**: MongoDB
