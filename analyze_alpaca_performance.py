#!/usr/bin/env python3
"""
Analyze Alpaca trading performance.

This script analyzes your Alpaca trading performance, including profit/loss,
win rate, Sharpe ratio, and other metrics. It also generates visualizations
of your trading performance.
"""

import os
import sys
import json
import logging
import argparse
import datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import requests

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/alpaca_performance.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("alpaca_performance")

# Load environment variables
load_dotenv()

# Alpaca API credentials
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

# Check if credentials are available
if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
    logger.error("Alpaca API credentials not found in .env file")
    sys.exit(1)

# Headers for Alpaca API requests
HEADERS = {
    "APCA-API-KEY-ID": ALPACA_API_KEY,
    "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY,
    "Content-Type": "application/json"
}

def get_account():
    """
    Get account information from Alpaca API.
    
    Returns:
        dict: Account information if successful, None otherwise
    """
    try:
        response = requests.get(
            f"{ALPACA_BASE_URL}/v2/account",
            headers=HEADERS
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get account: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting account: {str(e)}")
        return None

def get_portfolio_history(period="1M", timeframe="1D"):
    """
    Get portfolio history from Alpaca API.
    
    Args:
        period (str): Time period ('1D', '1W', '1M', '3M', '1A', 'all')
        timeframe (str): Time frame ('1Min', '5Min', '15Min', '1H', '1D')
        
    Returns:
        dict: Portfolio history if successful, None otherwise
    """
    try:
        response = requests.get(
            f"{ALPACA_BASE_URL}/v2/account/portfolio/history",
            headers=HEADERS,
            params={
                "period": period,
                "timeframe": timeframe
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get portfolio history: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting portfolio history: {str(e)}")
        return None

def get_orders(status="closed", limit=500, after=None):
    """
    Get orders from Alpaca API.
    
    Args:
        status (str): Order status ('open', 'closed', 'all')
        limit (int): Maximum number of orders to return
        after (str): Get orders after this timestamp
        
    Returns:
        list: Orders if successful, empty list otherwise
    """
    try:
        params = {
            "status": status,
            "limit": limit
        }
        
        if after:
            params["after"] = after
            
        response = requests.get(
            f"{ALPACA_BASE_URL}/v2/orders",
            headers=HEADERS,
            params=params
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get orders: {response.text}")
            return []
            
    except Exception as e:
        logger.error(f"Error getting orders: {str(e)}")
        return []

def calculate_metrics(orders):
    """
    Calculate performance metrics from orders.
    
    Args:
        orders (list): List of orders
        
    Returns:
        dict: Performance metrics
    """
    if not orders:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "avg_pnl": 0,
            "max_profit": 0,
            "max_loss": 0,
            "profit_factor": 0,
            "avg_win": 0,
            "avg_loss": 0,
            "risk_reward_ratio": 0
        }
    
    # Filter filled orders
    filled_orders = [order for order in orders if order.get("status") == "filled"]
    
    # Group orders by symbol and side to identify round trips
    trades = []
    order_map = {}
    
    for order in filled_orders:
        symbol = order.get("symbol")
        side = order.get("side")
        qty = float(order.get("qty", 0))
        filled_price = float(order.get("filled_avg_price", 0))
        filled_at = order.get("filled_at")
        
        if not filled_at:
            continue
            
        key = f"{symbol}_{side}"
        
        if key not in order_map:
            order_map[key] = []
            
        order_map[key].append({
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "price": filled_price,
            "filled_at": filled_at
        })
    
    # Match buy and sell orders to create trades
    for symbol in set([order.get("symbol") for order in filled_orders]):
        buy_key = f"{symbol}_buy"
        sell_key = f"{symbol}_sell"
        
        if buy_key in order_map and sell_key in order_map:
            buy_orders = sorted(order_map[buy_key], key=lambda x: x["filled_at"])
            sell_orders = sorted(order_map[sell_key], key=lambda x: x["filled_at"])
            
            # Match buy and sell orders
            for buy in buy_orders:
                for sell in sell_orders:
                    if buy["qty"] == sell["qty"]:
                        # Calculate profit/loss
                        entry_price = buy["price"]
                        exit_price = sell["price"]
                        qty = buy["qty"]
                        pnl = (exit_price - entry_price) * qty
                        
                        trades.append({
                            "symbol": symbol,
                            "entry_price": entry_price,
                            "exit_price": exit_price,
                            "qty": qty,
                            "pnl": pnl,
                            "entry_date": buy["filled_at"],
                            "exit_date": sell["filled_at"]
                        })
                        
                        # Remove matched orders
                        buy_orders.remove(buy)
                        sell_orders.remove(sell)
                        break
    
    # Calculate metrics
    total_trades = len(trades)
    winning_trades = len([trade for trade in trades if trade["pnl"] > 0])
    losing_trades = len([trade for trade in trades if trade["pnl"] < 0])
    
    win_rate = winning_trades / total_trades if total_trades > 0 else 0
    
    total_pnl = sum([trade["pnl"] for trade in trades])
    avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
    
    max_profit = max([trade["pnl"] for trade in trades]) if trades else 0
    max_loss = min([trade["pnl"] for trade in trades]) if trades else 0
    
    total_profit = sum([trade["pnl"] for trade in trades if trade["pnl"] > 0])
    total_loss = abs(sum([trade["pnl"] for trade in trades if trade["pnl"] < 0]))
    
    profit_factor = total_profit / total_loss if total_loss > 0 else 0
    
    avg_win = total_profit / winning_trades if winning_trades > 0 else 0
    avg_loss = total_loss / losing_trades if losing_trades > 0 else 0
    
    risk_reward_ratio = avg_win / abs(avg_loss) if avg_loss != 0 else 0
    
    return {
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": win_rate,
        "total_pnl": total_pnl,
        "avg_pnl": avg_pnl,
        "max_profit": max_profit,
        "max_loss": max_loss,
        "profit_factor": profit_factor,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "risk_reward_ratio": risk_reward_ratio,
        "trades": trades
    }

def calculate_sharpe_ratio(portfolio_history):
    """
    Calculate Sharpe ratio from portfolio history.
    
    Args:
        portfolio_history (dict): Portfolio history
        
    Returns:
        float: Sharpe ratio
    """
    if not portfolio_history or "equity" not in portfolio_history:
        return 0
    
    equity = portfolio_history["equity"]
    
    if not equity or len(equity) < 2:
        return 0
    
    # Calculate daily returns
    equity_series = pd.Series(equity)
    daily_returns = equity_series.pct_change().dropna()
    
    # Calculate Sharpe ratio (assuming risk-free rate of 0)
    sharpe_ratio = np.sqrt(252) * daily_returns.mean() / daily_returns.std()
    
    return sharpe_ratio

def calculate_drawdown(portfolio_history):
    """
    Calculate maximum drawdown from portfolio history.
    
    Args:
        portfolio_history (dict): Portfolio history
        
    Returns:
        float: Maximum drawdown as a percentage
    """
    if not portfolio_history or "equity" not in portfolio_history:
        return 0
    
    equity = portfolio_history["equity"]
    
    if not equity or len(equity) < 2:
        return 0
    
    # Calculate drawdown
    equity_series = pd.Series(equity)
    rolling_max = equity_series.cummax()
    drawdown = (equity_series - rolling_max) / rolling_max
    
    return drawdown.min()

def plot_equity_curve(portfolio_history, output_dir):
    """
    Plot equity curve from portfolio history.
    
    Args:
        portfolio_history (dict): Portfolio history
        output_dir (str): Output directory for plots
    """
    if not portfolio_history or "equity" not in portfolio_history or "timestamp" not in portfolio_history:
        logger.error("Invalid portfolio history for equity curve")
        return
    
    equity = portfolio_history["equity"]
    timestamps = portfolio_history["timestamp"]
    
    if not equity or not timestamps or len(equity) != len(timestamps):
        logger.error("Invalid data for equity curve")
        return
    
    # Convert timestamps to datetime
    dates = [datetime.datetime.fromtimestamp(ts) for ts in timestamps]
    
    # Create DataFrame
    df = pd.DataFrame({
        "date": dates,
        "equity": equity
    })
    
    # Plot equity curve
    plt.figure(figsize=(12, 6))
    plt.plot(df["date"], df["equity"])
    plt.title("Equity Curve")
    plt.xlabel("Date")
    plt.ylabel("Equity ($)")
    plt.grid(True)
    plt.tight_layout()
    
    # Save plot
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, "equity_curve.png"))
    plt.close()

def plot_daily_returns(portfolio_history, output_dir):
    """
    Plot daily returns from portfolio history.
    
    Args:
        portfolio_history (dict): Portfolio history
        output_dir (str): Output directory for plots
    """
    if not portfolio_history or "equity" not in portfolio_history or "timestamp" not in portfolio_history:
        logger.error("Invalid portfolio history for daily returns")
        return
    
    equity = portfolio_history["equity"]
    timestamps = portfolio_history["timestamp"]
    
    if not equity or not timestamps or len(equity) != len(timestamps):
        logger.error("Invalid data for daily returns")
        return
    
    # Convert timestamps to datetime
    dates = [datetime.datetime.fromtimestamp(ts) for ts in timestamps]
    
    # Create DataFrame
    df = pd.DataFrame({
        "date": dates,
        "equity": equity
    })
    
    # Calculate daily returns
    df["daily_return"] = df["equity"].pct_change()
    
    # Remove NaN values
    df = df.dropna()
    
    # Plot daily returns
    plt.figure(figsize=(12, 6))
    plt.bar(df["date"], df["daily_return"] * 100)
    plt.title("Daily Returns")
    plt.xlabel("Date")
    plt.ylabel("Return (%)")
    plt.grid(True)
    plt.tight_layout()
    
    # Save plot
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, "daily_returns.png"))
    plt.close()

def plot_drawdown(portfolio_history, output_dir):
    """
    Plot drawdown from portfolio history.
    
    Args:
        portfolio_history (dict): Portfolio history
        output_dir (str): Output directory for plots
    """
    if not portfolio_history or "equity" not in portfolio_history or "timestamp" not in portfolio_history:
        logger.error("Invalid portfolio history for drawdown")
        return
    
    equity = portfolio_history["equity"]
    timestamps = portfolio_history["timestamp"]
    
    if not equity or not timestamps or len(equity) != len(timestamps):
        logger.error("Invalid data for drawdown")
        return
    
    # Convert timestamps to datetime
    dates = [datetime.datetime.fromtimestamp(ts) for ts in timestamps]
    
    # Create DataFrame
    df = pd.DataFrame({
        "date": dates,
        "equity": equity
    })
    
    # Calculate drawdown
    df["rolling_max"] = df["equity"].cummax()
    df["drawdown"] = (df["equity"] - df["rolling_max"]) / df["rolling_max"] * 100
    
    # Plot drawdown
    plt.figure(figsize=(12, 6))
    plt.fill_between(df["date"], df["drawdown"], 0, color="red", alpha=0.3)
    plt.plot(df["date"], df["drawdown"], color="red")
    plt.title("Drawdown")
    plt.xlabel("Date")
    plt.ylabel("Drawdown (%)")
    plt.grid(True)
    plt.tight_layout()
    
    # Save plot
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, "drawdown.png"))
    plt.close()

def plot_win_loss_distribution(metrics, output_dir):
    """
    Plot win/loss distribution from metrics.
    
    Args:
        metrics (dict): Performance metrics
        output_dir (str): Output directory for plots
    """
    if not metrics or "trades" not in metrics or not metrics["trades"]:
        logger.error("Invalid metrics for win/loss distribution")
        return
    
    trades = metrics["trades"]
    
    # Extract profit/loss values
    pnl_values = [trade["pnl"] for trade in trades]
    
    # Plot histogram
    plt.figure(figsize=(12, 6))
    plt.hist(pnl_values, bins=20, alpha=0.7)
    plt.axvline(0, color="red", linestyle="--")
    plt.title("Win/Loss Distribution")
    plt.xlabel("Profit/Loss ($)")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.tight_layout()
    
    # Save plot
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, "win_loss_distribution.png"))
    plt.close()

def plot_cumulative_pnl(metrics, output_dir):
    """
    Plot cumulative P&L from metrics.
    
    Args:
        metrics (dict): Performance metrics
        output_dir (str): Output directory for plots
    """
    if not metrics or "trades" not in metrics or not metrics["trades"]:
        logger.error("Invalid metrics for cumulative P&L")
        return
    
    trades = sorted(metrics["trades"], key=lambda x: x["exit_date"])
    
    # Calculate cumulative P&L
    dates = [parse(trade["exit_date"]) for trade in trades]
    pnl_values = [trade["pnl"] for trade in trades]
    cumulative_pnl = np.cumsum(pnl_values)
    
    # Plot cumulative P&L
    plt.figure(figsize=(12, 6))
    plt.plot(dates, cumulative_pnl)
    plt.title("Cumulative P&L")
    plt.xlabel("Date")
    plt.ylabel("Cumulative P&L ($)")
    plt.grid(True)
    plt.tight_layout()
    
    # Save plot
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, "cumulative_pnl.png"))
    plt.close()

def generate_performance_report(metrics, portfolio_history, account, output_dir):
    """
    Generate performance report.
    
    Args:
        metrics (dict): Performance metrics
        portfolio_history (dict): Portfolio history
        account (dict): Account information
        output_dir (str): Output directory for report
    """
    # Calculate additional metrics
    sharpe_ratio = calculate_sharpe_ratio(portfolio_history)
    max_drawdown = calculate_drawdown(portfolio_history)
    
    # Create report
    report = {
        "generated_at": datetime.datetime.now().isoformat(),
        "account": {
            "id": account.get("id", "N/A"),
            "status": account.get("status", "N/A"),
            "equity": float(account.get("equity", 0)),
            "buying_power": float(account.get("buying_power", 0)),
            "cash": float(account.get("cash", 0)),
            "portfolio_value": float(account.get("portfolio_value", 0))
        },
        "performance": {
            "total_trades": metrics["total_trades"],
            "winning_trades": metrics["winning_trades"],
            "losing_trades": metrics["losing_trades"],
            "win_rate": metrics["win_rate"],
            "total_pnl": metrics["total_pnl"],
            "avg_pnl": metrics["avg_pnl"],
            "max_profit": metrics["max_profit"],
            "max_loss": metrics["max_loss"],
            "profit_factor": metrics["profit_factor"],
            "avg_win": metrics["avg_win"],
            "avg_loss": metrics["avg_loss"],
            "risk_reward_ratio": metrics["risk_reward_ratio"],
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown
        }
    }
    
    # Save report
    os.makedirs(output_dir, exist_ok=True)
    report_file = os.path.join(output_dir, f"performance_report_{datetime.datetime.now().strftime('%Y%m%d')}.json")
    
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Performance report saved to {report_file}")
    
    return report

def print_performance_summary(metrics, portfolio_history, account):
    """
    Print performance summary.
    
    Args:
        metrics (dict): Performance metrics
        portfolio_history (dict): Portfolio history
        account (dict): Account information
    """
    # Calculate additional metrics
    sharpe_ratio = calculate_sharpe_ratio(portfolio_history)
    max_drawdown = calculate_drawdown(portfolio_history)
    
    # Print summary
    print("\n" + "=" * 50)
    print("ALPACA TRADING PERFORMANCE SUMMARY")
    print("=" * 50)
    
    print("\nACCOUNT INFORMATION:")
    print(f"Account ID: {account.get('id', 'N/A')}")
    print(f"Status: {account.get('status', 'N/A')}")
    print(f"Equity: ${float(account.get('equity', 0)):.2f}")
    print(f"Buying Power: ${float(account.get('buying_power', 0)):.2f}")
    print(f"Cash: ${float(account.get('cash', 0)):.2f}")
    print(f"Portfolio Value: ${float(account.get('portfolio_value', 0)):.2f}")
    
    print("\nPERFORMANCE METRICS:")
    print(f"Total Trades: {metrics['total_trades']}")
    print(f"Winning Trades: {metrics['winning_trades']}")
    print(f"Losing Trades: {metrics['losing_trades']}")
    print(f"Win Rate: {metrics['win_rate']:.2%}")
    print(f"Total P&L: ${metrics['total_pnl']:.2f}")
    print(f"Average P&L: ${metrics['avg_pnl']:.2f}")
    print(f"Maximum Profit: ${metrics['max_profit']:.2f}")
    print(f"Maximum Loss: ${metrics['max_loss']:.2f}")
    print(f"Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"Average Win: ${metrics['avg_win']:.2f}")
    print(f"Average Loss: ${metrics['avg_loss']:.2f}")
    print(f"Risk/Reward Ratio: {metrics['risk_reward_ratio']:.2f}")
    print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
    print(f"Maximum Drawdown: {max_drawdown:.2%}")
    
    print("\n" + "=" * 50)
    print("VISUALIZATION FILES:")
    print("=" * 50)
    print("1. equity_curve.png - Equity curve over time")
    print("2. daily_returns.png - Daily returns histogram")
    print("3. drawdown.png - Drawdown over time")
    print("4. win_loss_distribution.png - Distribution of winning and losing trades")
    print("5. cumulative_pnl.png - Cumulative P&L over time")
    print("\nPerformance report saved to reports/performance_report_YYYYMMDD.json")

def main():
    """Main function to parse arguments and analyze performance."""
    parser = argparse.ArgumentParser(description="Analyze Alpaca trading performance")
    
    # Optional arguments
    parser.add_argument("--days", type=int, default=30, help="Number of days to analyze")
    parser.add_argument("--output", type=str, default="reports", help="Output directory for reports and plots")
    
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    try:
        # Get account information
        account = get_account()
        if not account:
            logger.error("Failed to get account information")
            return 1
        
        # Calculate date range
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=args.days)
        
        # Get portfolio history
        portfolio_history = get_portfolio_history(period=f"{args.days}D", timeframe="1D")
        if not portfolio_history:
            logger.error("Failed to get portfolio history")
            return 1
        
        # Get orders
        orders = get_orders(status="closed", after=start_date.isoformat())
        if not orders:
            logger.warning("No orders found for the specified period")
        
        # Calculate metrics
        metrics = calculate_metrics(orders)
        
        # Generate plots
        plot_equity_curve(portfolio_history, args.output)
        plot_daily_returns(portfolio_history, args.output)
        plot_drawdown(portfolio_history, args.output)
        
        if metrics["trades"]:
            plot_win_loss_distribution(metrics, args.output)
            plot_cumulative_pnl(metrics, args.output)
        
        # Generate report
        generate_performance_report(metrics, portfolio_history, account, args.output)
        
        # Print summary
        print_performance_summary(metrics, portfolio_history, account)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error analyzing performance: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 