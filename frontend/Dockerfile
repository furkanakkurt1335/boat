FROM node:22-slim AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# ---------- production ----------
FROM node:22-slim

RUN groupadd -r boat && useradd -r -g boat -d /app -s /sbin/nologin boat

WORKDIR /app

COPY --from=builder /app/build ./build
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules

RUN chown -R boat:boat /app

USER boat

EXPOSE 3000

ENV PORT=3000
ENV HOST=0.0.0.0
ENV ORIGIN=http://localhost:3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD node -e "fetch('http://localhost:3000').then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))" || exit 1

CMD ["node", "build"]
