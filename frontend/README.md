# DocMind AI — Frontend Architecture & Design System (Sprint 5.0)

Production-grade, modern AI SaaS frontend foundation built with **React**, **Vite**, **TypeScript**, **TailwindCSS**, **Framer Motion**, and **React Query**.

---

## 🎨 Color Palette & Design System

The application strictly enforces the DocMind AI color palette:

| Token | Hex Code | Purpose |
| :--- | :--- | :--- |
| **Jet Black** | `#0A0A0A` | Deep, dark backdrop & canvas surfaces (`bg-jet-900`) |
| **Cerulean Blue** | `#007BA7` | Primary AI actions, glowing borders, active navigation, confidence indicators |
| **Neon Rose** | `#FF2D95` | Secondary highlights, Cross-Encoder reranker badges, alerts, active tags |

### Glassmorphism Tokens (`src/styles/globals.css`)
- **`.glass-panel`**: `rgba(14, 14, 18, 0.72)` backdrop with `blur(16px)` and subtle `1px solid rgba(255, 255, 255, 0.07)` border.
- **`.glass-card`**: Dynamic hover cards with Cerulean / Neon Rose illumination rings.
- **`.glass-input`**: Sleek dark inputs with glow focus rings and inner illumination.
- **Ambient Canvas**: Multi-point subtle radial gradients and microscopic grid background.

---

## 🏗️ Folder Architecture

```
frontend/
├── src/
│   ├── assets/              # Static SVG emblems and branding
│   ├── components/
│   │   └── common/          # Reusable design system primitives
│   │       ├── Button.tsx       # Cerulean, Rose, Glass, Ghost variants + loading spinner
│   │       ├── Card.tsx         # Glassmorphic card containers with glow edges
│   │       ├── Badge.tsx        # Pill tags with micro pulse dots
│   │       ├── Input.tsx        # Input fields with validation & icons
│   │       ├── Modal.tsx        # Framer Motion animated modal dialogues
│   │       ├── Skeleton.tsx     # Dark shimmering loading states
│   │       ├── StatusPill.tsx   # Live backend connectivity monitor
│   │       └── ErrorBoundary.tsx# Fallback card with reload action
│   ├── context/
│   │   └── ToastContext.tsx # Context & animated toast notification container
│   ├── hooks/
│   │   ├── useHealth.ts     # React Query polling hook for /api/v1/health
│   │   └── useToast.ts      # Toast notification hook
│   ├── layout/
│   │   ├── Sidebar.tsx      # Collapsible navigation with brand emblem & active route indicator
│   │   ├── Navbar.tsx       # Search bar, breadcrumbs, live StatusPill, quick actions
│   │   └── AppLayout.tsx    # Responsive desktop shell with Framer Motion transitions
│   ├── pages/
│   │   ├── DashboardPage.tsx# Metric summary cards, quick actions, recent query list
│   │   ├── ChatPage.tsx     # Conversational RAG thread, floating input, source drawer
│   │   ├── DocumentsPage.tsx# Dropzone upload header & metadata catalog table
│   │   ├── AnalyticsPage.tsx# Latency breakdown, confidence tier distribution
│   │   └── SettingsPage.tsx # Model temperature, memory window, RAG parameters
│   ├── services/
│   │   ├── apiClient.ts     # Axios instance with interceptors & base URL
│   │   ├── healthService.ts # GET /health integration
│   │   ├── documentService.ts # GET /documents, POST /upload, DELETE /documents/{id}
│   │   └── chatService.ts   # POST /chat, GET /chat/history/{sessionId}
│   ├── styles/
│   │   └── globals.css      # Design system CSS tokens, glassmorphism, scrollbars
│   ├── types/               # TypeScript interfaces matching backend contracts
│   ├── App.tsx              # QueryClientProvider, ToastProvider, Router & code-split routes
│   └── main.tsx             # Application bootstrap & entrypoint
├── tailwind.config.js       # Custom colors, shadows, and animations
├── tsconfig.app.json        # TypeScript configuration with @/* path aliases
└── vite.config.ts           # Vite bundler configuration with dev server API proxy
```

---

## ⚡ API Layer & React Query Integration

- **Live Status Monitoring**: The `useHealth` hook polls `/api/v1/health` every 15 seconds. If the backend is active, `StatusPill` pulses with Cerulean illumination (`Backend Ready v1.0.0`). If unreachable, an alert badge offers a one-click retry.
- **Axios Interceptors**: Automatically unwraps backend error payloads (`detail`, `message`) into friendly human-readable messages.
- **Service Classes**:
  - `HealthService.getHealth()`
  - `DocumentService.getDocuments()`, `uploadDocument()`, `deleteDocument()`
  - `ChatService.sendMessage()`, `getSessionHistory()`

---

## 🚀 Running Locally

```bash
# In frontend/
npm install

# Start Vite dev server with proxy to backend (http://localhost:8000)
npm run dev

# Build production bundle with code-splitting
npm run build

# Preview production bundle
npm run preview
```
