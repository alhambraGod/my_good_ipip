# syntax=docker/dockerfile:1.7
# MindPrism frontend — Next.js 16 on Node 20 alpine
#
# Build:   docker build -f frontend/Dockerfile -t mindprism-frontend:latest frontend/
# Run:     docker run --rm -p 3000:3000 -e NEXT_PUBLIC_API_URL=... mindprism-frontend

FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
# `npm ci --omit=dev` for slimmer images, but Next 16 build needs devDeps.
# So install everything in build stage, then copy only the runtime artefacts.
RUN npm ci

# ----------------------- BUILD ---------------------------------------------
FROM node:20-alpine AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . ./
ARG NEXT_PUBLIC_API_URL=http://localhost:3001
ARG NEXT_PUBLIC_SITE_URL=http://localhost:3000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL
RUN npm run build

# ----------------------- RUNTIME -------------------------------------------
FROM node:20-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000

# Copy only the necessary build outputs.
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/package-lock.json ./package-lock.json
COPY --from=builder /app/node_modules ./node_modules

RUN addgroup -S mindprism && adduser -S mindprism -G mindprism \
    && chown -R mindprism:mindprism /app
USER mindprism

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD wget -q -O- http://127.0.0.1:3000/ > /dev/null || exit 1

CMD ["npm", "run", "start", "--", "--port", "3000", "--hostname", "0.0.0.0"]
