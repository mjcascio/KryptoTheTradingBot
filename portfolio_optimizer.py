import pandas as pd
import numpy as np
import json
import os
import logging
import yfinance as yf
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class PortfolioOptimizer:
    def __init__(self, max_positions=10, sector_max_allocation=0.30, 
                 stock_max_allocation=0.15, min_positions=3):
        """
        Initialize the Portfolio Optimizer
        
        Args:
            max_positions: Maximum number of positions in portfolio
            sector_max_allocation: Maximum allocation to a single sector
            stock_max_allocation: Maximum allocation to a single stock
            min_positions: Minimum number of positions for diversification
        """
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        self.max_positions = max_positions
        self.sector_max_allocation = sector_max_allocation
        self.stock_max_allocation = stock_max_allocation
        self.min_positions = min_positions
        
        # Cache for sector information
        self.sector_cache_file = 'data/sector_cache.json'
        self.sector_info = {}
        
        # Load sector cache
        self._load_sector_cache()
        
        # Trading bot reference
        self.bot = None
        
        logger.info(f"Portfolio Optimizer initialized: max_positions={max_positions}, sector_max={sector_max_allocation}, stock_max={stock_max_allocation}")
    
    def connect_to_bot(self, bot):
        """
        Connect this portfolio optimizer to the trading bot
        
        Args:
            bot: The trading bot instance to connect to
        """
        self.bot = bot
        logger.info("Portfolio Optimizer connected to trading bot")
    
    def _load_sector_cache(self):
        """Load sector cache from file"""
        if os.path.exists(self.sector_cache_file):
            try:
                with open(self.sector_cache_file, 'r') as f:
                    self.sector_info = json.load(f)
                logger.info(f"Loaded sector cache with {len(self.sector_info)} symbols")
            except Exception as e:
                logger.error(f"Error loading sector cache: {str(e)}")
                self.sector_info = {}
        else:
            self.sector_info = {}
    
    def _save_sector_cache(self):
        """Save sector cache to file"""
        try:
            with open(self.sector_cache_file, 'w') as f:
                json.dump(self.sector_info, f)
        except Exception as e:
            logger.error(f"Error saving sector cache: {str(e)}")
    
    def get_sector_info(self, symbol: str) -> Dict[str, str]:
        """
        Get sector information for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with sector and industry
        """
        if symbol in self.sector_info:
            return self.sector_info[symbol]
            
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            sector = info.get('sector', 'Unknown')
            industry = info.get('industry', 'Unknown')
            
            self.sector_info[symbol] = {
                'sector': sector,
                'industry': industry
            }
            
            # Save updated cache
            self._save_sector_cache()
            
            logger.info(f"Retrieved sector info for {symbol}: {sector}, {industry}")
            return self.sector_info[symbol]
        except Exception as e:
            logger.error(f"Error getting sector info for {symbol}: {str(e)}")
            return {'sector': 'Unknown', 'industry': 'Unknown'}
    
    def calculate_current_allocation(self, positions: Dict[str, Dict], account_value: float) -> Dict:
        """
        Calculate current allocation by stock and sector
        
        Args:
            positions: Dictionary of current positions
            account_value: Total account value
            
        Returns:
            Dictionary with stock and sector allocations
        """
        try:
            stock_allocation = {}
            sector_allocation = {}
            industry_allocation = {}
            
            for symbol, position in positions.items():
                # Get position value
                position_value = position['quantity'] * position['current_price']
                allocation = position_value / account_value
                
                # Stock allocation
                stock_allocation[symbol] = allocation
                
                # Sector allocation
                sector_info = self.get_sector_info(symbol)
                sector = sector_info['sector']
                industry = sector_info['industry']
                
                if sector in sector_allocation:
                    sector_allocation[sector] += allocation
                else:
                    sector_allocation[sector] = allocation
                    
                if industry in industry_allocation:
                    industry_allocation[industry] += allocation
                else:
                    industry_allocation[industry] = allocation
            
            logger.info(f"Current allocation: {len(positions)} positions, top sector: {max(sector_allocation.items(), key=lambda x: x[1])[0] if sector_allocation else 'None'}")
            
            return {
                'stock_allocation': stock_allocation,
                'sector_allocation': sector_allocation,
                'industry_allocation': industry_allocation
            }
        except Exception as e:
            logger.error(f"Error calculating current allocation: {str(e)}")
            return {'stock_allocation': {}, 'sector_allocation': {}, 'industry_allocation': {}}
    
    def rank_potential_trades(self, potential_trades: List[Dict]) -> List[Dict]:
        """
        Rank potential trades by expected return/risk
        
        Args:
            potential_trades: List of potential trade dictionaries
            
        Returns:
            List of ranked trade dictionaries
        """
        try:
            ranked_trades = []
            
            for trade in potential_trades:
                symbol = trade['symbol']
                entry = trade['entry_price']
                stop = trade['stop_loss']
                target = trade['take_profit']
                probability = trade['probability']
                
                # Calculate expected return
                risk = entry - stop
                reward = target - entry
                risk_reward = reward / risk if risk > 0 else 0
                expected_return = (probability * reward) - ((1 - probability) * risk)
                
                # Get sector info
                sector_info = self.get_sector_info(symbol)
                
                # Add to ranked list
                ranked_trades.append({
                    'symbol': symbol,
                    'trade': trade,
                    'expected_return': expected_return,
                    'risk_reward': risk_reward,
                    'probability': probability,
                    'sector': sector_info['sector'],
                    'industry': sector_info['industry']
                })
            
            # Sort by expected return (descending)
            ranked_trades.sort(key=lambda x: x['expected_return'], reverse=True)
            
            logger.info(f"Ranked {len(ranked_trades)} potential trades")
            return ranked_trades
        except Exception as e:
            logger.error(f"Error ranking potential trades: {str(e)}")
            return []
    
    def optimize_portfolio(self, current_positions: Dict[str, Dict], 
                          potential_trades: List[Dict], account_value: float) -> List[Dict]:
        """
        Optimize portfolio based on current positions and potential trades
        
        Args:
            current_positions: Dictionary of current positions
            potential_trades: List of potential trade dictionaries
            account_value: Total account value
            
        Returns:
            List of optimized trade dictionaries
        """
        try:
            # Calculate current allocation
            current_allocation = self.calculate_current_allocation(current_positions, account_value)
            
            # Rank potential trades
            ranked_trades = self.rank_potential_trades(potential_trades)
            
            # Filter trades based on portfolio constraints
            optimized_trades = []
            
            for trade in ranked_trades:
                symbol = trade['symbol']
                sector = trade['sector']
                industry = trade['industry']
                
                # Skip if we already have this symbol
                if symbol in current_positions:
                    continue
                    
                # Check if adding this position would exceed max positions
                if len(current_positions) + len(optimized_trades) >= self.max_positions:
                    logger.info(f"Maximum positions ({self.max_positions}) reached")
                    break
                    
                # Check sector allocation
                current_sector_allocation = current_allocation['sector_allocation'].get(sector, 0)
                estimated_new_allocation = trade['trade'].get('position_size', account_value * 0.05) / account_value
                
                if current_sector_allocation + estimated_new_allocation > self.sector_max_allocation:
                    logger.info(f"Skipping {symbol}: sector {sector} would exceed max allocation")
                    continue
                    
                # Check stock allocation
                if estimated_new_allocation > self.stock_max_allocation:
                    # Adjust position size to meet max allocation
                    original_size = trade['trade'].get('position_size', 0)
                    adjusted_size = account_value * self.stock_max_allocation
                    
                    logger.info(f"Adjusting position size for {symbol} from {original_size:.2f} to {adjusted_size:.2f}")
                    
                    # Update position size
                    trade['trade']['position_size'] = adjusted_size
                
                # Add to optimized trades
                optimized_trades.append(trade['trade'])
                
                logger.info(f"Added {symbol} to optimized trades (expected return: {trade['expected_return']:.2f})")
            
            logger.info(f"Optimized portfolio: {len(optimized_trades)} new trades")
            return optimized_trades
        except Exception as e:
            logger.error(f"Error optimizing portfolio: {str(e)}")
            return []
    
    def suggest_rebalancing(self, current_positions: Dict[str, Dict], account_value: float) -> List[Dict]:
        """
        Suggest rebalancing actions for current portfolio
        
        Args:
            current_positions: Dictionary of current positions
            account_value: Total account value
            
        Returns:
            List of rebalancing action dictionaries
        """
        try:
            current_allocation = self.calculate_current_allocation(current_positions, account_value)
            rebalance_actions = []
            
            # Check for overweight sectors
            for sector, allocation in current_allocation['sector_allocation'].items():
                if allocation > self.sector_max_allocation:
                    excess = allocation - self.sector_max_allocation
                    
                    logger.info(f"Sector {sector} is overweight by {excess:.1%}")
                    
                    # Find positions in this sector to reduce
                    sector_positions = {s: p for s, p in current_positions.items() 
                                       if self.get_sector_info(s)['sector'] == sector}
                    
                    # Sort by unrealized P&L (reduce losers first)
                    sorted_positions = sorted(sector_positions.items(), 
                                             key=lambda x: x[1].get('unrealized_pl', 0))
                    
                    for symbol, position in sorted_positions:
                        position_allocation = position['quantity'] * position['current_price'] / account_value
                        
                        if excess > 0:
                            # Calculate reduction needed
                            reduction_pct = min(position_allocation, excess)
                            reduction_shares = int(reduction_pct * account_value / position['current_price'])
                            
                            if reduction_shares > 0:
                                rebalance_actions.append({
                                    'action': 'reduce',
                                    'symbol': symbol,
                                    'shares': reduction_shares,
                                    'reason': f"Sector {sector} overweight by {excess:.1%}"
                                })
                                
                                logger.info(f"Suggesting to reduce {symbol} by {reduction_shares} shares")
                                
                                excess -= reduction_pct
            
            # Check for overweight individual positions
            for symbol, allocation in current_allocation['stock_allocation'].items():
                if allocation > self.stock_max_allocation:
                    excess = allocation - self.stock_max_allocation
                    position = current_positions[symbol]
                    
                    reduction_shares = int(excess * account_value / position['current_price'])
                    
                    if reduction_shares > 0:
                        rebalance_actions.append({
                            'action': 'reduce',
                            'symbol': symbol,
                            'shares': reduction_shares,
                            'reason': f"Position overweight by {excess:.1%}"
                        })
                        
                        logger.info(f"Suggesting to reduce {symbol} by {reduction_shares} shares (position overweight)")
            
            logger.info(f"Rebalancing suggestions: {len(rebalance_actions)} actions")
            return rebalance_actions
        except Exception as e:
            logger.error(f"Error suggesting rebalancing: {str(e)}")
            return []
    
    def calculate_portfolio_metrics(self, positions: Dict[str, Dict]) -> Dict:
        """
        Calculate portfolio metrics
        
        Args:
            positions: Dictionary of current positions
            
        Returns:
            Dictionary with portfolio metrics
        """
        try:
            if not positions:
                return {
                    'diversification_score': 0,
                    'sector_count': 0,
                    'industry_count': 0,
                    'concentration_score': 0
                }
                
            # Count sectors and industries
            sectors = set()
            industries = set()
            
            for symbol in positions:
                sector_info = self.get_sector_info(symbol)
                sectors.add(sector_info['sector'])
                industries.add(sector_info['industry'])
                
            # Calculate diversification score
            sector_count = len(sectors)
            industry_count = len(industries)
            position_count = len(positions)
            
            # Simple diversification score
            diversification_score = min(1.0, (
                (position_count / self.max_positions) * 0.4 +
                (sector_count / 11) * 0.4 +  # 11 sectors in S&P 500
                (industry_count / 24) * 0.2  # Simplified industry count
            ))
            
            # Calculate concentration
            concentration_score = 1.0  # Lower is more concentrated
            
            logger.info(f"Portfolio metrics: {position_count} positions, {sector_count} sectors, {industry_count} industries")
            
            return {
                'diversification_score': diversification_score,
                'sector_count': sector_count,
                'industry_count': industry_count,
                'concentration_score': concentration_score
            }
        except Exception as e:
            logger.error(f"Error calculating portfolio metrics: {str(e)}")
            return {
                'diversification_score': 0,
                'sector_count': 0,
                'industry_count': 0,
                'concentration_score': 0
            } 