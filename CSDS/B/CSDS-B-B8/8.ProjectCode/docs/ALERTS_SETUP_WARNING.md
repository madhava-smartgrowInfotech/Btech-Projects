# WARNING - Telegram and email alerts are not configured yet

CareWatch detects falls, runs the 'I'm OK' countdown, saves the snapshot and logs every alert. **But it can't
deliver alerts to family until these `.env` keys are filled in.** Until then each alert is marked
**undelivered**, with the reason "not configured" per channel. The Alerts and Contacts & settings screens show
the same warning.

| Key in `.env` | What it is | Status |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | **empty** |
| `SMTP_USER` | Gmail address that sends the alert emails | **empty** |
| `SMTP_PASSWORD` | Gmail **app password** (16 characters, not your normal password) | **empty** |

## How to fill them in (about 5 minutes)

**Telegram**
1. In Telegram, open **@BotFather**, send `/newbot`, pick a name. Copy the token it gives you.
2. Paste it into `.env` as `TELEGRAM_BOT_TOKEN=...`.
3. Each family member opens the new bot and sends it any message (for example "hi").
4. Restart CareWatch (`run.bat`). Go to **Contacts & settings -> Look up chats**, then click **Add as contact**.

**Gmail**
1. Turn on 2-Step Verification for the Google account (myaccount.google.com -> Security).
2. Open **App passwords**, create one called "CareWatch", and copy the 16-character password.
3. Put it in `.env`: `SMTP_USER=your.address@gmail.com` and `SMTP_PASSWORD=the app password`.
4. Restart CareWatch. Add each contact's email under **Contacts & settings**.

**Check it works:** Alerts -> **Send test alert**. Each contact should get a Telegram message and an email
within a few seconds. The alert card shows per-contact delivery and the time each one took.
