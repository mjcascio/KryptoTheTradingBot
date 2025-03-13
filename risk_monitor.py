#!/usr/bin/env python3
"""
Risk Monitor for KryptoBot

This module monitors trading activity and verifies that risk parameters
are being followed in real-time for both paper and live trading.
"""

import os
import json
import logging
import time
import threading
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv

# Import local modules
try:
    from strategy_manager import StrategyManager
    from telegram_notifications import send_telegram_message
except ImportError:
    # For standalone testing
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/risk_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
EST_TIMEZONE = pytz.timezone('US/Eastern')
RISK_CHECK_INTERVAL = 60  # seconds
MAX_POSITION_SIZE_PCT = 0.05  # 5% of portfolio
MAX_TOTAL_RISK_PCT = 0.20  # 20% of portfolio
MAX_DRAWDOWN_PCT = 0.10  # 10% max drawdown
STOP_LOSS_REQUIRED = True  # Require stop loss for all positions
RISK_REWARD_MIN = 2.0  # Minimum risk/reward ratio

class RiskMonitor:
    """
    Class for monitoring trading risk parameters in real-time.
    """
    
    def __init__(self, api, is_paper=True):
        """
        Initialize the risk monitor.
        
        Args:
            api: The trading API instance (Alpaca)
            is_paper: Whether this is paper trading
        """
        self.api = api
        self.is_paper = is_paper
        self.strategy_manager = StrategyManager()
        self.monitoring_active = False
        self.monitoring_thread = None
        self.last_check_time = None
        self.portfolio_history = []
        self.risk_violations = []
        self.max_portfolio_value = 0
        self.current_drawdown = 0
        
        # Load risk parameters from strategy
        self.load_risk_parameters()
        
        logger.info(f"Risk monitor initialized (Paper: {is_paper})")
    
    def load_risk_parameters(self):
        """Load risk parameters from the current strategy."""
        try:
            current_strategy = self.strategy_manager.get_current_strategy()
            
            # Set risk parameters from strategy
            self.max_position_size_pct = current_strategy.get('max_position_size_pct', MAX_POSITION_SIZE_PCT)
            self.max_total_risk_pct = current_strategy.get('max_total_risk_pct', MAX_TOTAL_RISK_PCT)
            self.max_drawdown_pct = current_strategy.get('max_drawdown_pct', MAX_DRAWDOWN_PCT)
            self.stop_loss_required = current_strategy.get('stop_loss_required', STOP_LOSS_REQUIRED)
            self.risk_reward_min = current_strategy.get('risk_reward_min', RISK_REWARD_MIN)
            
            logger.info(f"Loaded risk parameters from strategy: {current_strategy.get('name', 'Unknown')}")
            logger.info(f"Max position size: {self.max_position_size_pct*100}%")
            logger.info(f"Max total risk: {self.max_total_risk_pct*100}%")
            logger.info(f"Max drawdown: {self.max_drawdown_pct*100}%")
            logger.info(f"Stop loss required: {self.stop_loss_required}")
            logger.info(f"Min risk/reward ratio: {self.risk_reward_min}")
        
        except Exception as e:
            logger.error(f"Error loading risk parameters: {e}")
            # Use default values
            self.max_position_size_pct = MAX_POSITION_SIZE_PCT
            self.max_total_risk_pct = MAX_TOTAL_RISK_PCT
            self.max_drawdown_pct = MAX_DRAWDOWN_PCT
            self.stop_loss_required = STOP_LOSS_REQUIRED
            self.risk_reward_min = RISK_REWARD_MIN
    
    def start_monitoring(self, check_interval=RISK_CHECK_INTERVAL):
        """
        Start monitoring risk parameters.
        
        Args:
            check_interval: Interval in seconds between checks
        """
        if self.monitoring_active:
            logger.warning("Risk monitoring is already active")
            return
        
        self.monitoring_active = True
        self.last_check_time = datetime.now(EST_TIMEZONE)
        
        def monitoring_thread_func():
            logger.info("Starting risk monitoring thread")
            
            while self.monitoring_active:
                try:
                    # Check risk parameters
                    violations = self.check_risk_parameters()
                    
                    # Handle violations
                    if violations:
                        self.handle_risk_violations(violations)
                    
                    # Update portfolio history
                    self.update_portfolio_history()
                    
                    # Check for strategy changes
                    if self.strategy_manager.should_update_strategy():
                        self.load_risk_parameters()
                
                except Exception as e:
                    logger.error(f"Error in risk monitoring thread: {e}")
                
                # Sleep before next check
                time.sleep(check_interval)
            
            logger.info("Risk monitoring thread stopped")
        
        # Start the monitoring thread
        self.monitoring_thread = threading.Thread(target=monitoring_thread_func)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        logger.info(f"Started risk monitoring with interval {check_interval}s")
    
    def stop_monitoring(self):
        """Stop monitoring risk parameters."""
        if not self.monitoring_active:
            logger.warning("Risk monitoring is not active")
            return
        
        self.monitoring_active = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
            self.monitoring_thread = None
        
        logger.info("Stopped risk monitoring")
    
    def check_risk_parameters(self) -> List[Dict[str, Any]]:
        """
        Check all risk parameters.
        
        Returns:
            List of risk violations
        """
        violations = []
        
        try:
            # Get account information
            account = self.api.get_account()
            portfolio_value = float(account.portfolio_value)
            buying_power = float(account.buying_power)
            
            # Update max portfolio value
            if portfolio_value > self.max_portfolio_value:
                self.max_portfolio_value = portfolio_value
            
            # Calculate current drawdown
            if self.max_portfolio_value > 0:
                self.current_drawdown = (self.max_portfolio_value - portfolio_value) / self.max_portfolio_value
            
            # Check drawdown
            if self.current_drawdown > self.max_drawdown_pct:
                violations.append({
                    'type': 'drawdown',
                    'severity': 'high',
                    'message': f"Maximum drawdown exceeded: {self.current_drawdown*100:.2f}% > {self.max_drawdown_pct*100:.2f}%",
                    'timestamp': datetime.now(EST_TIMEZONE)
                })
            
            # Get positions
            positions = self.api.list_positions()
            
            # Check position sizes and stop losses
            total_position_value = 0
            total_at_risk = 0
            
            for position in positions:
                symbol = position.symbol
                qty = float(position.qty)
                market_value = float(position.market_value)
                entry_price = float(position.avg_entry_price)
                current_price = float(position.current_price)
                
                # Calculate position size as percentage of portfolio
                position_size_pct = market_value / portfolio_value
                
                # Check if position size exceeds maximum
                if position_size_pct > self.max_position_size_pct:
                    violations.append({
                        'type': 'position_size',
                        'severity': 'medium',
                        'message': f"Position size for {symbol} exceeds maximum: {position_size_pct*100:.2f}% > {self.max_position_size_pct*100:.2f}%",
                        'symbol': symbol,
                        'timestamp': datetime.now(EST_TIMEZONE)
                    })
                
                # Add to total position value
                total_position_value += market_value
                
                # Check for stop loss orders
                if self.stop_loss_required:
                    try:
                        # Get open orders for this symbol
                        orders = self.api.list_orders(
                            status='open',
                            side='sell' if float(position.qty) > 0 else 'buy',
                            symbols=[symbol]
                        )
                        
                        # Check if there's a stop loss order
                        has_stop_loss = any(order.type == 'stop' or order.type == 'stop_limit' for order in orders)
                        
                        if not has_stop_loss:
                            violations.append({
                                'type': 'stop_loss_missing',
                                'severity': 'high',
                                'message': f"No stop loss order found for {symbol}",
                                'symbol': symbol,
                                'timestamp': datetime.now(EST_TIMEZONE)
                            })
                        else:
                            # Get the stop loss price
                            stop_orders = [order for order in orders if order.type == 'stop' or order.type == 'stop_limit']
                            if stop_orders:
                                stop_price = float(stop_orders[0].stop_price)
                                
                                # Calculate amount at risk
                                if float(position.qty) > 0:  # Long position
                                    at_risk = (current_price - stop_price) * abs(float(position.qty))
                                else:  # Short position
                                    at_risk = (stop_price - current_price) * abs(float(position.qty))
                                
                                # Add to total at risk
                                total_at_risk += at_risk
                                
                                # Check risk/reward ratio for new positions (within last day)
                                position_age = datetime.now(EST_TIMEZONE) - datetime.fromisoformat(position.created_at.replace('Z', '+00:00')).astimezone(EST_TIMEZONE)
                                
                                if position_age < timedelta(days=1):
                                    # Try to find take profit order
                                    take_profit_orders = self.api.list_orders(
                                        status='open',
                                        side='sell' if float(position.qty) > 0 else 'buy',
                                        symbols=[symbol],
                                        limit_price=None if float(position.qty) < 0 else None
                                    )
                                    
                                    take_profit_orders = [order for order in take_profit_orders if order.type == 'limit']
                                    
                                    if take_profit_orders:
                                        take_profit_price = float(take_profit_orders[0].limit_price)
                                        
                                        # Calculate potential reward
                                        if float(position.qty) > 0:  # Long position
                                            reward = (take_profit_price - current_price) * abs(float(position.qty))
                                        else:  # Short position
                                            reward = (current_price - take_profit_price) * abs(float(position.qty))
                                        
                                        # Calculate risk/reward ratio
                                        if at_risk > 0:
                                            risk_reward_ratio = reward / at_risk
                                            
                                            if risk_reward_ratio < self.risk_reward_min:
                                                violations.append({
                                                    'type': 'risk_reward_ratio',
                                                    'severity': 'medium',
                                                    'message': f"Risk/reward ratio for {symbol} below minimum: {risk_reward_ratio:.2f} < {self.risk_reward_min:.2f}",
                                                    'symbol': symbol,
                                                    'timestamp': datetime.now(EST_TIMEZONE)
                                                })
                    
                    except Exception as e:
                        logger.error(f"Error checking stop loss for {symbol}: {e}")
            
            # Check total position value
            total_position_pct = total_position_value / portfolio_value
            
            # Check if total at risk exceeds maximum
            if total_at_risk > 0:
                total_risk_pct = total_at_risk / portfolio_value
                
                if total_risk_pct > self.max_total_risk_pct:
                    violations.append({
                        'type': 'total_risk',
                        'severity': 'high',
                        'message': f"Total portfolio at risk exceeds maximum: {total_risk_pct*100:.2f}% > {self.max_total_risk_pct*100:.2f}%",
                        'timestamp': datetime.now(EST_TIMEZONE)
                    })
            
            # Log the check
            logger.info(f"Risk check completed: {len(violations)} violations found")
            
            # Save violations
            self.risk_violations.extend(violations)
            
            # Return violations
            return violations
        
        except Exception as e:
            logger.error(f"Error checking risk parameters: {e}")
            return []
    
    def handle_risk_violations(self, violations: List[Dict[str, Any]]):
        """
        Handle risk violations.
        
        Args:
            violations: List of risk violations
        """
        try:
            # Group violations by severity
            high_severity = [v for v in violations if v.get('severity') == 'high']
            medium_severity = [v for v in violations if v.get('severity') == 'medium']
            low_severity = [v for v in violations if v.get('severity') == 'low']
            
            # Handle high severity violations
            if high_severity:
                # Send alert
                message = "🚨 *HIGH RISK ALERT* 🚨\n\n"
                message += "The following high-risk violations were detected:\n\n"
                
                for violation in high_severity:
                    message += f"- {violation.get('message')}\n"
                
                message += f"\nTimestamp: {datetime.now(EST_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')} EST"
                
                # Send Telegram alert
                try:
                    send_telegram_message(message)
                except:
                    logger.error("Failed to send Telegram alert")
                
                # Log violations
                for violation in high_severity:
                    logger.warning(f"High risk violation: {violation.get('message')}")
                
                # If in paper trading, we could automatically fix some violations
                if self.is_paper:
                    # For example, we could add missing stop losses or reduce position sizes
                    for violation in high_severity:
                        if violation.get('type') == 'stop_loss_missing' and 'symbol' in violation:
                            self.add_emergency_stop_loss(violation.get('symbol'))
            
            # Handle medium severity violations
            if medium_severity:
                # Log violations
                for violation in medium_severity:
                    logger.info(f"Medium risk violation: {violation.get('message')}")
                
                # If there are multiple medium violations, send an alert
                if len(medium_severity) >= 2:
                    message = "⚠️ *RISK WARNING* ⚠️\n\n"
                    message += "The following risk warnings were detected:\n\n"
                    
                    for violation in medium_severity:
                        message += f"- {violation.get('message')}\n"
                    
                    message += f"\nTimestamp: {datetime.now(EST_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')} EST"
                    
                    # Send Telegram alert
                    try:
                        send_telegram_message(message)
                    except:
                        logger.error("Failed to send Telegram alert")
            
            # Handle low severity violations
            if low_severity:
                # Log violations
                for violation in low_severity:
                    logger.info(f"Low risk violation: {violation.get('message')}")
        
        except Exception as e:
            logger.error(f"Error handling risk violations: {e}")
    
    def add_emergency_stop_loss(self, symbol: str):
        """
        Add an emergency stop loss for a position.
        
        Args:
            symbol: The symbol to add a stop loss for
        """
        try:
            # Only do this in paper trading
            if not self.is_paper:
                logger.warning(f"Cannot add emergency stop loss for {symbol} in live trading")
                return
            
            # Get the position
            position = self.api.get_position(symbol)
            
            # Calculate stop loss price (2% from current price)
            current_price = float(position.current_price)
            qty = float(position.qty)
            
            if qty > 0:  # Long position
                stop_price = current_price * 0.98
            else:  # Short position
                stop_price = current_price * 1.02
            
            # Submit stop loss order
            self.api.submit_order(
                symbol=symbol,
                qty=abs(qty),
                side='sell' if qty > 0 else 'buy',
                type='stop',
                time_in_force='gtc',
                stop_price=stop_price
            )
            
            logger.info(f"Added emergency stop loss for {symbol} at {stop_price}")
            
            # Send notification
            message = "🛑 *Emergency Stop Loss Added* 🛑\n\n"
            message += f"Symbol: {symbol}\n"
            message += f"Stop Price: ${stop_price:.2f}\n"
            message += f"This is an automated emergency action to limit risk.\n"
            message += f"\nTimestamp: {datetime.now(EST_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')} EST"
            
            try:
                send_telegram_message(message)
            except:
                logger.error("Failed to send Telegram alert")
        
        except Exception as e:
            logger.error(f"Error adding emergency stop loss for {symbol}: {e}")
    
    def update_portfolio_history(self):
        """Update the portfolio history."""
        try:
            # Get account information
            account = self.api.get_account()
            portfolio_value = float(account.portfolio_value)
            cash = float(account.cash)
            
            # Add to history
            self.portfolio_history.append({
                'timestamp': datetime.now(EST_TIMEZONE),
                'portfolio_value': portfolio_value,
                'cash': cash,
                'equity': portfolio_value - cash,
                'drawdown': self.current_drawdown
            })
            
            # Keep only the last 1440 entries (1 day at 1-minute intervals)
            if len(self.portfolio_history) > 1440:
                self.portfolio_history = self.portfolio_history[-1440:]
            
            # Save to file periodically (every hour)
            if len(self.portfolio_history) % 60 == 0:
                self.save_portfolio_history()
        
        except Exception as e:
            logger.error(f"Error updating portfolio history: {e}")
    
    def save_portfolio_history(self):
        """Save the portfolio history to a file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs('data/risk', exist_ok=True)
            
            # Convert to DataFrame
            df = pd.DataFrame(self.portfolio_history)
            
            # Save to CSV
            filename = f"data/risk/portfolio_history_{datetime.now(EST_TIMEZONE).strftime('%Y%m%d')}.csv"
            df.to_csv(filename, index=False)
            
            logger.info(f"Saved portfolio history to {filename}")
        
        except Exception as e:
            logger.error(f"Error saving portfolio history: {e}")
    
    def save_risk_violations(self):
        """Save the risk violations to a file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs('data/risk', exist_ok=True)
            
            # Convert to DataFrame
            df = pd.DataFrame(self.risk_violations)
            
            # Save to CSV
            filename = f"data/risk/risk_violations_{datetime.now(EST_TIMEZONE).strftime('%Y%m%d')}.csv"
            df.to_csv(filename, index=False)
            
            logger.info(f"Saved risk violations to {filename}")
        
        except Exception as e:
            logger.error(f"Error saving risk violations: {e}")
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current risk status.
        
        Returns:
            Dict with risk summary
        """
        try:
            # Get account information
            account = self.api.get_account()
            portfolio_value = float(account.portfolio_value)
            buying_power = float(account.buying_power)
            
            # Get positions
            positions = self.api.list_positions()
            
            # Calculate total position value and at risk
            total_position_value = sum(float(position.market_value) for position in positions)
            
            # Calculate position concentration
            position_values = [float(position.market_value) for position in positions]
            position_concentration = max(position_values) / portfolio_value if position_values else 0
            
            # Calculate drawdown
            drawdown = self.current_drawdown
            
            # Count risk violations
            high_violations = len([v for v in self.risk_violations if v.get('severity') == 'high' and 
                                  (datetime.now(EST_TIMEZONE) - v.get('timestamp')).total_seconds() < 86400])  # Last 24 hours
            
            medium_violations = len([v for v in self.risk_violations if v.get('severity') == 'medium' and 
                                    (datetime.now(EST_TIMEZONE) - v.get('timestamp')).total_seconds() < 86400])
            
            # Create summary
            summary = {
                'timestamp': datetime.now(EST_TIMEZONE),
                'portfolio_value': portfolio_value,
                'buying_power': buying_power,
                'total_position_value': total_position_value,
                'position_concentration': position_concentration,
                'drawdown': drawdown,
                'high_violations_24h': high_violations,
                'medium_violations_24h': medium_violations,
                'risk_status': 'high' if high_violations > 0 else 'medium' if medium_violations > 1 else 'low',
                'max_position_size_pct': self.max_position_size_pct,
                'max_total_risk_pct': self.max_total_risk_pct,
                'max_drawdown_pct': self.max_drawdown_pct,
                'stop_loss_required': self.stop_loss_required,
                'risk_reward_min': self.risk_reward_min
            }
            
            return summary
        
        except Exception as e:
            logger.error(f"Error getting risk summary: {e}")
            return {}

# Singleton instance
_monitor = None

def get_risk_monitor(api, is_paper=True) -> RiskMonitor:
    """
    Get the singleton RiskMonitor instance.
    
    Args:
        api: The trading API instance
        is_paper: Whether this is paper trading
    
    Returns:
        RiskMonitor instance
    """
    global _monitor
    if _monitor is None:
        _monitor = RiskMonitor(api, is_paper)
    return _monitor

def start_risk_monitoring(api, is_paper=True, check_interval=RISK_CHECK_INTERVAL):
    """
    Start monitoring risk parameters.
    
    Args:
        api: The trading API instance
        is_paper: Whether this is paper trading
        check_interval: Interval in seconds between checks
    """
    monitor = get_risk_monitor(api, is_paper)
    monitor.start_monitoring(check_interval)

def stop_risk_monitoring():
    """Stop monitoring risk parameters."""
    global _monitor
    if _monitor is not None:
        _monitor.stop_monitoring()

def get_risk_summary() -> Dict[str, Any]:
    """
    Get a summary of the current risk status.
    
    Returns:
        Dict with risk summary
    """
    global _monitor
    if _monitor is not None:
        return _monitor.get_risk_summary()
    return {}

# Example usage
if __name__ == "__main__":
    import alpaca_trade_api as tradeapi
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Get API credentials
    API_KEY = os.getenv('ALPACA_API_KEY')
    API_SECRET = os.getenv('ALPACA_API_SECRET')
    BASE_URL = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
    
    # Initialize Alpaca API
    api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')
    
    # Start risk monitoring
    start_risk_monitoring(api, is_paper=True)
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_risk_monitoring()
        print("Risk monitoring stopped") 