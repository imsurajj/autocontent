# Doclume: Bulk Markdown PDF Workstation

## Overview

A local-first desktop application that allows teams to generate bulk PDFs from Markdown content templates and dynamic titles.

The app is designed for companies, content teams, SEO agencies, marketing teams, ebook creators, and AI content workflows that need fast and scalable PDF generation without heavy cloud infrastructure costs.

---

# Core Workflow

## Input

### 1. Markdown Content
User provides a Markdown template.

Example:

```md
# {{title}}

Welcome to this guide 🚀

This document is generated automatically using the desktop app.

## Features
- Fast
- Bulk PDF generation
- Emoji support 😄
```

---

### 2. List of Titles

Example:

```txt
AI Marketing Guide
Next.js Mastery
Startup Growth Handbook
```

---

# Output

The app automatically generates:

```txt
AI Marketing Guide.pdf
Next.js Mastery.pdf
Startup Growth Handbook.pdf
```

Each PDF uses:
- same Markdown structure
- dynamic title replacement
- same styling/template

---

# Main Features

## Bulk PDF Generation
Generate hundreds or thousands of PDFs in one click.

---

## Markdown Support
Users can write content using Markdown syntax.

Supports:
- headings
- lists
- tables
- code blocks
- quotes
- links
- formatting

---

## Emoji Support
Supports emojis properly inside PDFs.

Examples:

```txt
🚀 🔥 📄 😄 ✨
```

---

## Live Preview
Users can preview rendered content before exporting PDFs.

---

## Local PDF Generation
PDFs are generated directly on the user's system.

Benefits:
- faster generation
- no cloud storage costs
- better privacy
- offline support

---

## OTA (Over-The-Air) Updates
Users receive update notifications automatically inside the app.

Example:

```txt
Update Available → Download → Restart App
```

---

## License-Based Access
Companies purchase licenses for team usage.

Example:
- 20 seats
- monthly subscription
- managed via backend verification

---

# Why Local-First Architecture

The app intentionally avoids cloud PDF storage.

Reason:
- PDFs consume huge storage
- daily generation volume can become massive
- cloud storage becomes expensive quickly

Instead:

```txt
Generate → Save Locally → Done
```

This keeps:
- infrastructure cost low
- performance high
- scaling easier

---

# Recommended Tech Stack

# Frontend

## Next.js

Why:
- modern React ecosystem
- easy routing
- scalable architecture
- strong TypeScript support
- excellent developer experience

Use Cases:
- app UI
- settings pages
- dashboard
- templates
- preview system

---

## Tailwind CSS

Why:
- fast UI development
- consistent design system
- responsive layouts
- easy customization

Use Cases:
- styling
- layout
- dark/light themes

---

## ShadCN UI

Why:
- modern component system
- accessible UI
- customizable
- production-ready components

Use Cases:
- dialogs
- buttons
- forms
- sidebar
- tables

---

# Desktop Layer

## Tauri

Why:
- lightweight desktop app
- lower RAM usage than Electron
- smaller installer size
- native performance
- better Windows compatibility

Use Cases:
- desktop packaging
- local filesystem access
- installers
- OTA updates

---

# Markdown Rendering

## react-markdown

Why:
- reliable Markdown rendering
- React ecosystem support
- extensible

Use Cases:
- preview rendering
- content formatting

---

# PDF Generation

## Puppeteer

Why:
- browser-quality PDF rendering
- excellent emoji support
- accurate typography
- CSS support
- proper page breaks

Use Cases:
- Markdown → HTML → PDF conversion
- bulk PDF export

---

# Emoji Rendering

## Native Browser Rendering / Twemoji

Why:
- proper Unicode rendering
- consistent emoji appearance

Use Cases:
- emojis inside generated PDFs

---

# Backend

## Appwrite

Why:
- authentication
- database
- storage
- lightweight backend infrastructure
- easy setup

Use Cases:
- license verification
- user authentication
- OTA update metadata
- storing update files

---

# Hosting

## Vercel

Why:
- easy deployment
- fast global CDN
- ideal for frontend hosting

Use Cases:
- download page
- changelog
- update metadata APIs
- landing page

---

# File Storage Strategy

## Local Storage on User Device

Why:
- avoids expensive cloud storage
- faster generation
- privacy-friendly
- scalable

Stored Locally:
- PDFs
- exports
- generated documents

---

# OTA Update System

## Update Flow

```txt
Developer pushes new release
↓
App checks latest version
↓
User receives update notification
↓
Update downloads automatically
↓
Restart app
```

---

# License System

## Simple Seat-Based Licensing

Example:

```txt
20 licenses
₹2000/month
```

Verification handled via backend API.

---

# Future Expansion Features

## CSV Variable Injection

Example:

```csv
title,author
AI Guide,Suraj
Next.js Guide,John
```

Dynamic placeholders:

```md
# {{title}}

Written by {{author}}
```

---

## ZIP Export
Export all generated PDFs as a ZIP file.

---

## AI Content Integration
Future AI integrations:
- AI document generation
- summaries
- rewriting
- formatting assistance

---

# Architecture Overview

```txt
Next.js Frontend
        ↓
Tauri Desktop App
        ↓
Local PDF Generation
        ↓
Local File Storage

Appwrite Backend
├── Auth
├── License Verification
└── OTA Updates

Vercel
├── Landing Page
├── Download Portal
└── Changelog
```

---

# Benefits of This Architecture

## Low Infrastructure Cost
Most processing happens locally.

---

## Scalable
Cloud costs remain minimal even with massive PDF generation.

---

## Better Performance
No need to upload/store generated PDFs.

---

## Professional User Experience
- desktop app
- OTA updates
- modern UI
- fast exports

---

# Target Users

- SEO agencies
- AI content teams
- ebook creators
- marketing agencies
- internal business teams
- automation workflows
- content production teams

---

# Business Model

## SaaS Licensing

Example:

```txt
₹2000/month
20 team licenses
```

Low server costs allow high profit margins.

---

# Packaging, Security & Distribution

# Desktop App Packaging

## MSI Installer Generation

The desktop application will be distributed using an MSI installer package.

Why MSI:
- native Windows installer format
- cleaner installation experience
- easier updates
- more trusted by Windows than raw EXE files
- supports uninstall functionality
- professional deployment workflow

The MSI installer will:
- install the desktop application
- create desktop/start menu shortcuts
- manage updates
- support app versioning

---

# Recommended Packaging System

## Tauri Bundler

Tauri provides built-in packaging support for:

- `.msi`
- `.exe`
- macOS bundles
- Linux packages

Why Tauri Packaging:
- smaller app size
- lower false positives
- cleaner installers
- better Windows compatibility

---

# OTA (Over-The-Air) Updates

The application supports automatic updates.

## Update Flow

```txt
Developer publishes new release
↓
App checks latest version
↓
User sees update notification
↓
Download update
↓
Restart application
```

Benefits:
- users always stay updated
- bug fixes deploy quickly
- no manual reinstall process
- smoother company-wide rollout

---

# Update Hosting

Update files can be hosted using:
- Appwrite Storage
- GitHub Releases
- Cloudflare R2

The desktop app checks update metadata automatically.

---

# Security & Trust

# Windows SmartScreen Warning

During early-stage/internal distribution, Windows may show:

```txt
Windows protected your PC
```

Reason:
- application is unsigned
- Microsoft SmartScreen does not yet recognize the publisher

This is common for:
- internal company tools
- startup software
- indie desktop apps

The application itself is still safe if distributed internally through official company channels.

---

# Why We Avoid Paid Code Signing Initially

Code signing certificates:
- are expensive
- unnecessary for small internal teams initially
- mainly required for public mass distribution

Current focus:
- product functionality
- internal deployment
- low operational cost

Future upgrade path:
- purchase code-signing certificate when scaling publicly

---

# Security Measures Implemented

## Local-First Processing

PDF generation happens locally on the user's machine.

Benefits:
- no sensitive files uploaded
- better privacy
- lower security risk
- faster processing

---

## Minimal Backend Storage

Backend stores only:
- authentication data
- license information
- update metadata

Generated PDFs are NOT stored in cloud infrastructure.

---

# SSL Certificate Handling (certifi)

## Why certifi Is Used

Some packaged Python applications can fail HTTPS requests on certain Windows systems because of outdated or missing certificate stores.

To avoid SSL verification issues, the application uses:

## certifi

Purpose:
- provides updated trusted SSL certificates
- ensures secure HTTPS communication
- improves compatibility across Windows versions

---

# certifi Benefits

Benefits:
- secure API requests
- proper SSL verification
- avoids HTTPS failures on Windows 10
- improves reliability for license verification APIs

---

# Example Use Cases for certifi

Used for:
- authentication requests
- license validation
- update metadata requests
- secure backend communication

---

# Why This Matters

Without proper SSL handling:
- API calls may fail
- license verification may break
- updates may not work

Using certifi ensures:
- stable HTTPS requests
- safer encrypted communication
- better cross-system compatibility

---

# Recommended Security Flow

```txt
Desktop App
↓
HTTPS Request
↓
SSL Verification via certifi
↓
Secure Backend Communication
```

---

# Future Security Improvements

As the product scales:
- code signing certificate
- stronger update verification
- signed release channels
- enterprise deployment options

can be added later.

Current architecture prioritizes:
- simplicity
- low cost
- internal deployment
- operational stability

---