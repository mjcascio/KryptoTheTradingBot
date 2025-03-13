#!/usr/bin/env python3
"""
Options Trading Strategy Module

This module implements options-specific trading strategies.
"""

from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
import numpy as np
from .base import BaseStrategy

logger = logging.getLogger(__name__)

class OptionsStrategy(BaseStrategy):
    """Options trading strategy implementation"""
    
    def __init__(
        self,
        name: str,
        description: str,
        risk_per_trade: float = 0.02,
        min_delta: float = 0.3,
        max_delta: float = 0.7,
        min_days_to_expiry: int = 30,
        max_days_to_expiry: int = 45,
        min_volume: int = 100,
        min_open_interest: int = 500,
        max_bid_ask_spread: float = 0.10,
        iv_percentile_threshold: float = 60.0
    ):
        """Initialize the options strategy
        
        Args:
            name (str): Strategy name
            description (str): Strategy description
            risk_per_trade (float): Risk per trade as a percentage of account value
            min_delta (float): Minimum option delta
            max_delta (float): Maximum option delta
            min_days_to_expiry (int): Minimum days to expiration
            max_days_to_expiry (int): Maximum days to expiration
            min_volume (int): Minimum option volume
            min_open_interest (int): Minimum open interest
            max_bid_ask_spread (float): Maximum bid-ask spread as percentage
            iv_percentile_threshold (float): IV percentile threshold for entry
        """
        super().__init__(name, description)
        self.risk_per_trade = risk_per_trade
        self.min_delta = min_delta
        self.max_delta = max_delta
        self.min_days_to_expiry = min_days_to_expiry
        self.max_days_to_expiry = max_days_to_expiry
        self.min_volume = min_volume
        self.min_open_interest = min_open_interest
        self.max_bid_ask_spread = max_bid_ask_spread
        self.iv_percentile_threshold = iv_percentile_threshold
        logger.info(f"Initialized options strategy: {name}")

    def analyze_market(self, market_data: Dict) -> List[Dict]:
        """Analyze market data and generate trading signals
        
        Args:
            market_data (Dict): Current market data
            
        Returns:
            List of trading signals
        """
        signals = []
        
        for symbol, data in market_data.items():
            # Get option chain data
            option_chain = self._get_option_chain(data)
            if not option_chain:
                continue
            
            # Analyze market conditions
            market_conditions = self._analyze_market_conditions(data)
            if not market_conditions['favorable']:
                continue
            
            # Find suitable options based on strategy criteria
            suitable_options = self._find_suitable_options(option_chain, data)
            
            for option in suitable_options:
                # Calculate option metrics
                metrics = self._calculate_option_metrics(option, data)
                
                # Generate trading signal if conditions are met
                if self._check_entry_conditions(metrics, market_conditions):
                    signals.append({
                        'symbol': option['symbol'],
                        'underlying': symbol,
                        'action': 'buy',
                        'option_type': option['type'],
                        'strike': option['strike'],
                        'expiry': option['expiry'],
                        'price': (option['bid'] + option['ask']) / 2,
                        'confidence': metrics['signal_strength'],
                        'reason': metrics['signal_reason'],
                        'delta': option['delta'],
                        'gamma': option['gamma'],
                        'theta': option['theta'],
                        'vega': option['vega'],
                        'implied_volatility': option['implied_volatility']
                    })
                
            # Check for exit signals on existing positions
            for position in self.get_all_positions():
                if self._check_exit_conditions(position, data):
                    signals.append({
                        'symbol': position['symbol'],
                        'underlying': symbol,
                        'action': 'sell',
                        'option_type': position['option_type'],
                        'strike': position['strike'],
                        'expiry': position['expiry'],
                        'price': position['current_price'],
                        'confidence': 0.8,
                        'reason': 'Exit conditions met'
                    })
        
        return signals

    def calculate_position_size(self, signal: Dict, account_info: Dict) -> float:
        """Calculate the position size for a trading signal
        
        Args:
            signal (Dict): Trading signal
            account_info (Dict): Account information
            
        Returns:
            Position size in contracts
        """
        account_value = float(account_info['portfolio_value'])
        risk_amount = account_value * self.risk_per_trade
        
        # Calculate max loss per contract
        option_price = signal['price']
        if signal['action'] == 'buy':
            max_loss_per_contract = option_price * 100  # 100 shares per contract
        else:
            # For short options, use margin requirement
            max_loss_per_contract = signal['strike'] * 100 * 0.2  # 20% margin requirement
        
        # Calculate number of contracts
        num_contracts = risk_amount / max_loss_per_contract
        
        # Round down to nearest whole contract
        return max(1, int(num_contracts))

    def set_stop_loss(self, position: Dict) -> float:
        """Set stop loss price for a position
        
        Args:
            position (Dict): Position information
            
        Returns:
            Stop loss price
        """
        entry_price = position['entry_price']
        option_type = position['option_type']
        delta = position['delta']
        
        # Set stop loss based on option type and delta
        if option_type == 'call':
            # More aggressive stop loss for calls
            stop_loss_pct = 0.25 if delta > 0.5 else 0.35
        else:
            # More conservative stop loss for puts
            stop_loss_pct = 0.20 if delta > 0.5 else 0.30
        
        return entry_price * (1 - stop_loss_pct)

    def set_take_profit(self, position: Dict) -> float:
        """Set take profit price for a position
        
        Args:
            position (Dict): Position information
            
        Returns:
            Take profit price
        """
        entry_price = position['entry_price']
        option_type = position['option_type']
        delta = position['delta']
        
        # Set take profit based on option type and delta
        if option_type == 'call':
            # Higher profit target for calls
            take_profit_pct = 0.50 if delta > 0.5 else 0.75
        else:
            # Conservative profit target for puts
            take_profit_pct = 0.40 if delta > 0.5 else 0.60
        
        return entry_price * (1 + take_profit_pct)

    def _analyze_market_conditions(self, data: Dict) -> Dict:
        """Analyze overall market conditions
        
        Args:
            data (Dict): Market data
            
        Returns:
            Dictionary with market condition analysis
        """
        try:
            # Calculate market metrics
            volatility = data.get('volatility', 0)
            trend = data.get('trend', 'neutral')
            volume = data.get('volume', 0)
            avg_volume = data.get('avg_volume', 0)
            rsi = data.get('rsi', 50)
            
            # Determine if conditions are favorable
            favorable = (
                volatility > 15 and  # Minimum volatility
                volume > avg_volume * 0.8 and  # Decent volume
                30 <= rsi <= 70  # Not overbought/oversold
            )
            
            return {
                'favorable': favorable,
                'volatility': volatility,
                'trend': trend,
                'volume_ratio': volume / avg_volume if avg_volume > 0 else 0,
                'rsi': rsi
            }
            
        except Exception as e:
            logger.error(f"Error analyzing market conditions: {e}")
            return {'favorable': False}

    def _calculate_option_metrics(self, option: Dict, market_data: Dict) -> Dict:
        """Calculate option-specific metrics
        
        Args:
            option (Dict): Option data
            market_data (Dict): Market data
            
        Returns:
            Dictionary with calculated metrics
        """
        try:
            # Calculate basic metrics
            bid_ask_spread = (option['ask'] - option['bid']) / option['ask']
            days_to_expiry = (datetime.fromisoformat(option['expiry']) - datetime.now()).days
            
            # Calculate signal strength based on multiple factors
            signal_strength = 0.0
            signal_reasons = []
            
            # Check delta
            if self.min_delta <= abs(option['delta']) <= self.max_delta:
                signal_strength += 0.2
                signal_reasons.append("Delta in range")
            
            # Check volume and open interest
            if option['volume'] >= self.min_volume:
                signal_strength += 0.2
                signal_reasons.append("Sufficient volume")
            if option['open_interest'] >= self.min_open_interest:
                signal_strength += 0.2
                signal_reasons.append("Good open interest")
            
            # Check bid-ask spread
            if bid_ask_spread <= self.max_bid_ask_spread:
                signal_strength += 0.2
                signal_reasons.append("Tight spread")
            
            # Check days to expiry
            if self.min_days_to_expiry <= days_to_expiry <= self.max_days_to_expiry:
                signal_strength += 0.2
                signal_reasons.append("Optimal expiry")
            
            return {
                'signal_strength': signal_strength,
                'signal_reason': ", ".join(signal_reasons),
                'bid_ask_spread': bid_ask_spread,
                'days_to_expiry': days_to_expiry
            }
            
        except Exception as e:
            logger.error(f"Error calculating option metrics: {e}")
            return {
                'signal_strength': 0.0,
                'signal_reason': "Error in calculation",
                'bid_ask_spread': float('inf'),
                'days_to_expiry': 0
            }

    def _check_entry_conditions(self, metrics: Dict, market_conditions: Dict) -> bool:
        """Check if entry conditions are met
        
        Args:
            metrics (Dict): Option metrics
            market_conditions (Dict): Market conditions
            
        Returns:
            bool: True if entry conditions are met
        """
        return (
            market_conditions['favorable'] and
            metrics['signal_strength'] >= 0.6 and  # At least 3 positive factors
            metrics['bid_ask_spread'] <= self.max_bid_ask_spread and
            self.min_days_to_expiry <= metrics['days_to_expiry'] <= self.max_days_to_expiry
        )

    def _check_exit_conditions(self, position: Dict, market_data: Dict) -> bool:
        """Check if exit conditions are met
        
        Args:
            position (Dict): Position information
            market_data (Dict): Market data
            
        Returns:
            bool: True if exit conditions are met
        """
        try:
            # Calculate days to expiry
            days_to_expiry = (datetime.fromisoformat(position['expiry']) - datetime.now()).days
            
            # Exit conditions
            return (
                days_to_expiry <= 5 or  # Close to expiration
                float(position['unrealized_plpc']) <= -0.25 or  # 25% loss
                float(position['unrealized_plpc']) >= 0.50 or  # 50% profit
                market_data.get('rsi', 50) >= 75 or  # Overbought
                market_data.get('rsi', 50) <= 25  # Oversold
            )
            
        except Exception as e:
            logger.error(f"Error checking exit conditions: {e}")
            return False

    def _get_option_chain(self, data: Dict) -> List[Dict]:
        """Get option chain data for a symbol
        
        Args:
            data (Dict): Market data for a symbol
            
        Returns:
            List of option chain data
        """
        try:
            # Get option chain from market data
            return data.get('option_chain', [])
            
        except Exception as e:
            logger.error(f"Error getting option chain: {e}")
            return []

    def _find_suitable_options(self, option_chain: List[Dict], market_data: Dict) -> List[Dict]:
        """Find suitable options based on strategy criteria
        
        Args:
            option_chain (List[Dict]): Option chain data
            market_data (Dict): Market data for the underlying
            
        Returns:
            List of suitable options
        """
        suitable_options = []
        
        try:
            current_price = market_data.get('current_price', 0)
            if not current_price:
                return []
            
            for option in option_chain:
                # Basic option criteria
                if not (
                    self.min_volume <= option['volume'] and
                    self.min_open_interest <= option['open_interest'] and
                    self.min_delta <= abs(option['delta']) <= self.max_delta
                ):
                    continue
                
                # Calculate days to expiry
                days_to_expiry = (datetime.fromisoformat(option['expiry']) - datetime.now()).days
                if not (self.min_days_to_expiry <= days_to_expiry <= self.max_days_to_expiry):
                    continue
                
                # Check bid-ask spread
                bid_ask_spread = (option['ask'] - option['bid']) / option['ask']
                if bid_ask_spread > self.max_bid_ask_spread:
                    continue
                
                # Check implied volatility
                if option['implied_volatility'] < market_data.get('iv_percentile', 0):
                    continue
                
                suitable_options.append(option)
            
            return suitable_options
            
        except Exception as e:
            logger.error(f"Error finding suitable options: {e}")
            return [] 