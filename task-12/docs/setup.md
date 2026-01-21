# n8n Twitter AI/ML Reply Automation – Setup

This guide covers environment variables, Groq and X/Twitter auth (cookies and password), the one-time cookie export, first run, and troubleshooting.

---

## 1. Requirements

- **Docker** (and Docker Compose) for n8n with Chromium via the `n8n-nodes-puppeteer` image
- **Groq API key** from [console.groq.com](https://console.groq.com)
- **X/Twitter account** (for password auth: app password if 2FA is enabled)

---

## 2. Environment variables

Set these in a `.env` file next to `docker-compose.yml` or export them in your shell.

| Variable         | Example   | Required | Description                                                                 |
|------------------|-----------|----------|-----------------------------------------------------------------------------|
| `GROQ_API_KEY`   | `gsk_...` | **Yes**  | Groq API key for classification and reply generation                        |
| `TARGET_REPLIES`| `50`      | No       | Stop posting when total replies reach this (default: `50`)                  |
| `BATCH_SIZE`     | `5`       | No       | Max replies per run; set the **Limit** node’s “Max items” in the workflow   |
| `X_USER`         | `@user`   | **Yes**  | X username/email; in `data/config.json` for the Login node                  |
| `X_PASSWORD`     | `...`     | **Yes**  | X password or app password (2FA); in `data/config.json`                     |

The workflow reads `X_USER` and `X_PASSWORD` from `data/config.json`, not from `.env`.

---

## 3. Groq and config

1. Sign up at [console.groq.com](https://console.groq.com) and create an API key.
2. Create `data/config.json` from `data/config.json.example` and set `GROQ_API_KEY`, `X_USER`, and `X_PASSWORD`. The workflow reads all of these from the file.
3. The workflow uses `llama-3.1-8b-instant` for both classification and reply generation.

---

## 4. X/Twitter auth (username + password)

The workflow logs in to X/Twitter on each run using **username and password** (no cookie file).

- Put **`X_USER`** and **`X_PASSWORD`** in `data/config.json`:
  - `X_USER`: your X email or @handle
  - `X_PASSWORD`: your password, or an **app password** if you use 2FA (X: Settings → Security → App passwords)
- The **Load config** node reads these; the **Login** (Puppeteer) node opens the Twitter login page, enters them, and continues the run with the session cookies.
- **Do not commit `data/config.json`**; it contains secrets. Use `data/config.json.example` as a template.

---

## 5. Login flow and fallback

The **Login** node goes to the Twitter login page, enters username and password from `config.json`, and continues. If X changes its login flow, update the **Login** node's `jsCode` or use a cookie-based fallback (see end of this section).

### Option 5a – Separate n8n workflow

1. **Manual Trigger** → **Puppeteer – Run Custom Script**.
2. Script (conceptual; adjust selectors if X changes):

   ```js
   await $page.goto('https://twitter.com/i/flow/login');
   await $page.waitForSelector('input[autocomplete="username"]', { visible: true });
   await $page.type('input[autocomplete="username"]', 'YOUR_X_USER');
   await $page.click('button[role="button"]:has-text("Next")');
   await $page.waitForSelector('input[name="password"]', { visible: true });
   await $page.type('input[name="password"]', 'YOUR_X_PASSWORD');
   await $page.click('button[role="button"]:has-text("Log in")');
   await $page.waitForNavigation({ waitUntil: 'networkidle0' });
   const cookies = await $page.cookies();
   return [{ json: { cookies } }];
   ```

3. Add a **Code** node:  
   `JSON.stringify($input.first().json.cookies, null, 2)` and use “Write Binary to File” or any node that can write to the mounted `data/` directory.  
   Or run a one-off script on the host that reads the output and writes `data/cookies.json`.

### Option 5b – Manual export

- Use a browser extension to export X/Twitter cookies (e.g. “EditThisCookie”, “Cookie-Editor”) while logged in.
- Save as `data/cookies.json` either as `[...] or `{ "cookies": [...] }`.

Ensure the `data/` directory is the one mounted as `/data` in the container so `Load cookies` can read `/data/cookies.json`.

---

## 6. First run

1. **Create `data/` and initial files** (if not already in the repo):

   - `data/replyCount.json` → `{"count": 0}` or `{"count": 0, "target": 50}` (optional `target`; default 50)
   - `data/repliedIds.json` → `[]`
   - `data/config.json` → copy from `data/config.json.example`, then set `GROQ_API_KEY` to your Groq key (e.g. `{"GROQ_API_KEY": "gsk_..."}`)
   - `data/cookies.json` → from the one-time login (Option A)

2. **Configure env**

   - The workflow reads `GROQ_API_KEY`, `X_USER`, and `X_PASSWORD` from `data/config.json`. No `.env` needed for these.

3. **Build and start:**

   ```bash
   docker compose build
   docker compose up -d
   ```

4. **Open n8n** at `http://localhost:5678`.

5. **Import the workflow**  
   - Import `workflows/twitter-ai-reply-automation.json`.

6. **Tune the Limit node**  
   - Set “Max items” to your desired `BATCH_SIZE` (e.g. 5–10). The env var `BATCH_SIZE` does not automatically change this; you set it in the node.

7. **Activate** the workflow (or run manually once to test).  
   - The schedule runs every 4 hours by default. It will stop when `replyCount.json`’s `count` reaches the `target` value (or 50 if omitted).

---

## 7. Troubleshooting

### Selectors (e.g. `tweetTextarea_0`, `tweetButtonInline`, `reply`)

- X’s DOM changes often. If **Scrape** or **Post** fail with “selector not found”:
  - Inspect the live X page (home timeline, reply composer) and update the `data-testid` or `role` selectors in the Puppeteer scripts.
  - Common fallbacks: `div[role="textbox"]` for the reply box, `div[data-testid="tweetButton"]` for the submit button.

### 2FA

- If you use **Option B (password)**, log in with an **app password** (X: Settings → Security → App passwords).  
- For **Option A**, export cookies **after** you have passed 2FA in the browser, so the cookie set includes the authenticated session.

### Rate limits and blocks

- Posting many replies in a short time is risky. The workflow uses:
  - A **Limit** (e.g. 5–10 per run),
  - **10–30 s** random delay between replies in the Post script,
  - A **schedule** every few hours.
- If you hit blocks or rate limits:
  - Reduce `BATCH_SIZE` and/or run the schedule less often.
  - Consider a proxy (Puppeteer “Proxy Server” in the node options) or a residential IP; see the plan’s “Optional improvements”.

### `GROQ_API_KEY missing` / `process is not defined`

- The Code nodes do **not** use `process.env` (it is not available in n8n’s sandbox). Create **`data/config.json`** with `{"GROQ_API_KEY": "gsk_..."}`. Copy `data/config.json.example` and replace the placeholder with your key.

### `Create /data/cookies.json first`

- You are using **Option A** but `data/cookies.json` is missing or not mounted.
- Create it with the one-time login workflow or a manual export, and ensure `./data` is bound to `/data` in the container.

### `Unrecognized node type: n8n-nodes-puppeteer.puppeteer`

- The Puppeteer node is loaded from `N8N_CUSTOM_EXTENSIONS`. Ensure `docker-compose` and the image set it to `/opt/n8n-custom-nodes/node_modules/n8n-nodes-puppeteer`. Rebuild (`docker compose build --no-cache`) and recreate the container (`docker compose up -d --force-recreate`).

### `Error while fetching community nodes: timeout of 3000ms exceeded`

- n8n fetches the community registry on startup; in restricted networks this can timeout. It does **not** affect the locally installed `n8n-nodes-puppeteer` from `N8N_CUSTOM_EXTENSIONS`. Safe to ignore. To reduce log noise: `N8N_COMMUNITY_PACKAGES_ENABLED=false`.

### `fs is disallowed` / `require('fs')` in Code nodes

- n8n blocks `fs` by default. Use **`NODE_FUNCTION_ALLOW_BUILTIN=fs`** (built‑in modules), not `NODE_FUNCTION_ALLOW_EXTERNAL`. The `docker-compose` in this project sets it. Recreate the container: `docker compose up -d --force-recreate`.

### Puppeteer / Chromium

- The image includes Chromium and `n8n-nodes-puppeteer`. If you see “Failed to launch browser”:
  - Confirm the Dockerfile and `PUPPETEER_EXECUTABLE_PATH` match your base image (e.g. Alpine’s `/usr/bin/chromium-browser`).
  - In restricted environments, you may need to use a remote browser (e.g. Browserless) and set the Puppeteer “Browser WebSocket Endpoint” in the node options.

---

## 8. Data files and `data/` layout

- `data/` is mounted as `/data` in the container.
- The workflow reads/writes:
  - `/data/replyCount.json` – `{ "count": 0, "target": 50 }`; `count` is incremented each run; optional `target` sets the reply limit (default 50).
  - `/data/repliedIds.json` – `[]`; tweet IDs of successfully posted replies are appended.
  - `/data/config.json` – `{"GROQ_API_KEY": "gsk_...", "X_USER": "your_email_or_handle", "X_PASSWORD": "your_password_or_app_password"}`; required. Copy from `data/config.json.example`.

Ensure `data/` exists and is writable by the user running n8n in the container.
