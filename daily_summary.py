#!/usr/bin/env python3
"""
Daily Summary Module

This module generates and sends a daily summary of trading activity at the end of each trading day.
It includes trade performance, active positions, and market insights.
"""

import os
import sys
import logging
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import argparse
import time
import schedule
from dotenv import load_dotenv

# Import our check_trades module
from check_trades import (
    load_trade_history, 
    check_trades_today, 
    check_active_positions,
    format_trade_summary,
    format_positions_summary
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("daily_summary.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
# Also try to load from .env.new
load_dotenv('.env.new')

class DailySummary:
    """
    Daily Summary class for generating and sending end-of-day trading reports.
    """
    
    def __init__(self):
        """Initialize the daily summary module"""
        self.email_enabled = False
        self.telegram_enabled = False
        
        # Load email settings
        self.email_sender = os.getenv('EMAIL_SENDER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.email_recipient = os.getenv('EMAIL_RECIPIENT')
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        
        if self.email_sender and self.email_password and self.email_recipient:
            self.email_enabled = True
            logger.info("Email notifications enabled")
        else:
            logger.warning("Email notifications disabled: Missing email configuration")
        
        # Load Telegram settings from environment variables
        env_token = os.getenv('TELEGRAM_BOT_TOKEN')
        env_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # Use environment variables if they exist and are not default values
        # Otherwise, fall back to hardcoded values
        if env_token and env_chat_id and not env_token.startswith('your_'):
            self.telegram_bot_token = env_token
            self.telegram_chat_id = env_chat_id
            logger.info("Using Telegram credentials from environment variables")
        else:
            # Fallback to hardcoded values
            self.telegram_bot_token = "8078241360:AAE3KoFYSUhV7uKSDaTBuWuCWtTRHkw4dyk"
            self.telegram_chat_id = "7924393886"
            logger.info("Using hardcoded Telegram credentials (fallback)")
        
        # Validate the Telegram token
        if self._validate_telegram_token():
            self.telegram_enabled = True
            logger.info("Telegram notifications enabled")
        else:
            self.telegram_enabled = False
            logger.warning("Telegram notifications disabled: Invalid bot token")
            logger.warning("Please create a new bot with @BotFather and update your .env file")
        
        # Create directories if they don't exist
        os.makedirs('data', exist_ok=True)
        os.makedirs('reports', exist_ok=True)
    
    def _validate_telegram_token(self):
        """
        Validate the Telegram bot token
        
        Returns:
            Boolean indicating if the token is valid
        """
        try:
            import requests
            
            # Telegram API URL for getMe
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/getMe"
            
            # Log the request details (without the full token for security)
            token_prefix = self.telegram_bot_token[:5] if len(self.telegram_bot_token) > 10 else "****"
            token_suffix = self.telegram_bot_token[-5:] if len(self.telegram_bot_token) > 10 else "****"
            logger.info(f"Validating Telegram bot token: {token_prefix}...{token_suffix}")
            
            # Send request
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get('ok', False):
                    bot_name = bot_info.get('result', {}).get('first_name', 'Unknown')
                    bot_username = bot_info.get('result', {}).get('username', 'Unknown')
                    logger.info(f"Telegram bot validated: {bot_name} (@{bot_username})")
                    return True
            
            # Log error details
            error_data = response.json() if response.text else {"error": "No response body"}
            logger.error(f"Error validating Telegram bot token: {response.status_code} - {response.reason}")
            logger.error(f"Error details: {error_data}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error validating Telegram bot token: {e}")
            return False
    
    def generate_daily_summary(self):
        """
        Generate a daily summary of trading activity
        
        Returns:
            Tuple of (summary_text, summary_html, charts)
        """
        try:
            # Get today's date
            today = datetime.now().date()
            
            # Load trade history
            trade_history = load_trade_history()
            
            # Check today's trades
            today_trades = check_trades_today(trade_history)
            
            # Check active positions
            positions = check_active_positions()
            
            # Generate summary text
            summary_text = f"KryptoBot Daily Summary - {today}\n\n"
            
            if today_trades.empty:
                summary_text += "No trades were executed today.\n\n"
            else:
                summary_text += f"The bot executed {len(today_trades)} trades today.\n\n"
                summary_text += format_trade_summary(today_trades) + "\n"
            
            summary_text += "Active Positions:\n"
            summary_text += format_positions_summary(positions) + "\n"
            
            # Generate performance metrics
            if not trade_history.empty:
                # Calculate daily P&L
                trade_history['date'] = trade_history['timestamp'].dt.date
                daily_pnl = trade_history.groupby('date')['profit'].sum()
                
                # Calculate cumulative P&L
                cumulative_pnl = daily_pnl.cumsum()
                
                # Calculate win rate
                win_rate = len(trade_history[trade_history['profit'] > 0]) / len(trade_history) * 100
                
                # Calculate Sharpe ratio (simplified)
                if len(daily_pnl) > 1:
                    sharpe_ratio = daily_pnl.mean() / daily_pnl.std() * np.sqrt(252)
                else:
                    sharpe_ratio = 0
                
                # Add performance metrics to summary
                summary_text += "Performance Metrics:\n"
                summary_text += f"  Total P&L: ${cumulative_pnl.iloc[-1]:.2f}\n"
                summary_text += f"  Win Rate: {win_rate:.2f}%\n"
                summary_text += f"  Sharpe Ratio: {sharpe_ratio:.2f}\n"
                
                # Generate charts
                charts = self._generate_performance_charts(daily_pnl, cumulative_pnl)
            else:
                charts = []
            
            # Generate HTML version
            summary_html = self._generate_html_summary(
                today, today_trades, positions, 
                trade_history, len(charts) > 0
            )
            
            return summary_text, summary_html, charts
            
        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
            return f"Error generating daily summary: {e}", "", []
    
    def _generate_performance_charts(self, daily_pnl, cumulative_pnl):
        """
        Generate performance charts
        
        Args:
            daily_pnl: Series with daily P&L
            cumulative_pnl: Series with cumulative P&L
            
        Returns:
            List of chart file paths
        """
        charts = []
        
        try:
            # Daily P&L chart
            plt.figure(figsize=(10, 6))
            daily_pnl.plot(kind='bar', color=daily_pnl.apply(lambda x: 'green' if x > 0 else 'red'))
            plt.title('Daily Profit/Loss')
            plt.xlabel('Date')
            plt.ylabel('Profit/Loss ($)')
            plt.tight_layout()
            
            # Save chart
            daily_chart_path = 'reports/daily_pnl.png'
            plt.savefig(daily_chart_path)
            plt.close()
            
            charts.append(daily_chart_path)
            
            # Cumulative P&L chart
            plt.figure(figsize=(10, 6))
            cumulative_pnl.plot()
            plt.title('Cumulative Profit/Loss')
            plt.xlabel('Date')
            plt.ylabel('Cumulative Profit/Loss ($)')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Save chart
            cumulative_chart_path = 'reports/cumulative_pnl.png'
            plt.savefig(cumulative_chart_path)
            plt.close()
            
            charts.append(cumulative_chart_path)
            
        except Exception as e:
            logger.error(f"Error generating performance charts: {e}")
        
        return charts
    
    def _generate_html_summary(self, today, today_trades, positions, trade_history, has_charts):
        """
        Generate HTML version of the summary
        
        Args:
            today: Today's date
            today_trades: DataFrame with today's trades
            positions: Dictionary with active positions
            trade_history: DataFrame with trade history
            has_charts: Boolean indicating if charts are available
            
        Returns:
            HTML string
        """
        try:
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>KryptoBot Daily Summary - {today}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1, h2 {{ color: #333366; }}
                    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    .profit {{ color: green; }}
                    .loss {{ color: red; }}
                    .chart {{ margin: 20px 0; max-width: 100%; }}
                </style>
            </head>
            <body>
                <h1>KryptoBot Daily Summary - {today}</h1>
            """
            
            # Today's trades
            html += "<h2>Today's Trades</h2>"
            if today_trades.empty:
                html += "<p>No trades were executed today.</p>"
            else:
                html += f"<p>The bot executed {len(today_trades)} trades today.</p>"
                html += "<table>"
                html += "<tr><th>Time</th><th>Symbol</th><th>Side</th><th>Quantity</th><th>Entry Price</th><th>Exit Price</th><th>Profit/Loss</th><th>Strategy</th></tr>"
                
                for _, trade in today_trades.iterrows():
                    timestamp = trade.get('timestamp', 'Unknown')
                    symbol = trade.get('symbol', 'Unknown')
                    side = trade.get('side', 'Unknown')
                    quantity = trade.get('quantity', 0)
                    entry_price = trade.get('entry_price', 0)
                    exit_price = trade.get('exit_price', 0)
                    profit = trade.get('profit', 0)
                    strategy = trade.get('strategy', 'Unknown')
                    
                    profit_class = "profit" if profit > 0 else "loss" if profit < 0 else ""
                    
                    html += f"<tr>"
                    html += f"<td>{timestamp}</td>"
                    html += f"<td>{symbol}</td>"
                    html += f"<td>{side.upper()}</td>"
                    html += f"<td>{quantity}</td>"
                    html += f"<td>${entry_price:.2f}</td>"
                    html += f"<td>${exit_price:.2f}</td>"
                    html += f"<td class='{profit_class}'>${profit:.2f}</td>"
                    html += f"<td>{strategy}</td>"
                    html += f"</tr>"
                
                html += "</table>"
                
                # Trade summary
                if 'profit' in today_trades.columns:
                    total_profit = today_trades['profit'].sum()
                    profitable_trades = len(today_trades[today_trades['profit'] > 0])
                    losing_trades = len(today_trades[today_trades['profit'] < 0])
                    
                    html += "<h3>Today's Summary</h3>"
                    html += "<table>"
                    html += f"<tr><td>Total Trades</td><td>{len(today_trades)}</td></tr>"
                    html += f"<tr><td>Profitable Trades</td><td>{profitable_trades}</td></tr>"
                    html += f"<tr><td>Losing Trades</td><td>{losing_trades}</td></tr>"
                    html += f"<tr><td>Total Profit/Loss</td><td class='{('profit' if total_profit > 0 else 'loss' if total_profit < 0 else '')}'>${total_profit:.2f}</td></tr>"
                    html += "</table>"
            
            # Active positions
            html += "<h2>Active Positions</h2>"
            if not positions:
                html += "<p>No active positions.</p>"
            else:
                html += "<table>"
                html += "<tr><th>Symbol</th><th>Side</th><th>Quantity</th><th>Entry Price</th><th>Current Price</th><th>Unrealized P/L</th><th>Strategy</th></tr>"
                
                for symbol, position in positions.items():
                    side = position.get('side', 'Unknown')
                    quantity = position.get('quantity', 0)
                    entry_price = position.get('entry_price', 0)
                    current_price = position.get('current_price', 0)
                    unrealized_profit = position.get('unrealized_profit', 0)
                    strategy = position.get('strategy', 'Unknown')
                    
                    profit_class = "profit" if unrealized_profit > 0 else "loss" if unrealized_profit < 0 else ""
                    
                    html += f"<tr>"
                    html += f"<td>{symbol}</td>"
                    html += f"<td>{side.upper()}</td>"
                    html += f"<td>{quantity}</td>"
                    html += f"<td>${entry_price:.2f}</td>"
                    html += f"<td>${current_price:.2f}</td>"
                    html += f"<td class='{profit_class}'>${unrealized_profit:.2f}</td>"
                    html += f"<td>{strategy}</td>"
                    html += f"</tr>"
                
                html += "</table>"
            
            # Performance metrics
            if not trade_history.empty:
                # Calculate metrics
                trade_history['date'] = trade_history['timestamp'].dt.date
                daily_pnl = trade_history.groupby('date')['profit'].sum()
                cumulative_pnl = daily_pnl.cumsum()
                win_rate = len(trade_history[trade_history['profit'] > 0]) / len(trade_history) * 100
                
                # Calculate Sharpe ratio (simplified)
                if len(daily_pnl) > 1:
                    sharpe_ratio = daily_pnl.mean() / daily_pnl.std() * np.sqrt(252)
                else:
                    sharpe_ratio = 0
                
                html += "<h2>Performance Metrics</h2>"
                html += "<table>"
                html += f"<tr><td>Total P&L</td><td class='{('profit' if cumulative_pnl.iloc[-1] > 0 else 'loss' if cumulative_pnl.iloc[-1] < 0 else '')}'>${cumulative_pnl.iloc[-1]:.2f}</td></tr>"
                html += f"<tr><td>Win Rate</td><td>{win_rate:.2f}%</td></tr>"
                html += f"<tr><td>Sharpe Ratio</td><td>{sharpe_ratio:.2f}</td></tr>"
                html += "</table>"
                
                # Charts
                if has_charts:
                    html += "<h2>Performance Charts</h2>"
                    html += "<p>See attached charts for daily and cumulative P&L.</p>"
            
            html += """
            </body>
            </html>
            """
            
            return html
            
        except Exception as e:
            logger.error(f"Error generating HTML summary: {e}")
            return f"<html><body><h1>Error</h1><p>Error generating HTML summary: {e}</p></body></html>"
    
    def send_email_summary(self, summary_text, summary_html, charts):
        """
        Send summary via email
        
        Args:
            summary_text: Plain text summary
            summary_html: HTML summary
            charts: List of chart file paths
        """
        if not self.email_enabled:
            logger.warning("Email notifications disabled")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"KryptoBot Daily Summary - {datetime.now().date()}"
            msg['From'] = self.email_sender
            msg['To'] = self.email_recipient
            
            # Attach text and HTML versions
            msg.attach(MIMEText(summary_text, 'plain'))
            msg.attach(MIMEText(summary_html, 'html'))
            
            # Attach charts
            for chart_path in charts:
                with open(chart_path, 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-ID', f'<{os.path.basename(chart_path)}>')
                    img.add_header('Content-Disposition', 'inline', filename=os.path.basename(chart_path))
                    msg.attach(img)
            
            # Connect to SMTP server and send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_sender, self.email_password)
                server.send_message(msg)
            
            logger.info(f"Daily summary email sent to {self.email_recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email summary: {e}")
            return False
    
    def send_telegram_summary(self, summary_text):
        """
        Send summary via Telegram
        
        Args:
            summary_text: Plain text summary
        """
        if not self.telegram_enabled:
            logger.warning("Telegram notifications disabled")
            return False
        
        try:
            import requests
            
            # Telegram API URL
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            
            # Prepare message
            data = {
                "chat_id": self.telegram_chat_id,
                "text": summary_text
            }
            
            # Log the request details (without the full token for security)
            token_prefix = self.telegram_bot_token[:5] if len(self.telegram_bot_token) > 10 else "****"
            token_suffix = self.telegram_bot_token[-5:] if len(self.telegram_bot_token) > 10 else "****"
            logger.info(f"Sending Telegram message to chat ID: {self.telegram_chat_id}")
            logger.info(f"Using bot token: {token_prefix}...{token_suffix}")
            
            # Send message
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                logger.info("Daily summary sent via Telegram")
                
                # Send charts if available
                charts_dir = 'reports'
                for chart_file in os.listdir(charts_dir):
                    if chart_file.endswith('.png'):
                        chart_path = os.path.join(charts_dir, chart_file)
                        self._send_telegram_photo(chart_path)
                
                return True
            else:
                # Log detailed error information
                error_data = response.json() if response.text else {"error": "No response body"}
                logger.error(f"Error sending Telegram message: {response.status_code} - {response.reason}")
                logger.error(f"Error details: {error_data}")
                
                # Provide troubleshooting information based on error code
                if response.status_code == 401:
                    logger.error("Unauthorized error: The bot token is invalid or has been revoked.")
                    logger.error("Please create a new bot with @BotFather and update your .env file.")
                elif response.status_code == 400:
                    logger.error("Bad request: Check if the chat_id is correct.")
                elif response.status_code == 404:
                    logger.error("Not found: The API endpoint or method is incorrect.")
                
                return False
            
        except Exception as e:
            logger.error(f"Error sending Telegram summary: {e}")
            return False
    
    def _send_telegram_photo(self, photo_path):
        """
        Send photo via Telegram
        
        Args:
            photo_path: Path to photo file
        """
        try:
            import requests
            
            # Telegram API URL
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendPhoto"
            
            # Prepare files and data
            files = {
                "photo": open(photo_path, "rb")
            }
            
            data = {
                "chat_id": self.telegram_chat_id
            }
            
            # Send photo
            response = requests.post(url, files=files, data=data)
            
            if response.status_code == 200:
                logger.info(f"Chart sent via Telegram: {photo_path}")
                return True
            else:
                logger.error(f"Error sending Telegram photo: {response.text}")
                return False
            
        except Exception as e:
            logger.error(f"Error sending Telegram photo: {e}")
            return False
    
    def save_summary_to_file(self, summary_text, summary_html):
        """
        Save summary to file
        
        Args:
            summary_text: Plain text summary
            summary_html: HTML summary
        """
        try:
            # Create reports directory if it doesn't exist
            os.makedirs('reports', exist_ok=True)
            
            # Get today's date
            today = datetime.now().date()
            
            # Save text summary
            text_path = f'reports/summary_{today}.txt'
            with open(text_path, 'w') as f:
                f.write(summary_text)
            
            # Save HTML summary
            html_path = f'reports/summary_{today}.html'
            with open(html_path, 'w') as f:
                f.write(summary_html)
            
            logger.info(f"Summary saved to {text_path} and {html_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving summary to file: {e}")
            return False
    
    def run_daily_summary(self):
        """Run the daily summary process"""
        try:
            logger.info("Generating daily summary...")
            
            # Generate summary
            summary_text, summary_html, charts = self.generate_daily_summary()
            
            # Save summary to file
            self.save_summary_to_file(summary_text, summary_html)
            
            # Send summary via email
            if self.email_enabled:
                self.send_email_summary(summary_text, summary_html, charts)
            
            # Send summary via Telegram
            if self.telegram_enabled:
                self.send_telegram_summary(summary_text)
            
            logger.info("Daily summary completed")
            return True
            
        except Exception as e:
            logger.error(f"Error running daily summary: {e}")
            return False
    
    def schedule_daily_summary(self, time="16:00"):
        """
        Schedule daily summary to run at specified time
        
        Args:
            time: Time to run daily summary (HH:MM format)
        """
        try:
            # Schedule daily summary
            schedule.every().monday.at(time).do(self.run_daily_summary)
            schedule.every().tuesday.at(time).do(self.run_daily_summary)
            schedule.every().wednesday.at(time).do(self.run_daily_summary)
            schedule.every().thursday.at(time).do(self.run_daily_summary)
            schedule.every().friday.at(time).do(self.run_daily_summary)
            
            logger.info(f"Daily summary scheduled to run at {time}")
            
            # Run the scheduler
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except Exception as e:
            logger.error(f"Error scheduling daily summary: {e}")
            return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Generate and send daily trading summary')
    parser.add_argument('--now', action='store_true', help='Generate and send summary now')
    parser.add_argument('--schedule', type=str, default="16:00", help='Schedule time for daily summary (HH:MM format)')
    args = parser.parse_args()
    
    try:
        # Create daily summary instance
        daily_summary = DailySummary()
        
        if args.now:
            # Generate and send summary now
            daily_summary.run_daily_summary()
        else:
            # Schedule daily summary
            daily_summary.schedule_daily_summary(args.schedule)
            
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 