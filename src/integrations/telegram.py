"""Telegram integration for notifications and command handling."""

import logging
from typing import Any, Optional
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from ..utils.config import Config

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Handles Telegram notifications and commands."""
    
    def __init__(self, config: Config) -> None:
        """Initialize Telegram notifier.
        
        Args:
            config: Bot configuration
        """
        self.config = config
        self.bot_token = config.get('monitoring.telegram_bot_token')
        self.chat_id = config.get('monitoring.telegram_chat_id')
        self.enabled = config.get('monitoring.telegram_enabled', False)
        
        if not self.enabled:
            logger.info("Telegram notifications are disabled")
            return
            
        if not self.bot_token or not self.chat_id:
            logger.error("Missing Telegram configuration")
            self.enabled = False
            return
            
        self.application = Application.builder().token(self.bot_token).build()
        self._setup_handlers()
        logger.info("Telegram notifier initialized")
        
    def _setup_handlers(self) -> None:
        """Set up command handlers."""
        # Core commands
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("help", self._help_command))
        self.application.add_handler(CommandHandler("status", self._status_command))
        
        # Trading commands
        self.application.add_handler(CommandHandler("positions", self._positions_command))
        self.application.add_handler(CommandHandler("balance", self._balance_command))
        self.application.add_handler(CommandHandler("performance", self._performance_command))
        
        # System commands
        self.application.add_handler(CommandHandler("stop", self._stop_command))
        self.application.add_handler(CommandHandler("restart", self._restart_command))
        self.application.add_handler(CommandHandler("diagnostics", self._diagnostics_command))
        
        # Error handler
        self.application.add_error_handler(self._error_handler)
        
    async def start(self) -> None:
        """Start the Telegram bot."""
        if not self.enabled:
            return
            
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("Telegram bot started")
            await self.send_message("Trading bot started and ready for commands! 🚀")
            
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")
            self.enabled = False
            
    async def stop(self) -> None:
        """Stop the Telegram bot."""
        if not self.enabled:
            return
            
        try:
            await self.send_message("Trading bot shutting down... 👋")
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Telegram bot stopped")
            
        except Exception as e:
            logger.error(f"Error stopping Telegram bot: {e}")
            
    async def send_message(
        self,
        message: str,
        parse_mode: Optional[str] = None,
        reply_markup: Any = None
    ) -> bool:
        """Send a message to the configured chat.
        
        Args:
            message: Message text
            parse_mode: Message parse mode (None, HTML, Markdown)
            reply_markup: Reply markup
            
        Returns:
            True if message was sent successfully
        """
        if not self.enabled:
            return False
            
        try:
            await self.application.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
            return True
            
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
            
    # Command Handlers
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        welcome_message = (
            "👋 Welcome to the Trading Bot!\n\n"
            "Available commands:\n"
            "/help - Show this help message\n"
            "/status - Get bot status\n"
            "/positions - View open positions\n"
            "/balance - Check account balance\n"
            "/performance - View trading performance\n"
            "/stop - Stop the bot\n"
            "/restart - Restart the bot\n"
            "/diagnostics - System diagnostics"
        )
        await update.message.reply_text(welcome_message)
        
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        await self._start_command(update, context)
        
    async def _status_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /status command."""
        try:
            # Get bot status from trading bot instance
            status = "🟢 Bot is running\n"
            status += "Active strategies:\n"
            # TODO: Add active strategies
            status += "No active strategies"
            
            await update.message.reply_text(status)
            
        except Exception as e:
            logger.error(f"Error in status command: {e}")
            await update.message.reply_text("❌ Error getting bot status")
            
    async def _positions_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /positions command."""
        try:
            # Get positions from position manager
            positions = "📊 Open Positions:\n"
            # TODO: Add positions
            positions += "No open positions"
            
            await update.message.reply_text(positions)
            
        except Exception as e:
            logger.error(f"Error in positions command: {e}")
            await update.message.reply_text("❌ Error getting positions")
            
    async def _balance_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /balance command."""
        try:
            # Get balance from broker
            balance = "💰 Account Balance:\n"
            # TODO: Add balance
            balance += "Balance not available"
            
            await update.message.reply_text(balance)
            
        except Exception as e:
            logger.error(f"Error in balance command: {e}")
            await update.message.reply_text("❌ Error getting balance")
            
    async def _performance_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /performance command."""
        try:
            # Get performance metrics
            performance = "📈 Trading Performance:\n"
            # TODO: Add performance metrics
            performance += "Performance data not available"
            
            await update.message.reply_text(performance)
            
        except Exception as e:
            logger.error(f"Error in performance command: {e}")
            await update.message.reply_text("❌ Error getting performance data")
            
    async def _stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /stop command."""
        try:
            await update.message.reply_text("🛑 Stopping trading bot...")
            # TODO: Implement stop logic
            
        except Exception as e:
            logger.error(f"Error in stop command: {e}")
            await update.message.reply_text("❌ Error stopping bot")
            
    async def _restart_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /restart command."""
        try:
            await update.message.reply_text("🔄 Restarting trading bot...")
            # TODO: Implement restart logic
            
        except Exception as e:
            logger.error(f"Error in restart command: {e}")
            await update.message.reply_text("❌ Error restarting bot")
            
    async def _diagnostics_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /diagnostics command."""
        try:
            # Get system diagnostics
            diagnostics = "🔍 System Diagnostics:\n"
            # TODO: Add system metrics
            diagnostics += "Diagnostic data not available"
            
            await update.message.reply_text(diagnostics)
            
        except Exception as e:
            logger.error(f"Error in diagnostics command: {e}")
            await update.message.reply_text("❌ Error getting diagnostics")
            
    async def _error_handler(
        self,
        update: object,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle errors in command processing."""
        logger.error(f"Error handling update: {context.error}")
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred while processing your command"
            ) 