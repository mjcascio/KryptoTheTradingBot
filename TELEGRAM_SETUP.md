# Setting Up Telegram Notifications for KryptoBot

This guide will help you set up Telegram notifications for your KryptoBot trading system.

## Why Use Telegram Notifications?

Telegram notifications provide a convenient way to receive real-time updates about your trading activities, including:

- Daily trading summaries
- Trade execution alerts
- Position updates
- Performance metrics

## Creating a Telegram Bot

To set up Telegram notifications, you need to create a bot and get its token:

1. **Open Telegram** and search for `@BotFather`
2. **Start a chat** with BotFather and send the command `/newbot`
3. **Follow the instructions** to create a new bot:
   - Provide a name for your bot (e.g., "KryptoTradingBot")
   - Provide a username for your bot (must end with "bot", e.g., "krypto_trading_bot")
4. **Copy the token** provided by BotFather (it looks like `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`)
5. **Send a message** to your new bot to activate the chat

## Getting Your Chat ID

After creating a bot, you need to get your chat ID:

1. **Run the helper script**:
   ```bash
   ./get_chat_id.py
   ```
2. When prompted, **enter your bot token**
3. The script will display your chat ID and instructions for adding it to your `.env` file

Alternatively, you can get your chat ID manually:
1. Send a message to your bot
2. Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` in your browser
3. Look for the `"chat":{"id":` field in the response

## Updating Your Configuration

Once you have your bot token and chat ID, update your `.env` file:

1. **Open the `.env` file** in your favorite text editor
2. **Update the Telegram section**:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```
3. **Save the file**

## Testing Your Configuration

To test if your Telegram notifications are working:

1. **Run the test script**:
   ```bash
   ./send_telegram_env.py
   ```
2. If successful, you should receive a test message in your Telegram chat

## Troubleshooting

If you encounter issues with Telegram notifications:

### 401 Unauthorized Error
- This means your bot token is invalid or has been revoked
- Create a new bot with BotFather and update your `.env` file

### 400 Bad Request Error
- This usually means your chat ID is incorrect
- Run `./get_chat_id.py` again to get the correct chat ID

### 404 Not Found Error
- This could mean the API endpoint is incorrect
- Check for typos in your bot token

## Using Telegram Notifications

Once configured, Telegram notifications will be automatically sent by:

- **Daily Summary**: Sends a daily summary of your trading activity
- **Trade Execution**: Notifies you when a trade is executed
- **Position Updates**: Notifies you when positions change

You can generate and send a daily summary in several ways:

1. **Using the daily summary script directly**:
   ```bash
   ./daily_summary.py --now
   ```

2. **Using the run_daily_summary.py script** (recommended):
   ```bash
   ./run_daily_summary.py
   ```
   This script sets the Telegram environment variables directly, which ensures they are correctly loaded.

3. **Using the start_daily_summary.sh script**:
   ```bash
   ./start_daily_summary.sh --now
   ```
   This script also sets the environment variables and can be used to schedule the daily summary.

## Scheduling Daily Summaries

To schedule daily summaries to run automatically at the end of each trading day:

```bash
./start_daily_summary.sh --time 16:00
```

This will start a background service that will generate and send a daily summary at 4:00 PM every trading day.

## Additional Resources

- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [BotFather Commands](https://core.telegram.org/bots#botfather-commands)
- [Telegram Bot Development](https://core.telegram.org/bots) 