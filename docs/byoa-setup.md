# Bring Your Own API Setup

Recombyne uses a bring-your-own-API (BYOA) model so you keep full control over credentials, limits, and billing. No central key escrow is required.

## 1) Get a Twitter Bearer Token
1. Sign in at <https://developer.twitter.com/en/portal/dashboard>.
2. Create or open an app in your project.
3. Enable API v2 access.
4. Copy the app Bearer Token.
5. Paste it into `TWITTER_BEARER_TOKEN` in `.env`.

## 2) Get Reddit Credentials
1. Sign in at <https://www.reddit.com/prefs/apps>.
2. Click **Create App**.
3. Select **script** app type.
4. Copy the client ID and secret.
5. Set `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, and `REDDIT_USER_AGENT` in `.env`.

## 3) Create `.env`
From repository root:

```bash
cp .env.example .env
```

Fill in your key values and save.

## 4) Verify Before Running
Run the key validation helper:

```bash
python scripts/test_keys.py
```

The script prints pass/fail for each source with troubleshooting hints.
