import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class NotificationSystem:
    def __init__(self):
        """Initialize the notification system"""
        load_dotenv()
        self.sender_email = os.getenv('EMAIL_ADDRESS')
        self.sender_password = os.getenv('EMAIL_PASSWORD')
        self.recipient_email = os.getenv('NOTIFICATION_EMAIL')
        
        # Check if email is configured
        self.email_configured = (
            self.sender_email is not None and
            self.sender_password is not None and
            self.recipient_email is not None
        )
        
        if not self.email_configured:
            logger.warning("Email notifications not configured. Set EMAIL_ADDRESS, EMAIL_PASSWORD, and NOTIFICATION_EMAIL in .env file.")
        else:
            logger.info(f"Email notifications configured for {self.recipient_email}")
        
    def send_email(self, subject: str, body: str):
        """Send email notification"""
        if not self.email_configured:
            logger.warning("Email notifications not configured. Skipping email.")
            return
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = f"KryptoBot: {subject}"
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to Gmail's SMTP server
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email notification sent: {subject}")
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
            
    def trade_executed(self, symbol: str, side: str, quantity: int, price: float, trade_type: str):
        """Send trade execution notification"""
        subject = f"Trade Executed: {symbol}"
        body = f"""
Trade Details:
-------------
Symbol: {symbol}
Side: {side}
Quantity: {quantity}
Price: ${price:.2f}
Type: {trade_type}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        self.send_email(subject, body)
        logger.info(f"Trade notification sent for {symbol}")
        
    def position_closed(self, symbol: str, profit_loss: float, roi: float):
        """Send position closed notification"""
        subject = f"Position Closed: {symbol}"
        body = f"""
Position Closed:
---------------
Symbol: {symbol}
Profit/Loss: ${profit_loss:.2f}
ROI: {roi:.2f}%
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        self.send_email(subject, body)
        logger.info(f"Position closed notification sent for {symbol}")
        
    def daily_summary(self, total_trades: int, win_rate: float, total_pl: float):
        """Send daily trading summary"""
        subject = "Daily Trading Summary"
        body = f"""
Daily Summary:
-------------
Date: {datetime.now().strftime('%Y-%m-%d')}
Total Trades: {total_trades}
Win Rate: {win_rate:.2f}%
Total P/L: ${total_pl:.2f}
        """
        self.send_email(subject, body)
        logger.info("Daily summary notification sent")
        
    def alert(self, message: str, priority: str = "INFO"):
        """Send general alert"""
        subject = f"{priority} Alert"
        body = f"""
Alert Details:
-------------
Priority: {priority}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Message: {message}
        """
        self.send_email(subject, body)
        logger.info(f"Alert notification sent: {priority} - {message}")
        
    def send_performance_report(self, report: dict):
        """Send performance report"""
        subject = "Performance Report"
        
        # Extract key metrics
        metrics = report.get('summary', {})
        suggestions = report.get('suggestions', [])
        
        body = f"""
Performance Report:
------------------
Date: {datetime.now().strftime('%Y-%m-%d')}

Key Metrics:
- Total Trades: {metrics.get('total_trades', 0)}
- Win Rate: {metrics.get('win_rate', 0):.2f}%
- Profit Factor: {metrics.get('profit_factor', 0):.2f}
- Total Profit: ${metrics.get('total_profit', 0):.2f}
- Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}
- Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%

Improvement Suggestions:
"""
        
        if suggestions:
            for suggestion in suggestions:
                body += f"- {suggestion['area']} ({suggestion['priority']}): {suggestion['suggestion']}\n"
                body += f"  Current: {suggestion['current']}, Target: {suggestion['target']}\n"
        else:
            body += "- No suggestions at this time\n"
            
        self.send_email(subject, body)
        logger.info("Performance report notification sent") 