# Frontend Development Guide

This guide covers frontend development for the Grid Services React application, including setup, component architecture, API integration, and deployment workflows.

## Project Overview

The Grid Services frontend is a modern React application built with:

- **Vite** - Fast build tool and development server
- **TypeScript** - Type-safe JavaScript development
- **React 18** - Modern React with hooks and concurrent features
- **shadcn/ui** - Beautiful, accessible UI components
- **Tailwind CSS** - Utility-first CSS framework
- **React Query** - Server state management
- **React Router** - Client-side routing
- **Lovable.dev** - Visual development platform integration

## Development Setup

### Prerequisites
- **Node.js 18+** and **npm**
- **Git** for version control
- **VS Code** (recommended) with TypeScript support

### Local Development
```bash
# Clone and navigate to frontend directory
cd ecs-frontend

# Install dependencies
npm install

# Start development server
npm run dev

# The app will be available at http://localhost:5173
```

### Available Scripts
```bash
# Development
npm run dev              # Start dev server with hot reload
npm run preview          # Preview production build locally

# Building
npm run build            # Production build
npm run build:dev        # Development build

# Code Quality
npm run lint             # ESLint checking
npm run type-check       # TypeScript checking (if configured)
```

### Environment Configuration
```bash
# .env.development
VITE_API_BASE_URL=http://localhost:8000
VITE_VEN_BASE_URL=http://localhost:8081
VITE_IOT_ENDPOINT=localhost:1883
VITE_ENVIRONMENT=development

# .env.production
VITE_API_BASE_URL=https://api.gridcircuit.link
VITE_VEN_BASE_URL=https://sim.gridcircuit.link
VITE_IOT_ENDPOINT=a1mgxpe8mg484j-ats.iot.us-west-2.amazonaws.com
VITE_ENVIRONMENT=production
```

## Project Structure

### Directory Layout
```
ecs-frontend/
├── public/                     # Static assets
│   └── robots.txt
├── src/                        # Source code
│   ├── components/             # Reusable UI components
│   │   ├── ui/                # shadcn/ui components
│   │   ├── charts/            # Chart components
│   │   ├── forms/             # Form components
│   │   └── layout/            # Layout components
│   ├── hooks/                 # Custom React hooks
│   │   ├── useApi.ts          # API integration hooks
│   │   ├── useVenData.ts      # VEN data fetching
│   │   └── useWebSocket.ts    # WebSocket connections
│   ├── lib/                   # Utility libraries
│   │   ├── api.ts             # API client configuration
│   │   ├── utils.ts           # Utility functions
│   │   └── validations.ts     # Zod schemas
│   ├── pages/                 # Page components
│   │   ├── Dashboard.tsx      # Main dashboard
│   │   ├── VenControl.tsx     # VEN control interface
│   │   ├── Analytics.tsx      # Analytics and reporting
│   │   └── Settings.tsx       # Configuration settings
│   ├── types/                 # TypeScript type definitions
│   │   ├── api.ts             # API response types
│   │   ├── ven.ts             # VEN-specific types
│   │   └── common.ts          # Common types
│   ├── App.tsx                # Main application component
│   ├── main.tsx               # Application entry point
│   └── index.css              # Global styles
├── components.json             # shadcn/ui configuration
├── tailwind.config.ts          # Tailwind CSS configuration
├── tsconfig.json              # TypeScript configuration
├── vite.config.ts             # Vite configuration
└── package.json               # Dependencies and scripts
```

### Component Architecture

#### UI Components (`src/components/ui/`)
```typescript
// Example: Button component with variants
import { Button } from "@/components/ui/button"

<Button variant="default" size="lg">
  Primary Action
</Button>

<Button variant="outline" size="sm">
  Secondary Action  
</Button>
```

#### Custom Components
```typescript
// src/components/VenStatusCard.tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface VenStatusCardProps {
  venId: string
  status: 'online' | 'offline' | 'error'
  powerKw: number
  lastSeen: Date
}

export function VenStatusCard({ venId, status, powerKw, lastSeen }: VenStatusCardProps) {
  const statusColors = {
    online: 'bg-green-500',
    offline: 'bg-gray-500', 
    error: 'bg-red-500'
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          {venId}
          <Badge className={statusColors[status]}>
            {status}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div>Power: {powerKw.toFixed(1)} kW</div>
          <div>Last Seen: {lastSeen.toLocaleString()}</div>
        </div>
      </CardContent>
    </Card>
  )
}
```

## API Integration

### API Client Setup
```typescript
// src/lib/api.ts
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for auth
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth-token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('auth-token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export { api }
```

### Type-Safe API Hooks
```typescript
// src/hooks/useApi.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { VenData, NetworkStats, LoadConfig } from '@/types/api'

// Fetch network statistics
export function useNetworkStats() {
  return useQuery({
    queryKey: ['network-stats'],
    queryFn: async (): Promise<NetworkStats> => {
      const { data } = await api.get('/stats/network')
      return data
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  })
}

// Fetch VEN data
export function useVenData(venId: string) {
  return useQuery({
    queryKey: ['ven-data', venId],
    queryFn: async (): Promise<VenData> => {
      const { data } = await api.get(`/vens/${venId}`)
      return data
    },
    enabled: !!venId,
  })
}

// Update load configuration
export function useUpdateLoadConfig() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ venId, loadId, config }: {
      venId: string
      loadId: string
      config: LoadConfig
    }) => {
      const { data } = await api.put(`/vens/${venId}/loads/${loadId}`, config)
      return data
    },
    onSuccess: (_, { venId }) => {
      // Invalidate VEN data to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['ven-data', venId] })
    },
  })
}
```

### VEN HTTP API Integration
```typescript
// src/hooks/useVenData.ts
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

const venApi = axios.create({
  baseURL: import.meta.env.VITE_VEN_BASE_URL,
  timeout: 5000,
})

export function useVenLiveData(venId: string) {
  return useQuery({
    queryKey: ['ven-live', venId],
    queryFn: async () => {
      const { data } = await venApi.get('/live')
      return data
    },
    refetchInterval: 2000, // Real-time updates
    retry: 2,
  })
}

export function useVenConfig(venId: string) {
  return useQuery({
    queryKey: ['ven-config', venId],
    queryFn: async () => {
      const { data } = await venApi.get('/config')
      return data
    },
  })
}

export function useVenCircuits(venId: string) {
  return useQuery({
    queryKey: ['ven-circuits', venId],
    queryFn: async () => {
      const { data } = await venApi.get('/circuits')
      return data
    },
  })
}
```

## State Management

### React Query Configuration
```typescript
// src/main.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: (failureCount, error) => {
        if (error?.response?.status === 404) return false
        return failureCount < 3
      },
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          {/* Your routes */}
        </Routes>
      </Router>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
```

### Local State with Hooks
```typescript
// src/hooks/useLocalStorage.ts
import { useState, useEffect } from 'react'

export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key)
      return item ? JSON.parse(item) : initialValue
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error)
      return initialValue
    }
  })

  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value
      setStoredValue(valueToStore)
      window.localStorage.setItem(key, JSON.stringify(valueToStore))
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error)
    }
  }

  return [storedValue, setValue] as const
}
```

## Component Development

### Page Components
```typescript
// src/pages/Dashboard.tsx
import { useNetworkStats } from '@/hooks/useApi'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'

export function Dashboard() {
  const { data: stats, isLoading, error } = useNetworkStats()

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Failed to load dashboard data. Please try again.
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Grid Services Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Total Power</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.totalPowerKw.toFixed(1)} kW
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Active VENs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.activeVenCount}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Reduction Available</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.availableReductionKw.toFixed(1)} kW
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
```

### Form Components with Validation
```typescript
// src/components/forms/LoadConfigForm.tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'

const loadConfigSchema = z.object({
  loadId: z.string().min(1, 'Load ID is required'),
  enabled: z.boolean(),
  capacityKw: z.number().min(0, 'Capacity must be positive'),
  priority: z.number().int().min(1).max(10),
})

type LoadConfigFormData = z.infer<typeof loadConfigSchema>

interface LoadConfigFormProps {
  initialData?: Partial<LoadConfigFormData>
  onSubmit: (data: LoadConfigFormData) => void
  isLoading?: boolean
}

export function LoadConfigForm({ initialData, onSubmit, isLoading }: LoadConfigFormProps) {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<LoadConfigFormData>({
    resolver: zodResolver(loadConfigSchema),
    defaultValues: initialData,
  })

  const enabled = watch('enabled')

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <Label htmlFor="loadId">Load ID</Label>
        <Input
          id="loadId"
          {...register('loadId')}
          error={errors.loadId?.message}
        />
      </div>

      <div className="flex items-center space-x-2">
        <Switch
          id="enabled"
          checked={enabled}
          onCheckedChange={(checked) => setValue('enabled', checked)}
        />
        <Label htmlFor="enabled">Enabled</Label>
      </div>

      <div>
        <Label htmlFor="capacityKw">Capacity (kW)</Label>
        <Input
          id="capacityKw"
          type="number"
          step="0.1"
          {...register('capacityKw', { valueAsNumber: true })}
          error={errors.capacityKw?.message}
        />
      </div>

      <div>
        <Label htmlFor="priority">Priority (1-10)</Label>
        <Input
          id="priority"
          type="number"
          {...register('priority', { valueAsNumber: true })}
          error={errors.priority?.message}
        />
      </div>

      <Button type="submit" disabled={isLoading}>
        {isLoading ? 'Saving...' : 'Save Configuration'}
      </Button>
    </form>
  )
}
```

## Real-Time Features

### WebSocket Integration
```typescript
// src/hooks/useWebSocket.ts
import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

export function useWebSocket(url: string) {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<any>(null)
  const ws = useRef<WebSocket | null>(null)
  const queryClient = useQueryClient()

  useEffect(() => {
    const connect = () => {
      ws.current = new WebSocket(url)

      ws.current.onopen = () => {
        setIsConnected(true)
        console.log('WebSocket connected')
      }

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setLastMessage(data)
          
          // Invalidate relevant queries based on message type
          if (data.type === 'ven-update') {
            queryClient.invalidateQueries({ queryKey: ['ven-data', data.venId] })
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      ws.current.onclose = () => {
        setIsConnected(false)
        console.log('WebSocket disconnected, attempting to reconnect...')
        setTimeout(connect, 3000) // Reconnect after 3 seconds
      }

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    }

    connect()

    return () => {
      ws.current?.close()
    }
  }, [url, queryClient])

  const sendMessage = (message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message))
    }
  }

  return { isConnected, lastMessage, sendMessage }
}
```

### Live Data Components
```typescript
// src/components/LivePowerGauge.tsx
import { useVenLiveData } from '@/hooks/useVenData'
import { Progress } from '@/components/ui/progress'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface LivePowerGaugeProps {
  venId: string
  maxPowerKw: number
}

export function LivePowerGauge({ venId, maxPowerKw }: LivePowerGaugeProps) {
  const { data, isLoading, error } = useVenLiveData(venId)

  if (isLoading) {
    return <div className="animate-pulse h-32 bg-gray-200 rounded" />
  }

  if (error) {
    return <div className="text-red-500">Error loading power data</div>
  }

  const powerPercent = (data?.power_kw || 0) / maxPowerKw * 100

  return (
    <Card>
      <CardHeader>
        <CardTitle>Live Power Output</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-3xl font-bold">
          {data?.power_kw?.toFixed(1) || '0.0'} kW
        </div>
        <Progress value={powerPercent} className="h-4" />
        <div className="text-sm text-gray-500">
          {powerPercent.toFixed(1)}% of capacity ({maxPowerKw} kW)
        </div>
      </CardContent>
    </Card>
  )
}
```

## Styling and Theming

### Tailwind CSS Configuration
```typescript
// tailwind.config.ts
import { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        // Custom grid services colors
        'grid-green': '#10b981',
        'grid-blue': '#3b82f6',
        'grid-red': '#ef4444',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}

export default config
```

### Dark Mode Support
```typescript
// src/components/theme-provider.tsx
import { createContext, useContext, useEffect, useState } from 'react'

type Theme = 'dark' | 'light' | 'system'

type ThemeProviderProps = {
  children: React.ReactNode
  defaultTheme?: Theme
  storageKey?: string
}

type ThemeProviderState = {
  theme: Theme
  setTheme: (theme: Theme) => void
}

const ThemeProviderContext = createContext<ThemeProviderState | undefined>(undefined)

export function ThemeProvider({
  children,
  defaultTheme = 'system',
  storageKey = 'grid-services-theme',
  ...props
}: ThemeProviderProps) {
  const [theme, setTheme] = useState<Theme>(
    () => (localStorage.getItem(storageKey) as Theme) || defaultTheme
  )

  useEffect(() => {
    const root = window.document.documentElement
    root.classList.remove('light', 'dark')

    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'
      root.classList.add(systemTheme)
      return
    }

    root.classList.add(theme)
  }, [theme])

  const value = {
    theme,
    setTheme: (theme: Theme) => {
      localStorage.setItem(storageKey, theme)
      setTheme(theme)
    },
  }

  return (
    <ThemeProviderContext.Provider {...props} value={value}>
      {children}
    </ThemeProviderContext.Provider>
  )
}

export const useTheme = () => {
  const context = useContext(ThemeProviderContext)
  if (context === undefined)
    throw new Error('useTheme must be used within a ThemeProvider')
  return context
}
```

## Building and Deployment

### Production Build
```bash
# Create optimized production build
npm run build

# Build output goes to `dist/` directory
# - index.html (entry point)
# - assets/ (JS, CSS, images with hashed filenames)
```

### Docker Integration
```dockerfile
# ecs-frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx Configuration
```nginx
# nginx/default.conf
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Enable gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript;

    # Handle client-side routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

## Lovable.dev Integration

### Development Workflow
```bash
# Working with Lovable.dev platform
# 1. Changes made in Lovable are automatically committed to git
# 2. Local changes can be pushed and will appear in Lovable
# 3. No special configuration needed - just standard git workflow
```

### Project Configuration
```json
// package.json - Lovable-specific configuration
{
  "lovable": {
    "projectId": "fbe406b3-af67-4382-b3f6-b6cfe27f19bf",
    "buildCommand": "npm run build",
    "outputDirectory": "dist"
  }
}
```

### Deployment from Lovable
```bash
# Deploy directly from Lovable platform:
# 1. Open project in Lovable
# 2. Click Share -> Publish
# 3. Choose deployment target
# 4. Automatic build and deployment
```

## Testing Strategy

### Component Testing
```typescript
// src/components/__tests__/VenStatusCard.test.tsx
import { render, screen } from '@testing-library/react'
import { VenStatusCard } from '../VenStatusCard'

describe('VenStatusCard', () => {
  const mockProps = {
    venId: 'ven-001',
    status: 'online' as const,
    powerKw: 2.5,
    lastSeen: new Date('2023-10-11T15:30:00Z'),
  }

  it('renders VEN information correctly', () => {
    render(<VenStatusCard {...mockProps} />)
    
    expect(screen.getByText('ven-001')).toBeInTheDocument()
    expect(screen.getByText('online')).toBeInTheDocument()
    expect(screen.getByText('Power: 2.5 kW')).toBeInTheDocument()
  })

  it('shows correct status badge color', () => {
    render(<VenStatusCard {...mockProps} />)
    
    const badge = screen.getByText('online')
    expect(badge).toHaveClass('bg-green-500')
  })
})
```

### API Testing
```typescript
// src/hooks/__tests__/useApi.test.ts
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useNetworkStats } from '../useApi'

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useNetworkStats', () => {
  it('fetches network statistics', async () => {
    const { result } = renderHook(() => useNetworkStats(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toHaveProperty('totalPowerKw')
    expect(result.current.data).toHaveProperty('activeVenCount')
  })
})
```

## Performance Optimization

### Code Splitting
```typescript
// src/App.tsx - Lazy load pages
import { lazy, Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'
import { Skeleton } from '@/components/ui/skeleton'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const VenControl = lazy(() => import('./pages/VenControl'))
const Analytics = lazy(() => import('./pages/Analytics'))

function App() {
  return (
    <Suspense fallback={<Skeleton className="h-screen w-full" />}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/ven-control" element={<VenControl />} />
        <Route path="/analytics" element={<Analytics />} />
      </Routes>
    </Suspense>
  )
}
```

### Bundle Analysis
```bash
# Analyze bundle size
npm install --save-dev vite-bundle-analyzer
npx vite-bundle-analyzer

# Optimize images
npm install --save-dev @squoosh/lib
# Configure in vite.config.ts for automatic image optimization
```

## Deployment Workflows

### ECS Deployment
```bash
# Build and push frontend image
cd ecs-frontend
./build_and_push.sh

# Update ECS service
aws ecs update-service \
  --cluster grid-services-dev \
  --service frontend-service \
  --force-new-deployment
```

### Environment-Specific Builds
```bash
# Development build with source maps
npm run build:dev

# Production build optimized
npm run build

# Environment variables are injected at build time
```

This comprehensive frontend development guide provides everything needed to build, maintain, and deploy the Grid Services React application effectively.