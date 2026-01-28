# Render Keep-Alive Service

Simple Vercel app that pings your Render service every 2 hours to prevent it from sleeping.

## Setup

1. Deploy to Vercel
2. Set environment variable: `RENDER_URL` (your Render service URL)
3. Cron job will automatically run every 2 hours

## Manual Test

Visit: `https://your-app.vercel.app/api/ping`

## Configuration

Edit `vercel.json` to change cron schedule:
- `0 */2 * * *` - Every 2 hours (default)
- `0 * * * *` - Every hour
- `*/30 * * * *` - Every 30 minutes
