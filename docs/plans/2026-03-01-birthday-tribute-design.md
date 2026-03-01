# Dad's 80th Birthday Tribute Site — Design Document

**Date**: 2026-03-01
**Domain**: dad.melvinit.com
**Timeline**: ~2 weeks
**Status**: Approved

## Overview

A nostalgic, vintage-themed tribute website for Dad's 80th birthday party. Features a curated photo/video gallery and a message wall where guests can leave birthday wishes. Built on the same Svelte + Python Lambda + AWS CDK stack as the dakamin portfolio site.

## Requirements

- **Gallery**: Admin-curated photos and videos, served from S3 via CloudFront
- **Message wall**: Guests can view and leave text birthday messages
- **Access control**: Party code for manual entry, or expiring UUID token as URL parameter
- **Admin page**: Upload media, manage access tokens
- **Aesthetic**: Nostalgic & vintage — sepia tones, film-grain textures, retro typography

## Architecture

```
dad.melvinit.com (Route53 A record)
    → CloudFront Distribution
        → Default: S3 Site Bucket (SvelteKit static build)
        → /api/*: API Gateway → Lambda
        → /media/*: S3 Media Bucket
```

### Stack

- **Frontend**: Svelte 5, SvelteKit 2, Tailwind CSS 4, TypeScript
- **Backend**: Python 3.13, AWS SAM, Lambda + API Gateway
- **Infrastructure**: AWS CDK 2 (TypeScript)
- **Database**: DynamoDB (single table, on-demand billing)
- **Storage**: S3 (media) + CloudFront (CDN)

## Data Model

Single DynamoDB table (`DadBirthdayTable`) with single-table design:

| Item Type    | PK      | SK               | Attributes                                         |
|--------------|---------|------------------|----------------------------------------------------|
| Message      | `MSG`   | `MSG#<ulid>`     | `author`, `text`, `createdAt`                      |
| AccessToken  | `TOKEN` | `TOKEN#<uuid>`   | `expiresAt` (TTL), `createdAt`, `label`            |
| Media        | `MEDIA` | `MEDIA#<ulid>`   | `s3Key`, `type` (photo/video), `caption`, `order`, `createdAt` |

- Messages sorted by ULID (time-ordered)
- AccessTokens use DynamoDB TTL — expired tokens auto-delete
- Party code stored as Lambda environment variable (not in DB)

## API Endpoints

All endpoints behind CloudFront `/api/*` path → API Gateway → Lambda.

### Public

| Method   | Path       | Description                                              |
|----------|------------|----------------------------------------------------------|
| `POST`   | `/verify`  | Validate party code or UUID token. Returns session cookie (signed JWT). |

### Guest (session required)

| Method   | Path        | Description                            |
|----------|-------------|----------------------------------------|
| `GET`    | `/media`    | List all media items with CloudFront URLs |
| `GET`    | `/messages` | List all birthday messages, newest first |
| `POST`   | `/messages` | Submit a birthday message (`author`, `text`) |

### Admin (admin session required)

| Method   | Path                    | Description                     |
|----------|-------------------------|---------------------------------|
| `GET`    | `/admin/tokens`         | List active UUID access tokens  |
| `POST`   | `/admin/tokens`         | Create token with expiration    |
| `DELETE` | `/admin/tokens/{uuid}`  | Revoke a token                  |
| `POST`   | `/admin/media/upload-url` | Get pre-signed S3 upload URL  |
| `POST`   | `/admin/media`          | Save media metadata after upload |
| `DELETE` | `/admin/media/{id}`     | Remove a media item             |
| `PUT`    | `/admin/media/{id}`     | Update caption or display order |

### Auth Flow

1. **Guest**: Enters party code or arrives via `?token=<uuid>`
2. `POST /verify` validates code/token → returns signed JWT as HttpOnly cookie
3. JWT contains `role` (guest or admin) — Lambda checks on each request
4. **Admin**: Separate admin code (env var) → `POST /verify` with admin flag → admin JWT
5. JWT signed with `JWT_SECRET` env var — no session store needed

## Frontend

### Routes

| Route       | Purpose                                              |
|-------------|------------------------------------------------------|
| `/`         | Gate page — party code input, auto-checks `?token=`  |
| `/gallery`  | Photo/video gallery with lightbox                     |
| `/messages` | Message wall + form to leave a message                |
| `/admin`    | Admin dashboard (upload media, manage tokens)         |

### Key Components

| Component         | Description                                                    |
|-------------------|----------------------------------------------------------------|
| `GatePage`        | Party code input, vintage aesthetic. Auto-verifies URL token.  |
| `Gallery`         | Grid/masonry of photos/videos. Sepia thumbnails. Click → lightbox. |
| `Lightbox`        | Full-screen overlay for single photo/video with caption.       |
| `VideoPlayer`     | Embedded player for S3-hosted videos.                          |
| `MessageWall`     | Scrollable birthday messages, styled like handwritten cards.   |
| `MessageForm`     | Name + message textarea.                                       |
| `AdminDashboard`  | Tabs: Upload Media, Manage Tokens. Drag-and-drop upload.      |
| `TokenManager`    | Create/revoke UUID tokens with date picker for expiration.     |

### Design System (Nostalgic & Vintage)

- **Colors**: Warm cream background (`#FFF8F0`), deep brown text (`#3E2723`), muted gold accents (`#C8A96E`)
- **Typography**: Playfair Display for headers, Caveat or Dancing Script for message cards
- **Textures**: Subtle paper/linen background, soft vignette on photos
- **Effects**: Sepia filter on gallery thumbnails, film-grain overlay, polaroid-style photo frames
- **Transitions**: Gentle fade-ins, no jarring animations
- **Mobile-first**: Responsive layout, touch-friendly gallery

### Navigation

- Shared nav bar after auth: Gallery | Messages
- Admin link visible only for admin sessions
- Mobile hamburger menu

## Infrastructure (CDK)

### Resources

1. **S3 Site Bucket** — SvelteKit static build (private, OAC)
2. **S3 Media Bucket** — photos/videos (private, OAC)
3. **CloudFront Distribution** — three behaviors:
   - Default → site bucket (SPA fallback: 404 → `/index.html`)
   - `/api/*` → API Gateway origin
   - `/media/*` → media bucket
4. **ACM Certificate** — `dad.melvinit.com` (us-east-1, DNS validation)
5. **Route53 A Record** — `dad.melvinit.com` → CloudFront
6. **DynamoDB Table** — single table, on-demand, TTL on `expiresAt`
7. **Lambda + API Gateway** — SAM-managed, environment variables:
   - `TABLE_NAME`, `MEDIA_BUCKET`, `PARTY_CODE`, `ADMIN_CODE`, `JWT_SECRET`

### CDK Stack Entry

```typescript
new BirthdayTributeSiteStack(app, 'DadBirthdayStack', {
  env: { account, region: 'us-east-1' },
  domainName: 'dad.melvinit.com',
  parentDomainName: 'melvinit.com',
  tags: { Project: 'DadBirthday', Environment: 'Production', ManagedBy: 'CDK' }
});
```

## CI/CD (GitHub Actions)

- **Trigger**: Push to `main`
- **Frontend job**: `npm run build` → upload to site S3 bucket → invalidate CloudFront
- **Backend job**: `sam build` → `sam deploy`
- **Auth**: OIDC (same as dakamin)
- **Secrets**: `DAD_S3_BUCKET_NAME`, `DAD_CLOUDFRONT_DISTRIBUTION_ID`, `AWS_IAM_ROLE_ARN`

## Scope Boundaries (YAGNI)

**In scope:**
- Curated gallery (admin uploads)
- Guest text messages
- Party code + expiring UUID access
- Admin dashboard (upload, tokens)
- Vintage design theme

**Out of scope (not building):**
- Guest photo/video uploads
- User accounts or registration
- Comments on individual photos
- Search functionality
- Analytics dashboard
- Email notifications
- Social sharing buttons
