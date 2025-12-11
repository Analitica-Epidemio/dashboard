# Dockerfile para Frontend Next.js
# Multi-stage build optimizado para producción

# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: Dependencias
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Instalar pnpm
RUN corepack enable && corepack prepare pnpm@9 --activate

# Copiar archivos de dependencias
COPY package.json pnpm-lock.yaml ./

# Instalar dependencias
RUN pnpm install --frozen-lockfile

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Build
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app

RUN corepack enable && corepack prepare pnpm@9 --activate

# Copiar dependencias del stage anterior
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Variables de entorno para el build
ARG NEXT_PUBLIC_API_HOST
ARG NEXT_PUBLIC_APP_ENV=production
ARG SECRET_KEY
ENV SECRET_KEY=$SECRET_KEY
ENV NEXT_PUBLIC_API_HOST=$NEXT_PUBLIC_API_HOST
ENV NEXT_PUBLIC_APP_ENV=$NEXT_PUBLIC_APP_ENV
ENV NEXT_TELEMETRY_DISABLED=1

# Build de producción
RUN pnpm build

# ─────────────────────────────────────────────────────────────────────────────
# Stage 3: Runner (imagen mínima de producción)
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Usuario no-root para seguridad
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copiar archivos necesarios
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
