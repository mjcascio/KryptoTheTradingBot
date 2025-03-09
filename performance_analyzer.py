import pandas as pd
import numpy as np
import json
import os
import logging
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io
import base64
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class PerformanceAnalyzer:
    def __init__(self, history_file='data/trade_history.json'):
        """
        Initialize the Performance Analyzer
        
        Args:
            history_file: Path to trade history file
        """
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        os.makedirs('reports', exist_ok=True)
        
        self.history_file = history_file
        self.trade_history = []
        self.daily_returns = []
        self.metrics = {}
        self.parameter_sensitivity = {}
        
        # Load trade history
        self._load_history()
        
        # Trading bot reference
        self.bot = None
        
        logger.info(f"Performance Analyzer initialized with {len(self.trade_history)} historical trades")
    
    def connect_to_bot(self, bot):
        """
        Connect this performance analyzer to the trading bot
        
        Args:
            bot: The trading bot instance to connect to
        """
        self.bot = bot
        logger.info("Performance Analyzer connected to trading bot")
    
    def _load_history(self):
        """Load trade history from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    self.trade_history = json.load(f)
                logger.info(f"Loaded trade history with {len(self.trade_history)} trades")
            except Exception as e:
                logger.error(f"Error loading trade history: {str(e)}")
                self.trade_history = []
        else:
            self.trade_history = []
    
    def save_history(self):
        """Save trade history to file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.trade_history, f)
            logger.info(f"Saved trade history with {len(self.trade_history)} trades")
        except Exception as e:
            logger.error(f"Error saving trade history: {str(e)}")
    
    def add_trade(self, trade_data: Dict):
        """
        Add a trade to the history
        
        Args:
            trade_data: Dictionary with trade data
        """
        try:
            # Add timestamp if not present
            if 'timestamp' not in trade_data:
                trade_data['timestamp'] = datetime.now().isoformat()
                
            # Add to history
            self.trade_history.append(trade_data)
            
            # Save updated history
            self.save_history()
            
            logger.info(f"Added trade for {trade_data.get('symbol')} to history")
        except Exception as e:
            logger.error(f"Error adding trade to history: {str(e)}")
    
    def calculate_metrics(self) -> Dict:
        """
        Calculate key performance metrics
        
        Returns:
            Dictionary with performance metrics
        """
        try:
            if not self.trade_history:
                logger.warning("No trade history available for metrics calculation")
                return {}
                
            # Basic metrics
            total_trades = len(self.trade_history)
            winning_trades = sum(1 for t in self.trade_history if t.get('profit', 0) > 0)
            losing_trades = total_trades - winning_trades
            
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            total_profit = sum(t.get('profit', 0) for t in self.trade_history)
            total_wins = sum(t.get('profit', 0) for t in self.trade_history if t.get('profit', 0) > 0)
            total_losses = sum(abs(t.get('profit', 0)) for t in self.trade_history if t.get('profit', 0) < 0)
            
            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
            
            # Calculate daily returns
            daily_pnl = {}
            for trade in self.trade_history:
                date_str = trade.get('exit_time', trade.get('timestamp', '')).split('T')[0]
                if date_str:
                    if date_str in daily_pnl:
                        daily_pnl[date_str] += trade.get('profit', 0)
                    else:
                        daily_pnl[date_str] = trade.get('profit', 0)
                    
            self.daily_returns = [{'date': date, 'return': pnl} for date, pnl in daily_pnl.items()]
            
            # Calculate Sharpe ratio (if we have enough data)
            sharpe_ratio = 0
            max_drawdown = 0
            
            if len(self.daily_returns) > 5:
                daily_returns_series = pd.Series([r['return'] for r in self.daily_returns])
                
                # Sharpe ratio (annualized)
                sharpe_ratio = daily_returns_series.mean() / daily_returns_series.std() * np.sqrt(252) if daily_returns_series.std() > 0 else 0
                
                # Calculate drawdown
                cumulative_returns = daily_returns_series.cumsum()
                running_max = cumulative_returns.cummax()
                drawdown = (cumulative_returns - running_max) / running_max
                max_drawdown = drawdown.min() if len(drawdown) > 0 else 0
            
            # Calculate average trade metrics
            avg_profit = total_profit / total_trades if total_trades > 0 else 0
            avg_win = total_wins / winning_trades if winning_trades > 0 else 0
            avg_loss = total_losses / losing_trades if losing_trades > 0 else 0
            
            # Store metrics
            self.metrics = {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'total_profit': total_profit,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'avg_profit': avg_profit,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'risk_reward_realized': abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
            }
            
            logger.info(f"Calculated performance metrics: win_rate={win_rate:.2f}, profit_factor={profit_factor:.2f}, total_profit={total_profit:.2f}")
            
            return self.metrics
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            return {}
    
    def analyze_by_factor(self, factor_name: str) -> Dict:
        """
        Analyze performance by a specific factor
        
        Args:
            factor_name: Name of the factor to analyze
            
        Returns:
            Dictionary with factor analysis
        """
        try:
            if not self.trade_history:
                return {}
                
            # Special handling for strategy which might be a list
            if factor_name == 'strategy':
                # Create a new trade history with strategy as string
                processed_history = []
                for trade in self.trade_history:
                    if 'strategy' in trade:
                        if isinstance(trade['strategy'], list):
                            # Join list into string
                            trade_copy = trade.copy()
                            trade_copy['strategy'] = ','.join(trade['strategy'])
                            processed_history.append(trade_copy)
                        else:
                            processed_history.append(trade)
                    else:
                        processed_history.append(trade)
                        
                # Use processed history
                history_to_use = processed_history
            else:
                history_to_use = self.trade_history
                
            # Check if factor exists in trade history
            if not any(factor_name in trade for trade in history_to_use):
                logger.warning(f"Factor {factor_name} not found in trade history")
                return {}
                
            # Group trades by factor
            factor_groups = {}
            for trade in history_to_use:
                factor_value = trade.get(factor_name, 'unknown')
                
                if factor_value not in factor_groups:
                    factor_groups[factor_value] = []
                    
                factor_groups[factor_value].append(trade)
                
            # Calculate metrics for each group
            factor_metrics = {}
            for value, trades in factor_groups.items():
                total = len(trades)
                wins = sum(1 for t in trades if t.get('profit', 0) > 0)
                profit = sum(t.get('profit', 0) for t in trades)
                
                factor_metrics[value] = {
                    'trades': total,
                    'win_rate': wins / total if total > 0 else 0,
                    'profit': profit,
                    'avg_profit': profit / total if total > 0 else 0
                }
                
            logger.info(f"Analyzed performance by {factor_name}: {len(factor_groups)} distinct values")
            
            return factor_metrics
        except Exception as e:
            logger.error(f"Error analyzing by factor: {str(e)}")
            return {}
    
    def analyze_parameter_sensitivity(self, parameter_ranges: Dict[str, List[float]]) -> Dict:
        """
        Analyze sensitivity to strategy parameters
        
        Args:
            parameter_ranges: Dictionary of parameter names and ranges to test
            
        Returns:
            Dictionary with sensitivity analysis results
        """
        try:
            sensitivity_results = {}
            
            for param, values in parameter_ranges.items():
                param_results = []
                
                for value in values:
                    # Simulate performance with this parameter value
                    # In a real implementation, this would re-run the strategy
                    # Here we use a simple model for demonstration
                    
                    # Baseline metrics
                    base_win_rate = 0.5
                    base_profit = 1000
                    
                    # Parameter sensitivity model (simplified)
                    if param == 'price_threshold':
                        # Higher threshold -> higher win rate but fewer trades
                        win_rate = base_win_rate + (value - np.mean(values)) / 10
                        profit = base_profit * win_rate
                    elif param == 'volume_threshold':
                        # Higher volume threshold -> higher win rate but fewer trades
                        win_rate = base_win_rate + (value - np.mean(values)) / 20
                        profit = base_profit * win_rate
                    elif param == 'stop_loss_pct':
                        # Tighter stops -> lower win rate but better risk management
                        win_rate = base_win_rate - (value - np.mean(values)) / 15
                        profit = base_profit * win_rate * (1 + (np.mean(values) - value) / 5)
                    else:
                        # Generic model
                        win_rate = base_win_rate + (value - np.mean(values)) / 100
                        profit = base_profit * win_rate
                    
                    param_results.append({
                        'value': value,
                        'win_rate': win_rate,
                        'profit': profit
                    })
                    
                sensitivity_results[param] = param_results
                
            self.parameter_sensitivity = sensitivity_results
            
            logger.info(f"Analyzed parameter sensitivity for {len(parameter_ranges)} parameters")
            
            return sensitivity_results
        except Exception as e:
            logger.error(f"Error analyzing parameter sensitivity: {str(e)}")
            return {}
    
    def suggest_improvements(self) -> List[Dict]:
        """
        Suggest strategy improvements based on analysis
        
        Returns:
            List of improvement suggestion dictionaries
        """
        try:
            if not self.metrics:
                self.calculate_metrics()
                
            suggestions = []
            
            # Check win rate
            if self.metrics.get('win_rate', 0) < 0.4:
                suggestions.append({
                    'area': 'Entry Criteria',
                    'suggestion': 'Tighten entry criteria to improve win rate',
                    'current': f"{self.metrics.get('win_rate', 0):.1%}",
                    'target': '> 50%',
                    'priority': 'high'
                })
                
            # Check risk-reward
            if self.metrics.get('risk_reward_realized', 0) < 1.5:
                suggestions.append({
                    'area': 'Exit Strategy',
                    'suggestion': 'Widen take profit targets to improve risk-reward ratio',
                    'current': f"{self.metrics.get('risk_reward_realized', 0):.2f}",
                    'target': '> 2.0',
                    'priority': 'medium'
                })
                
            # Check drawdown
            if self.metrics.get('max_drawdown', 0) < -0.2:
                suggestions.append({
                    'area': 'Risk Management',
                    'suggestion': 'Reduce position sizing to limit drawdowns',
                    'current': f"{self.metrics.get('max_drawdown', 0):.1%}",
                    'target': '> -15%',
                    'priority': 'high'
                })
                
            # Check profit factor
            if self.metrics.get('profit_factor', 0) < 1.2:
                suggestions.append({
                    'area': 'Strategy',
                    'suggestion': 'Review overall strategy effectiveness',
                    'current': f"{self.metrics.get('profit_factor', 0):.2f}",
                    'target': '> 1.5',
                    'priority': 'high'
                })
                
            # Check trade frequency
            if self.metrics.get('total_trades', 0) < 20:
                suggestions.append({
                    'area': 'Trade Frequency',
                    'suggestion': 'Consider relaxing entry criteria to increase trade frequency',
                    'current': f"{self.metrics.get('total_trades', 0)} trades",
                    'target': '> 50 trades',
                    'priority': 'low'
                })
                
            logger.info(f"Generated {len(suggestions)} improvement suggestions")
            
            return suggestions
        except Exception as e:
            logger.error(f"Error suggesting improvements: {str(e)}")
            return []
    
    def generate_equity_curve_chart(self) -> Optional[str]:
        """
        Generate equity curve chart as base64 image
        
        Returns:
            Base64 encoded image string or None if error
        """
        try:
            if not self.daily_returns:
                logger.warning("No daily returns data for equity curve")
                return None
                
            # Convert to DataFrame
            df = pd.DataFrame(self.daily_returns)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            df['cumulative'] = df['return'].cumsum()
            
            # Create plot
            plt.figure(figsize=(10, 6))
            plt.plot(df['date'], df['cumulative'])
            plt.title('Equity Curve')
            plt.xlabel('Date')
            plt.ylabel('Cumulative P&L ($)')
            plt.grid(True)
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close()
            
            logger.info("Generated equity curve chart")
            
            return image_base64
        except Exception as e:
            logger.error(f"Error generating equity curve chart: {str(e)}")
            return None
    
    def generate_report(self) -> Dict:
        """
        Generate a comprehensive performance report
        
        Returns:
            Dictionary with performance report
        """
        try:
            # Calculate metrics if not already done
            if not self.metrics:
                self.calculate_metrics()
                
            # Generate equity curve
            equity_curve = self.generate_equity_curve_chart()
            
            # Analyze by various factors
            by_market_regime = self.analyze_by_factor('market_condition')
            by_day_of_week = self.analyze_by_factor('day_of_week')
            by_strategy = self.analyze_by_factor('strategy')
            
            # Get improvement suggestions
            suggestions = self.suggest_improvements()
            
            # Create report dictionary
            report = {
                'timestamp': datetime.now().isoformat(),
                'summary': self.metrics,
                'suggestions': suggestions,
                'by_market_regime': by_market_regime,
                'by_day_of_week': by_day_of_week,
                'by_strategy': by_strategy,
                'parameter_sensitivity': self.parameter_sensitivity,
                'equity_curve': equity_curve
            }
            
            # Save report to file
            report_file = f"reports/performance_report_{datetime.now().strftime('%Y%m%d')}.json"
            with open(report_file, 'w') as f:
                # Remove equity curve from saved report (too large)
                report_to_save = report.copy()
                report_to_save.pop('equity_curve', None)
                json.dump(report_to_save, f)
                
            logger.info(f"Generated performance report: {report_file}")
            
            return report
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return {} 