"""
Notifications Module - Handles sending notifications to users.

This module is responsible for sending notifications to users through
various channels such as email, SMS, and Slack.
"""

import os
import logging
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class NotificationChannel:
    """
    Base class for notification channels.
    
    This class defines the interface for notification channels.
    Concrete notification channels should inherit from this class
    and implement the send method.
    """
    
    def __init__(self, name: str):
        """
        Initialize the notification channel.
        
        Args:
            name (str): Name of the notification channel
        """
        self.name = name
        self.enabled = True
    
    def send(self, subject: str, message: str) -> bool:
        """
        Send a notification.
        
        Args:
            subject (str): Notification subject
            message (str): Notification message
            
        Returns:
            bool: True if the notification was sent successfully, False otherwise
        """
        raise NotImplementedError("Subclasses must implement send method")
    
    def enable(self):
        """Enable the notification channel."""
        self.enabled = True
    
    def disable(self):
        """Disable the notification channel."""
        self.enabled = False
    
    def is_enabled(self) -> bool:
        """
        Check if the notification channel is enabled.
        
        Returns:
            bool: True if the notification channel is enabled, False otherwise
        """
        return self.enabled

class EmailNotificationChannel(NotificationChannel):
    """
    Email notification channel.
    
    This class implements the NotificationChannel interface for sending
    notifications via email.
    
    Attributes:
        smtp_server (str): SMTP server address
        smtp_port (int): SMTP server port
        smtp_username (str): SMTP username
        smtp_password (str): SMTP password
        sender_email (str): Sender email address
        recipient_emails (List[str]): Recipient email addresses
    """
    
    def __init__(self, smtp_server: str, smtp_port: int, smtp_username: str,
                smtp_password: str, sender_email: str, recipient_emails: List[str]):
        """
        Initialize the email notification channel.
        
        Args:
            smtp_server (str): SMTP server address
            smtp_port (int): SMTP server port
            smtp_username (str): SMTP username
            smtp_password (str): SMTP password
            sender_email (str): Sender email address
            recipient_emails (List[str]): Recipient email addresses
        """
        super().__init__("Email")
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.sender_email = sender_email
        self.recipient_emails = recipient_emails
    
    def send(self, subject: str, message: str) -> bool:
        """
        Send an email notification.
        
        Args:
            subject (str): Email subject
            message (str): Email message
            
        Returns:
            bool: True if the email was sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info("Email notifications are disabled")
            return False
        
        if not self.recipient_emails:
            logger.warning("No recipient emails configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(self.recipient_emails)
            msg['Subject'] = subject
            
            # Add message body
            msg.attach(MIMEText(message, 'plain'))
            
            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email notification sent to {', '.join(self.recipient_emails)}")
            return True
        
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False

class SlackNotificationChannel(NotificationChannel):
    """
    Slack notification channel.
    
    This class implements the NotificationChannel interface for sending
    notifications via Slack.
    
    Attributes:
        webhook_url (str): Slack webhook URL
        channel (str): Slack channel
        username (str): Slack username
    """
    
    def __init__(self, webhook_url: str, channel: str = None, username: str = "KryptoBot"):
        """
        Initialize the Slack notification channel.
        
        Args:
            webhook_url (str): Slack webhook URL
            channel (str, optional): Slack channel
            username (str, optional): Slack username
        """
        super().__init__("Slack")
        self.webhook_url = webhook_url
        self.channel = channel
        self.username = username
    
    def send(self, subject: str, message: str) -> bool:
        """
        Send a Slack notification.
        
        Args:
            subject (str): Notification subject
            message (str): Notification message
            
        Returns:
            bool: True if the notification was sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info("Slack notifications are disabled")
            return False
        
        try:
            # Create payload
            payload = {
                "text": f"*{subject}*\n{message}",
                "username": self.username
            }
            
            if self.channel:
                payload["channel"] = self.channel
            
            # Send request
            response = requests.post(self.webhook_url, json=payload)
            
            if response.status_code == 200:
                logger.info("Slack notification sent")
                return True
            else:
                logger.warning(f"Error sending Slack notification: {response.status_code} {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            return False

class SMSNotificationChannel(NotificationChannel):
    """
    SMS notification channel.
    
    This class implements the NotificationChannel interface for sending
    notifications via SMS using Twilio.
    
    Attributes:
        account_sid (str): Twilio account SID
        auth_token (str): Twilio auth token
        from_number (str): Twilio phone number
        to_numbers (List[str]): Recipient phone numbers
    """
    
    def __init__(self, account_sid: str, auth_token: str, from_number: str, to_numbers: List[str]):
        """
        Initialize the SMS notification channel.
        
        Args:
            account_sid (str): Twilio account SID
            auth_token (str): Twilio auth token
            from_number (str): Twilio phone number
            to_numbers (List[str]): Recipient phone numbers
        """
        super().__init__("SMS")
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.to_numbers = to_numbers
        
        # Check if Twilio is available
        try:
            import twilio.rest
            self.client = twilio.rest.Client(account_sid, auth_token)
            self.twilio_available = True
        except ImportError:
            logger.warning("Twilio not available. SMS notifications will be disabled.")
            self.twilio_available = False
            self.enabled = False
    
    def send(self, subject: str, message: str) -> bool:
        """
        Send an SMS notification.
        
        Args:
            subject (str): Notification subject
            message (str): Notification message
            
        Returns:
            bool: True if the notification was sent successfully, False otherwise
        """
        if not self.enabled or not self.twilio_available:
            logger.info("SMS notifications are disabled")
            return False
        
        if not self.to_numbers:
            logger.warning("No recipient phone numbers configured")
            return False
        
        try:
            # Create message
            sms_message = f"{subject}\n{message}"
            
            # Send message to each recipient
            for to_number in self.to_numbers:
                self.client.messages.create(
                    body=sms_message,
                    from_=self.from_number,
                    to=to_number
                )
            
            logger.info(f"SMS notification sent to {', '.join(self.to_numbers)}")
            return True
        
        except Exception as e:
            logger.error(f"Error sending SMS notification: {e}")
            return False

class NotificationSystem:
    """
    System for sending notifications through various channels.
    
    This class manages multiple notification channels and provides
    a unified interface for sending notifications.
    
    Attributes:
        channels (Dict[str, NotificationChannel]): Notification channels
        notification_history (List[Dict[str, Any]]): History of sent notifications
    """
    
    def __init__(self):
        """
        Initialize the notification system.
        """
        self.channels = {}
        self.notification_history = []
        
        # Initialize notification channels from environment variables
        self._init_from_env()
        
        logger.info("Notification system initialized")
    
    def _init_from_env(self):
        """
        Initialize notification channels from environment variables.
        """
        # Initialize email notifications
        if os.environ.get('KRYPTOBOT_EMAIL_ENABLED', 'false').lower() == 'true':
            smtp_server = os.environ.get('KRYPTOBOT_EMAIL_SMTP_SERVER')
            smtp_port = int(os.environ.get('KRYPTOBOT_EMAIL_SMTP_PORT', '587'))
            smtp_username = os.environ.get('KRYPTOBOT_EMAIL_SMTP_USERNAME')
            smtp_password = os.environ.get('KRYPTOBOT_EMAIL_SMTP_PASSWORD')
            sender_email = os.environ.get('KRYPTOBOT_EMAIL_SENDER')
            recipient_emails = os.environ.get('KRYPTOBOT_EMAIL_RECIPIENTS', '').split(',')
            
            if smtp_server and smtp_username and smtp_password and sender_email and recipient_emails:
                self.add_channel(EmailNotificationChannel(
                    smtp_server, smtp_port, smtp_username, smtp_password,
                    sender_email, recipient_emails
                ))
                logger.info("Email notifications enabled")
        
        # Initialize Slack notifications
        if os.environ.get('KRYPTOBOT_SLACK_ENABLED', 'false').lower() == 'true':
            webhook_url = os.environ.get('KRYPTOBOT_SLACK_WEBHOOK_URL')
            channel = os.environ.get('KRYPTOBOT_SLACK_CHANNEL')
            username = os.environ.get('KRYPTOBOT_SLACK_USERNAME', 'KryptoBot')
            
            if webhook_url:
                self.add_channel(SlackNotificationChannel(
                    webhook_url, channel, username
                ))
                logger.info("Slack notifications enabled")
        
        # Initialize SMS notifications
        if os.environ.get('KRYPTOBOT_SMS_ENABLED', 'false').lower() == 'true':
            account_sid = os.environ.get('KRYPTOBOT_SMS_ACCOUNT_SID')
            auth_token = os.environ.get('KRYPTOBOT_SMS_AUTH_TOKEN')
            from_number = os.environ.get('KRYPTOBOT_SMS_FROM_NUMBER')
            to_numbers = os.environ.get('KRYPTOBOT_SMS_TO_NUMBERS', '').split(',')
            
            if account_sid and auth_token and from_number and to_numbers:
                self.add_channel(SMSNotificationChannel(
                    account_sid, auth_token, from_number, to_numbers
                ))
                logger.info("SMS notifications enabled")
    
    def add_channel(self, channel: NotificationChannel):
        """
        Add a notification channel.
        
        Args:
            channel (NotificationChannel): Notification channel to add
        """
        self.channels[channel.name] = channel
        logger.info(f"Added notification channel: {channel.name}")
    
    def remove_channel(self, channel_name: str):
        """
        Remove a notification channel.
        
        Args:
            channel_name (str): Name of the notification channel to remove
        """
        if channel_name in self.channels:
            del self.channels[channel_name]
            logger.info(f"Removed notification channel: {channel_name}")
    
    def enable_channel(self, channel_name: str):
        """
        Enable a notification channel.
        
        Args:
            channel_name (str): Name of the notification channel to enable
        """
        if channel_name in self.channels:
            self.channels[channel_name].enable()
            logger.info(f"Enabled notification channel: {channel_name}")
    
    def disable_channel(self, channel_name: str):
        """
        Disable a notification channel.
        
        Args:
            channel_name (str): Name of the notification channel to disable
        """
        if channel_name in self.channels:
            self.channels[channel_name].disable()
            logger.info(f"Disabled notification channel: {channel_name}")
    
    def send_notification(self, subject: str, message: str, channels: List[str] = None) -> bool:
        """
        Send a notification through all enabled channels.
        
        Args:
            subject (str): Notification subject
            message (str): Notification message
            channels (List[str], optional): List of channel names to use.
                If None, all enabled channels will be used.
            
        Returns:
            bool: True if the notification was sent through at least one channel,
                False otherwise
        """
        if not self.channels:
            logger.warning("No notification channels configured")
            return False
        
        # Determine which channels to use
        if channels:
            channels_to_use = {name: channel for name, channel in self.channels.items() if name in channels}
        else:
            channels_to_use = self.channels
        
        # Send notification through each channel
        success = False
        for name, channel in channels_to_use.items():
            if channel.is_enabled():
                if channel.send(subject, message):
                    success = True
        
        # Record notification in history
        self.notification_history.append({
            'timestamp': datetime.now(),
            'subject': subject,
            'message': message,
            'success': success
        })
        
        return success
    
    def get_notification_history(self) -> List[Dict[str, Any]]:
        """
        Get the notification history.
        
        Returns:
            List[Dict[str, Any]]: List of notification history entries
        """
        return self.notification_history
    
    def clear_notification_history(self):
        """
        Clear the notification history.
        """
        self.notification_history = []
        logger.info("Notification history cleared") 