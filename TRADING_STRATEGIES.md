# KryptoBot Trading Strategies Database

This document serves as a database of trading strategies for KryptoBot. Each strategy includes a description, risk parameters, and implementation details. Strategies are organized by category and risk level.

## Table of Contents

1. [Strategy Overview](#strategy-overview)
2. [Trend Following Strategies](#trend-following-strategies)
3. [Mean Reversion Strategies](#mean-reversion-strategies)
4. [Breakout Strategies](#breakout-strategies)
5. [Options Strategies](#options-strategies)
6. [Multi-Asset Strategies](#multi-asset-strategies)
7. [Risk Management](#risk-management)
8. [Adding New Strategies](#adding-new-strategies)

## Strategy Overview

Each strategy in this database includes the following information:

- **ID**: Unique identifier for the strategy
- **Name**: Descriptive name
- **Category**: Type of strategy (trend following, mean reversion, etc.)
- **Risk Level**: Low, Medium, or High
- **Asset Types**: Stocks, Options, or Both
- **Description**: Brief explanation of the strategy
- **Parameters**: Technical parameters used by the strategy
- **Risk Parameters**: Risk management settings
- **Performance Metrics**: Historical performance data (if available)
- **Implementation Notes**: Details on how the strategy is implemented in KryptoBot

## Trend Following Strategies

### TF001: Simple Moving Average Crossover

- **ID**: TF001
- **Name**: Simple Moving Average Crossover
- **Category**: Trend Following
- **Risk Level**: Medium
- **Asset Types**: Stocks
- **Description**: This strategy uses the crossover of two simple moving averages (SMA) to identify trends. It goes long when the short-term SMA crosses above the long-term SMA and goes short when the short-term SMA crosses below the long-term SMA.
- **Parameters**:
  - `short_period`: 20 (days)
  - `long_period`: 50 (days)
  - `signal_threshold`: 0.01 (1% threshold for signal confirmation)
- **Risk Parameters**:
  - `max_position_size_pct`: 0.05 (5% of portfolio per position)
  - `max_total_risk_pct`: 0.20 (20% of portfolio at risk)
  - `stop_loss_pct`: 0.05 (5% stop loss)
  - `take_profit_pct`: 0.15 (15% take profit)
  - `risk_reward_min`: 2.0 (minimum risk/reward ratio)
- **Performance Metrics**:
  - Win Rate: 55%
  - Average Profit: 12%
  - Average Loss: 4%
  - Sharpe Ratio: 1.2
- **Implementation Notes**: 
  - Uses daily price data for calculations
  - Includes volume confirmation for entry signals
  - Adjusts position size based on volatility

### TF002: MACD Trend Strategy

- **ID**: TF002
- **Name**: MACD Trend Strategy
- **Category**: Trend Following
- **Risk Level**: Medium
- **Asset Types**: Stocks
- **Description**: Uses the Moving Average Convergence Divergence (MACD) indicator to identify trends and potential entry/exit points. Enters long positions when MACD line crosses above the signal line and short positions when it crosses below.
- **Parameters**:
  - `fast_period`: 12 (days)
  - `slow_period`: 26 (days)
  - `signal_period`: 9 (days)
  - `histogram_threshold`: 0.001 (threshold for signal confirmation)
- **Risk Parameters**:
  - `max_position_size_pct`: 0.04 (4% of portfolio per position)
  - `max_total_risk_pct`: 0.15 (15% of portfolio at risk)
  - `stop_loss_pct`: 0.06 (6% stop loss)
  - `take_profit_pct`: 0.18 (18% take profit)
  - `risk_reward_min`: 2.5 (minimum risk/reward ratio)
- **Performance Metrics**:
  - Win Rate: 52%
  - Average Profit: 15%
  - Average Loss: 5%
  - Sharpe Ratio: 1.3
- **Implementation Notes**: 
  - Uses both daily and 4-hour data for confirmation
  - Includes RSI filter to avoid overbought/oversold conditions
  - Adjusts entry timing based on volume profile

### TF003: Adaptive Trend Following

- **ID**: TF003
- **Name**: Adaptive Trend Following
- **Category**: Trend Following
- **Risk Level**: Medium-High
- **Asset Types**: Both
- **Description**: An adaptive trend following strategy that adjusts parameters based on market volatility. Uses a combination of moving averages and ADX (Average Directional Index) to identify strong trends.
- **Parameters**:
  - `atr_period`: 14 (days)
  - `adx_period`: 14 (days)
  - `adx_threshold`: 25 (minimum ADX for trend confirmation)
  - `volatility_lookback`: 20 (days)
  - `ma_type`: "EMA" (exponential moving average)
- **Risk Parameters**:
  - `max_position_size_pct`: 0.06 (6% of portfolio per position)
  - `max_total_risk_pct`: 0.25 (25% of portfolio at risk)
  - `stop_loss_pct`: Variable (based on ATR)
  - `take_profit_pct`: Variable (based on ATR and trend strength)
  - `risk_reward_min`: 2.0 (minimum risk/reward ratio)
- **Performance Metrics**:
  - Win Rate: 48%
  - Average Profit: 22%
  - Average Loss: 7%
  - Sharpe Ratio: 1.4
- **Implementation Notes**: 
  - Dynamically adjusts parameters based on market conditions
  - Uses ATR for position sizing and stop placement
  - Includes trend strength filter for entry confirmation

## Mean Reversion Strategies

### MR001: RSI Oversold/Overbought

- **ID**: MR001
- **Name**: RSI Oversold/Overbought
- **Category**: Mean Reversion
- **Risk Level**: Medium
- **Asset Types**: Stocks
- **Description**: Uses the Relative Strength Index (RSI) to identify oversold and overbought conditions. Enters long positions when RSI is below 30 (oversold) and short positions when RSI is above 70 (overbought).
- **Parameters**:
  - `rsi_period`: 14 (days)
  - `oversold_threshold`: 30
  - `overbought_threshold`: 70
  - `exit_rsi_low`: 50 (exit long when RSI crosses above 50)
  - `exit_rsi_high`: 50 (exit short when RSI crosses below 50)
- **Risk Parameters**:
  - `max_position_size_pct`: 0.03 (3% of portfolio per position)
  - `max_total_risk_pct`: 0.12 (12% of portfolio at risk)
  - `stop_loss_pct`: 0.05 (5% stop loss)
  - `take_profit_pct`: 0.10 (10% take profit)
  - `risk_reward_min`: 1.8 (minimum risk/reward ratio)
- **Performance Metrics**:
  - Win Rate: 65%
  - Average Profit: 8%
  - Average Loss: 4%
  - Sharpe Ratio: 1.1
- **Implementation Notes**: 
  - Works best in range-bound markets
  - Includes trend filter to avoid trading against strong trends
  - Uses volume confirmation for entry signals

### MR002: Bollinger Band Reversion

- **ID**: MR002
- **Name**: Bollinger Band Reversion
- **Category**: Mean Reversion
- **Risk Level**: Medium
- **Asset Types**: Stocks
- **Description**: Uses Bollinger Bands to identify potential reversal points. Enters long positions when price touches the lower band and short positions when price touches the upper band, with confirmation from other indicators.
- **Parameters**:
  - `bb_period`: 20 (days)
  - `bb_std_dev`: 2 (standard deviations)
  - `rsi_period`: 14 (days)
  - `rsi_oversold`: 30
  - `rsi_overbought`: 70
- **Risk Parameters**:
  - `max_position_size_pct`: 0.04 (4% of portfolio per position)
  - `max_total_risk_pct`: 0.16 (16% of portfolio at risk)
  - `stop_loss_pct`: 0.04 (4% stop loss)
  - `take_profit_pct`: 0.08 (8% take profit)
  - `risk_reward_min`: 1.5 (minimum risk/reward ratio)
- **Performance Metrics**:
  - Win Rate: 62%
  - Average Profit: 7%
  - Average Loss: 3.5%
  - Sharpe Ratio: 1.2
- **Implementation Notes**: 
  - Uses RSI for confirmation of reversal signals
  - Includes volume spike detection for entry confirmation
  - Adjusts position size based on distance from mean

### MR003: Statistical Arbitrage

- **ID**: MR003
- **Name**: Statistical Arbitrage
- **Category**: Mean Reversion
- **Risk Level**: High
- **Asset Types**: Both
- **Description**: A pairs trading strategy that identifies statistically correlated securities and trades the spread between them when it deviates from historical norms. Enters positions when the spread exceeds a statistical threshold.
- **Parameters**:
  - `lookback_period`: 60 (days)
  - `entry_threshold`: 2.0 (standard deviations)
  - `exit_threshold`: 0.5 (standard deviations)
  - `correlation_min`: 0.7 (minimum correlation coefficient)
  - `half_life_max`: 15 (maximum half-life of mean reversion in days)
- **Risk Parameters**:
  - `max_position_size_pct`: 0.05 (5% of portfolio per pair)
  - `max_total_risk_pct`: 0.25 (25% of portfolio at risk)
  - `stop_loss_pct`: 0.10 (10% stop loss on spread)
  - `max_holding_period`: 20 (days)
  - `risk_reward_min`: 1.5 (minimum risk/reward ratio)
- **Performance Metrics**:
  - Win Rate: 70%
  - Average Profit: 5%
  - Average Loss: 3%
  - Sharpe Ratio: 1.6
- **Implementation Notes**: 
  - Uses cointegration testing for pair selection
  - Implements dynamic hedge ratios
  - Includes regime detection to avoid trading during unstable periods

## Breakout Strategies

### BO001: Volatility Breakout

- **ID**: BO001
- **Name**: Volatility Breakout
- **Category**: Breakout
- **Risk Level**: High
- **Asset Types**: Both
- **Description**: Identifies consolidation patterns and enters positions when price breaks out with increased volatility. Uses Average True Range (ATR) to measure volatility and set profit targets and stop losses.
- **Parameters**:
  - `atr_period`: 14 (days)
  - `breakout_period`: 20 (days)
  - `volatility_multiplier`: 2.0 (for breakout confirmation)
  - `volume_threshold`: 1.5 (times average volume)
- **Risk Parameters**:
  - `max_position_size_pct`: 0.05 (5% of portfolio per position)
  - `max_total_risk_pct`: 0.20 (20% of portfolio at risk)
  - `stop_loss_atr`: 2.0 (ATR multiplier for stop loss)
  - `take_profit_atr`: 4.0 (ATR multiplier for take profit)
  - `risk_reward_min`: 2.0 (minimum risk/reward ratio)
- **Performance Metrics**:
  - Win Rate: 45%
  - Average Profit: 18%
  - Average Loss: 6%
  - Sharpe Ratio: 1.3
- **Implementation Notes**: 
  - Uses volume confirmation for breakout validation
  - Includes false breakout detection
  - Adjusts position size based on volatility

### BO002: Channel Breakout

- **ID**: BO002
- **Name**: Channel Breakout
- **Category**: Breakout
- **Risk Level**: Medium-High
- **Asset Types**: Stocks
- **Description**: Identifies price channels using Donchian Channels and enters positions when price breaks out of the channel. Uses confirmation indicators to filter out false breakouts.
- **Parameters**:
  - `channel_period`: 20 (days)
  - `confirmation_period`: 5 (days)
  - `atr_period`: 14 (days)
  - `momentum_threshold`: 0.5 (minimum momentum for confirmation)
- **Risk Parameters**:
  - `max_position_size_pct`: 0.04 (4% of portfolio per position)
  - `max_total_risk_pct`: 0.16 (16% of portfolio at risk)
  - `stop_loss_pct`: 0.07 (7% stop loss)
  - `take_profit_pct`: 0.21 (21% take profit)
  - `risk_reward_min`: 2.5 (minimum risk/reward ratio)
- **Performance Metrics**:
  - Win Rate: 42%
  - Average Profit: 20%
  - Average Loss: 7%
  - Sharpe Ratio: 1.2
- **Implementation Notes**: 
  - Uses ADX for trend strength confirmation
  - Includes pullback entry technique for better entry prices
  - Implements trailing stops after breakout confirmation

### BO003: Gap and Go

- **ID**: BO003
- **Name**: Gap and Go
- **Category**: Breakout
- **Risk Level**: High
- **Asset Types**: Stocks
- **Description**: Targets stocks that gap up or down at market open with high relative volume. Enters positions in the direction of the gap when price confirms the move after the first 15-30 minutes of trading.
- **Parameters**:
  - `gap_threshold`: 0.03 (3% minimum gap)
  - `volume_threshold`: 2.0 (times average volume)
  - `confirmation_period`: 30 (minutes)
  - `vwap_filter`: true (use VWAP as support/resistance)
- **Risk Parameters**:
  - `max_position_size_pct`: 0.03 (3% of portfolio per position)
  - `max_total_risk_pct`: 0.15 (15% of portfolio at risk)
  - `stop_loss_pct`: 0.04 (4% stop loss)
  - `take_profit_pct`: 0.12 (12% take profit)
  - `risk_reward_min`: 2.0 (minimum risk/reward ratio)
- **Performance Metrics**:
  - Win Rate: 55%
  - Average Profit: 10%
  - Average Loss: 4%
  - Sharpe Ratio: 1.4
- **Implementation Notes**: 
  - Only trades during the first 2 hours of the market
  - Uses pre-market high/low as support/resistance
  - Includes news catalyst screening

## Options Strategies

### OP001: Momentum Options

- **ID**: OP001
- **Name**: Momentum Options
- **Category**: Momentum
- **Risk Level**: High
- **Asset Types**: Options
- **Description**: Buys call or put options on stocks showing strong momentum signals. Uses a combination of technical indicators to identify stocks with potential for significant short-term moves.
- **Parameters**:
  - `momentum_period`: 10 (days)
  - `rsi_period`: 14 (days)
  - `macd_fast`: 12 (days)
  - `macd_slow`: 26 (days)
  - `macd_signal`: 9 (days)
  - `volume_threshold`: 1.5 (times average volume)
- **Risk Parameters**:
  - `max_position_size_pct`: 0.02 (2% of portfolio per position)
  - `max_total_risk_pct`: 0.10 (10% of portfolio at risk)
  - `stop_loss_pct`: 0.30 (30% stop loss on option price)
  - `take_profit_pct`: 0.90 (90% take profit on option price)
  - `days_to_expiration_min`: 30 (minimum days to expiration)
  - `days_to_expiration_max`: 60 (maximum days to expiration)
  - `delta_min`: 0.40 (minimum option delta)
  - `delta_max`: 0.60 (maximum option delta)
- **Performance Metrics**:
  - Win Rate: 40%
  - Average Profit: 75%
  - Average Loss: 25%
  - Sharpe Ratio: 1.2
- **Implementation Notes**: 
  - Focuses on liquid options with tight bid-ask spreads
  - Uses implied volatility percentile for option selection
  - Includes earnings calendar filter to avoid earnings surprises

### OP002: Volatility Skew Strategy

- **ID**: OP002
- **Name**: Volatility Skew Strategy
- **Category**: Volatility
- **Risk Level**: High
- **Asset Types**: Options
- **Description**: Exploits volatility skew by selling overpriced options and buying underpriced options based on implied volatility analysis. Typically implemented as vertical spreads to limit risk.
- **Parameters**:
  - `iv_rank_threshold`: 0.7 (minimum IV rank for selling options)
  - `iv_percentile_threshold`: 0.8 (minimum IV percentile)
  - `skew_threshold`: 0.1 (minimum skew difference)
  - `term_structure_filter`: true (use term structure for confirmation)
- **Risk Parameters**:
  - `max_position_size_pct`: 0.03 (3% of portfolio per position)
  - `max_total_risk_pct`: 0.15 (15% of portfolio at risk)
  - `max_loss_per_spread`: 0.02 (2% of portfolio)
  - `days_to_expiration_min`: 30 (minimum days to expiration)
  - `days_to_expiration_max`: 45 (maximum days to expiration)
  - `profit_target_pct`: 0.50 (50% of maximum potential profit)
- **Performance Metrics**:
  - Win Rate: 68%
  - Average Profit: 25%
  - Average Loss: 40%
  - Sharpe Ratio: 1.3
- **Implementation Notes**: 
  - Primarily uses vertical spreads (bull put, bear call)
  - Includes historical volatility comparison
  - Adjusts position size based on probability of profit

### OP003: Iron Condor Strategy

- **ID**: OP003
- **Name**: Iron Condor Strategy
- **Category**: Volatility
- **Risk Level**: Medium
- **Asset Types**: Options
- **Description**: Sells an out-of-the-money put spread and an out-of-the-money call spread simultaneously on the same underlying asset. Profits when the underlying asset remains within a specified range until expiration.
- **Parameters**:
  - `iv_rank_threshold`: 0.6 (minimum IV rank)
  - `expected_move_buffer`: 0.2 (20% buffer outside expected move)
  - `delta_short_options`: 0.16 (target delta for short options)
  - `delta_long_options`: 0.05 (target delta for long options)
- **Risk Parameters**:
  - `max_position_size_pct`: 0.04 (4% of portfolio per position)
  - `max_total_risk_pct`: 0.20 (20% of portfolio at risk)
  - `max_loss_per_condor`: 0.02 (2% of portfolio)
  - `days_to_expiration_min`: 30 (minimum days to expiration)
  - `days_to_expiration_max`: 45 (maximum days to expiration)
  - `profit_target_pct`: 0.30 (30% of maximum potential profit)
  - `loss_exit_pct`: 0.50 (50% of maximum potential loss)
- **Performance Metrics**:
  - Win Rate: 75%
  - Average Profit: 15%
  - Average Loss: 35%
  - Sharpe Ratio: 1.1
- **Implementation Notes**: 
  - Targets high IV rank but low IV percentile environments
  - Uses technical analysis to identify strong support/resistance levels
  - Includes adjustment strategies for defending positions

## Multi-Asset Strategies

### MA001: Sector Rotation

- **ID**: MA001
- **Name**: Sector Rotation
- **Category**: Multi-Asset
- **Risk Level**: Medium
- **Asset Types**: Both
- **Description**: Rotates capital between different market sectors based on relative strength and momentum. Overweights sectors showing strong performance and underweights or shorts weak sectors.
- **Parameters**:
  - `momentum_period`: 90 (days)
  - `relative_strength_period`: 60 (days)
  - `rebalance_frequency`: 30 (days)
  - `top_sectors_count`: 3 (number of top sectors to invest in)
- **Risk Parameters**:
  - `max_position_size_pct`: 0.10 (10% of portfolio per sector)
  - `max_total_risk_pct`: 0.30 (30% of portfolio at risk)
  - `stop_loss_pct`: 0.08 (8% stop loss)
  - `sector_concentration_max`: 0.40 (40% maximum in any single sector)
  - `risk_reward_min`: 1.5 (minimum risk/reward ratio)
- **Performance Metrics**:
  - Win Rate: 60%
  - Average Profit: 12%
  - Average Loss: 6%
  - Sharpe Ratio: 1.4
- **Implementation Notes**: 
  - Uses ETFs for sector exposure
  - Includes economic cycle analysis
  - Implements gradual position building and reduction

### MA002: Asset Allocation Strategy

- **ID**: MA002
- **Name**: Asset Allocation Strategy
- **Category**: Multi-Asset
- **Risk Level**: Low-Medium
- **Asset Types**: Both
- **Description**: Dynamically allocates capital across multiple asset classes (stocks, bonds, commodities, cash) based on market conditions, economic indicators, and relative performance.
- **Parameters**:
  - `trend_period`: 200 (days)
  - `volatility_period`: 20 (days)
  - `rebalance_frequency`: 30 (days)
  - `economic_indicators`: ["unemployment", "inflation", "gdp_growth", "interest_rates"]
- **Risk Parameters**:
  - `max_position_size_pct`: 0.30 (30% of portfolio per asset class)
  - `max_total_risk_pct`: 0.15 (15% of portfolio at risk)
  - `max_drawdown_pct`: 0.10 (10% maximum drawdown)
  - `cash_minimum_pct`: 0.05 (5% minimum cash allocation)
  - `risk_reward_min`: 1.2 (minimum risk/reward ratio)
- **Performance Metrics**:
  - Win Rate: 65%
  - Average Profit: 8%
  - Average Loss: 4%
  - Sharpe Ratio: 1.5
- **Implementation Notes**: 
  - Uses ETFs for asset class exposure
  - Includes risk parity principles for allocation
  - Implements tactical shifts based on market regime

## Risk Management

All strategies in KryptoBot adhere to the following risk management principles:

1. **Position Sizing**: No single position should exceed the specified percentage of the portfolio.
2. **Total Risk**: The total amount at risk across all positions should not exceed the specified percentage of the portfolio.
3. **Stop Losses**: All positions must have a stop loss order in place.
4. **Risk/Reward Ratio**: New positions should meet the minimum risk/reward ratio requirement.
5. **Drawdown Control**: Trading is reduced or halted if the maximum drawdown threshold is exceeded.
6. **Correlation Management**: Positions are monitored for correlation to avoid overexposure to similar market factors.
7. **Volatility Adjustment**: Position sizes are adjusted based on the volatility of the underlying asset.

## Adding New Strategies

To add a new strategy to KryptoBot:

1. Create a new strategy definition following the template in this document.
2. Implement the strategy logic in the `strategies.py` file.
3. Add the strategy parameters to the strategy manager.
4. Test the strategy in paper trading mode before using it with real money.
5. Document performance metrics and any implementation notes.

New strategies should be thoroughly backtested and validated before being added to the production system. All strategies should include proper risk management parameters and be compatible with the existing monitoring and notification systems. 