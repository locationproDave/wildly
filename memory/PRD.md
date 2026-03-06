# Wildly Ones - Pet Wellness E-Commerce Platform

## Original Problem Statement
Build a pet wellness e-commerce store with:
1. Customer-facing storefront - Product browsing, shopping cart, Stripe/PayPal checkout
2. Admin dashboard with 7 AI agents built-in to help business owners manage operations
3. Full admin CRUD for products, orders, and promotions
4. Email automation for abandoned cart recovery and post-purchase engagement
5. Customer segmentation with AI-powered targeted campaigns

## User Personas
1. **Pet Parents (Customers)** - Shopping for premium pet wellness products
2. **Store Owners (Admins)** - Managing orders, products, and using AI agents for business operations

## Core Requirements (Static)
- E-commerce storefront with product catalog
- Shopping cart with Stripe + PayPal checkout
- Customer accounts with order history
- Admin dashboard with product/order/promotion management
- 7 specialized AI agents for business operations
- Pre-populated product catalog (45 products, 8 pet types)
- Email automation system
- Customer segmentation with targeted campaigns

## What's Been Implemented (March 6, 2026)

### Admin Dashboard & Management (7 Modules)
- [x] **Admin Analytics** (/admin/analytics)
  - Summary cards: Total Revenue, Orders, Customers, Avg Order Value
  - Sales Trend chart (last 7/14/30 days)
  - Top Products by revenue with images
  - Sales by Category and Pet Type breakdowns
  - Recent Customers list
- [x] **Admin Customer Segments** (/admin/segments) - NEW
  - AI-powered segmentation: VIP, Loyal, At-Risk, New, Dormant
  - Auto-classification based on purchase behavior
  - Campaign templates per segment (VIP20, LOYAL15, COMEBACK25, WELCOME10, WINBACK30)
  - View segment customers with revenue/order data
  - Create and send targeted email campaigns
- [x] **Admin Email Automation** (/admin/emails)
  - Abandoned Cart Recovery (Active) - COMEBACK10 discount
  - Post-Purchase Review Requests (Active) - 25 bonus points
  - Low Stock Alerts (Coming Soon)
- [x] **Admin Order Management** (/admin/orders)
  - View all orders with status filters
  - Update order status
  - Add tracking information
  - View detailed order info
- [x] **Admin Product Management** (/admin/products)
  - Full CRUD with search/filters
  - Add/Edit/Delete products via dialogs
- [x] **Admin Promotions** (/admin/promotions)
  - Create/manage promotion codes
- [x] **AI Agents** (/admin/agents)
  - 7 specialized agents for business operations

### E-Commerce Backend (FastAPI + MongoDB)
- [x] Product catalog with 45 products across 8 pet types
- [x] Shopping cart system with session-based storage
- [x] Stripe + PayPal checkout integration
- [x] Order management with tracking
- [x] User authentication (JWT)
- [x] Email automation endpoints
- [x] Customer segmentation with campaign system

### Customer Features
- [x] Homepage with hero, best sellers, new arrivals
- [x] Product browsing with filters
- [x] Customer reviews system
- [x] Shopping cart and checkout
- [x] Order history and tracking
- [x] Referral program ("Give $10, Get $10")
- [x] Loyalty program (Bronze/Silver/Gold/Platinum tiers)
- [x] Promo code support at checkout

### AI Agents (7 Specialized)
- [x] Product Sourcing Agent
- [x] Due Diligence Agent
- [x] Product Copywriter
- [x] SEO Blog Writer
- [x] Performance Marketing
- [x] Email Marketing
- [x] Customer Service

## Admin Credentials
- Email: admin@calmtails.com
- Password: admin123

## Key API Endpoints

### Customer Segmentation (NEW)
- `GET /api/admin/customer-segments` - Get all segments with stats
- `GET /api/admin/customer-segments/{segment}` - Get segment details
- `POST /api/admin/customer-segments/{segment}/campaign` - Generate campaign template
- `POST /api/admin/customer-segments/{segment}/send-campaign` - Send email campaign

### Email Automation
- `GET /api/admin/email-automation` - Get automation stats
- `POST /api/admin/email-automation/send-abandoned` - Trigger cart recovery emails
- `POST /api/admin/email-automation/send-reviews` - Trigger review requests

### Admin CRUD
- `GET/POST/PUT/DELETE /api/admin/products/*` - Product management
- `GET/PATCH /api/admin/orders/*` - Order management
- `GET/POST /api/admin/promotions` - Promotion management

## Prioritized Backlog

### P0 - Completed
- [x] Admin Product Management CRUD
- [x] Admin Order Management
- [x] Admin Analytics Dashboard
- [x] Email Automation (Abandoned Cart, Review Requests)
- [x] Brand rename to "Wildly Ones"
- [x] Customer Segmentation with Targeted Campaigns

### P1 - Next Priority
- [ ] Backend Refactoring - Split monolithic server.py into modules
- [ ] Blog section for SEO content
- [ ] Low Stock Alerts automation

### P2 - Medium Priority
- [ ] Real supplier API integration (CJdropshipping, Zendrop)
- [ ] Inventory management with alerts
- [ ] Customer support chat widget

### P3 - Future
- [ ] Wishlist functionality
- [ ] Product recommendations engine
- [ ] Multi-currency support
- [ ] Mobile app

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Shadcn UI, React Router
- **Backend**: FastAPI, Motor (async MongoDB), JWT auth
- **Payments**: Stripe, PayPal (sandbox)
- **Email**: Resend (MOCKED - requires API key)
- **Tracking**: 17Track (MOCKED - requires API key)
- **AI**: Claude Opus 4.6 via emergentintegrations
- **Database**: MongoDB

## Known Limitations / Mocked Services
- PayPal is in sandbox mode
- Email notifications require RESEND_API_KEY
- Order tracking requires TRACK17_API_KEY
- AI agents require EMERGENT LLM key balance
