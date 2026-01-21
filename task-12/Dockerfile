# n8n + n8n-nodes-puppeteer + Chromium for Twitter AI Reply Automation
# Uses node:20-alpine so we can apk-add Chromium; n8n:latest is distroless (no apk).
FROM node:20-alpine

# Install Chrome dependencies, Chromium, and git (needed by n8n-nodes-puppeteer for github: deps)
RUN apk add --no-cache \
    chromium \
    nss \
    glib \
    freetype \
    freetype-dev \
    harfbuzz \
    ca-certificates \
    ttf-freefont \
    udev \
    ttf-liberation \
    font-noto-emoji \
    git

# Tell Puppeteer to use installed Chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser

# Install n8n and n8n-nodes-puppeteer
RUN npm install -g n8n && \
    mkdir -p /opt/n8n-custom-nodes && \
    cd /opt/n8n-custom-nodes && \
    npm install n8n-nodes-puppeteer && \
    chown -R node:node /opt/n8n-custom-nodes

# n8n loads custom nodes: point to the package root (must have package.json with "n8n" key)
ENV N8N_CUSTOM_EXTENSIONS=/opt/n8n-custom-nodes/node_modules/n8n-nodes-puppeteer

USER node

WORKDIR /home/node

EXPOSE 5678

CMD ["n8n", "start"]
