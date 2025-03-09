import logging
import os
from ml_enhancer import MLSignalEnhancer
from strategy_allocator import StrategyAllocator
from portfolio_optimizer import PortfolioOptimizer
from performance_analyzer import PerformanceAnalyzer
from parameter_tuner import AdaptiveParameterTuner
from market_data import MarketDataService
from strategies import TradingStrategy
from config import BREAKOUT_PARAMS, TREND_PARAMS
import alpaca_trade_api as tradeapi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ml_enhancer():
    """Test the ML Signal Enhancer"""
    print("\n=== Testing ML Signal Enhancer ===")
    
    # Initialize components
    api = tradeapi.REST(
        os.getenv('ALPACA_API_KEY'),
        os.getenv('ALPACA_SECRET_KEY'),
        base_url=os.getenv('ALPACA_BASE_URL')
    )
    market_data = MarketDataService(api)
    strategy = TradingStrategy()
    ml_enhancer = MLSignalEnhancer()
    
    # Get market data
    symbol = 'AAPL'
    data = market_data.get_market_data(symbol, timeframe='1D', limit=100)
    
    if data is None or data.empty:
        print(f"❌ Failed to get market data for {symbol}")
        return
        
    # Generate dummy training data
    print(f"Generating dummy training data for {symbol}...")
    historical_data, outcomes = ml_enhancer.generate_dummy_training_data(symbol, market_data, num_samples=50)
    
    if not historical_data:
        print("❌ Failed to generate dummy training data")
        return
        
    # Train the model
    print(f"Training ML model with {len(historical_data)} samples...")
    training_results = ml_enhancer.train(historical_data, [{}] * len(historical_data), outcomes)
    
    print(f"Training accuracy: {training_results['accuracy']:.2f}")
    
    # Test signal enhancement
    success_prob, trade_params = strategy.analyze_trade_opportunity(data)
    
    base_signal = {
        'probability': success_prob,
        **trade_params
    }
    
    enhanced_signal = ml_enhancer.enhance_signal(data, base_signal)
    
    print(f"Base probability: {success_prob:.2f}")
    print(f"ML probability: {enhanced_signal['ml_probability']:.2f}")
    print(f"Combined score: {enhanced_signal['combined_score']:.2f}")
    
    print("✅ ML Signal Enhancer test completed")

def test_strategy_allocator():
    """Test the Strategy Allocator"""
    print("\n=== Testing Strategy Allocator ===")
    
    # Initialize components
    api = tradeapi.REST(
        os.getenv('ALPACA_API_KEY'),
        os.getenv('ALPACA_SECRET_KEY'),
        base_url=os.getenv('ALPACA_BASE_URL')
    )
    market_data = MarketDataService(api)
    strategy = TradingStrategy()
    
    # Create strategy configurations
    strategies_config = {
        'breakout': BREAKOUT_PARAMS,
        'trend_following': TREND_PARAMS,
        'mean_reversion': {
            'bb_window': 20,
            'bb_std': 2,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70
        },
        'momentum': {
            'price_momentum_period': 5,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'adx_period': 14,
            'adx_threshold': 25
        }
    }
    
    strategy_allocator = StrategyAllocator(strategies_config)
    
    # Get market data
    symbol = 'AAPL'
    data = market_data.get_market_data(symbol, timeframe='1D', limit=100)
    
    if data is None or data.empty:
        print(f"❌ Failed to get market data for {symbol}")
        return
        
    # Detect market condition
    market_condition = strategy_allocator.detect_market_condition(data)
    print(f"Detected market condition: {market_condition}")
    
    # Get optimal strategy
    signal = strategy_allocator.get_optimal_strategy(symbol, data, strategy)
    
    if signal:
        print(f"Optimal strategy signal:")
        print(f"  Probability: {signal['probability']:.2f}")
        print(f"  Strategies used: {signal['strategies_used']}")
        print(f"  Entry price: ${signal['entry_price']:.2f}")
        print(f"  Stop loss: ${signal['stop_loss']:.2f}")
        print(f"  Take profit: ${signal['take_profit']:.2f}")
    else:
        print("❌ No valid strategy signal generated")
    
    print("✅ Strategy Allocator test completed")

def test_portfolio_optimizer():
    """Test the Portfolio Optimizer"""
    print("\n=== Testing Portfolio Optimizer ===")
    
    # Initialize components
    portfolio_optimizer = PortfolioOptimizer(
        max_positions=10,
        sector_max_allocation=0.30,
        stock_max_allocation=0.15
    )
    
    # Test sector info retrieval
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    print("Testing sector info retrieval:")
    for symbol in symbols:
        sector_info = portfolio_optimizer.get_sector_info(symbol)
        print(f"  {symbol}: {sector_info['sector']} / {sector_info['industry']}")
    
    # Test portfolio optimization
    current_positions = {
        'AAPL': {
            'quantity': 10,
            'current_price': 200.0,
            'unrealized_pl': 500.0
        },
        'MSFT': {
            'quantity': 5,
            'current_price': 400.0,
            'unrealized_pl': 300.0
        }
    }
    
    potential_trades = [
        {
            'symbol': 'GOOGL',
            'probability': 0.85,
            'entry_price': 170.0,
            'stop_loss': 160.0,
            'take_profit': 190.0,
            'position_size_modifier': 1.0
        },
        {
            'symbol': 'AMZN',
            'probability': 0.75,
            'entry_price': 180.0,
            'stop_loss': 170.0,
            'take_profit': 200.0,
            'position_size_modifier': 0.8
        }
    ]
    
    account_value = 10000.0
    
    # Calculate current allocation
    allocation = portfolio_optimizer.calculate_current_allocation(current_positions, account_value)
    
    print("\nCurrent allocation:")
    for symbol, alloc in allocation['stock_allocation'].items():
        print(f"  {symbol}: {alloc:.1%}")
        
    print("\nSector allocation:")
    for sector, alloc in allocation['sector_allocation'].items():
        print(f"  {sector}: {alloc:.1%}")
    
    # Optimize portfolio
    optimized_trades = portfolio_optimizer.optimize_portfolio(
        current_positions, potential_trades, account_value
    )
    
    print("\nOptimized trades:")
    for trade in optimized_trades:
        print(f"  {trade['symbol']}: Entry=${trade['entry_price']:.2f}, Stop=${trade['stop_loss']:.2f}, Target=${trade['take_profit']:.2f}")
    
    # Test rebalancing suggestions
    rebalance_actions = portfolio_optimizer.suggest_rebalancing(current_positions, account_value)
    
    print("\nRebalancing suggestions:")
    if rebalance_actions:
        for action in rebalance_actions:
            print(f"  {action['action']} {action['symbol']} by {action['shares']} shares: {action['reason']}")
    else:
        print("  No rebalancing needed")
    
    print("✅ Portfolio Optimizer test completed")

def test_performance_analyzer():
    """Test the Performance Analyzer"""
    print("\n=== Testing Performance Analyzer ===")
    
    # Initialize components
    performance_analyzer = PerformanceAnalyzer()
    
    # Add some sample trades
    print("Adding sample trades...")
    
    # Winning trades
    for i in range(7):
        performance_analyzer.add_trade({
            'symbol': 'AAPL',
            'entry_time': '2023-01-01T10:00:00',
            'exit_time': '2023-01-02T10:00:00',
            'entry_price': 150.0,
            'exit_price': 155.0,
            'shares': 10,
            'profit': 50.0,
            'status': 'closed',
            'market_condition': 'bullish_trend',
            'day_of_week': 'Monday',
            'strategy': ['trend_following']
        })
    
    # Losing trades
    for i in range(3):
        performance_analyzer.add_trade({
            'symbol': 'MSFT',
            'entry_time': '2023-01-03T10:00:00',
            'exit_time': '2023-01-04T10:00:00',
            'entry_price': 300.0,
            'exit_price': 295.0,
            'shares': 5,
            'profit': -25.0,
            'status': 'closed',
            'market_condition': 'ranging',
            'day_of_week': 'Tuesday',
            'strategy': ['breakout']
        })
    
    # Calculate metrics
    metrics = performance_analyzer.calculate_metrics()
    
    print("\nPerformance metrics:")
    print(f"  Total trades: {metrics['total_trades']}")
    print(f"  Win rate: {metrics['win_rate']:.1%}")
    print(f"  Profit factor: {metrics['profit_factor']:.2f}")
    print(f"  Total profit: ${metrics['total_profit']:.2f}")
    
    # Analyze by factor
    market_regime_analysis = performance_analyzer.analyze_by_factor('market_condition')
    
    print("\nPerformance by market condition:")
    for condition, stats in market_regime_analysis.items():
        print(f"  {condition}: {stats['win_rate']:.1%} win rate, ${stats['profit']:.2f} profit")
    
    # Get improvement suggestions
    suggestions = performance_analyzer.suggest_improvements()
    
    print("\nImprovement suggestions:")
    for suggestion in suggestions:
        print(f"  {suggestion['area']} ({suggestion['priority']}): {suggestion['suggestion']}")
        print(f"    Current: {suggestion['current']}, Target: {suggestion['target']}")
    
    # Generate report
    print("\nGenerating performance report...")
    report = performance_analyzer.generate_report()
    
    print(f"Report generated with {len(report['suggestions'])} suggestions")
    
    print("✅ Performance Analyzer test completed")

def test_parameter_tuner():
    """Test the Adaptive Parameter Tuner"""
    print("\n=== Testing Adaptive Parameter Tuner ===")
    
    # Initialize with base parameters
    base_params = {
        'price_threshold': 0.02,
        'volume_threshold': 2.0,
        'lookback_period': 20,
        'consolidation_threshold': 0.01,
        'short_ma': 9,
        'medium_ma': 21,
        'long_ma': 50
    }
    
    # Parameter bounds
    param_bounds = {
        'price_threshold': {'min': 0.005, 'max': 0.05},
        'volume_threshold': {'min': 1.2, 'max': 3.0},
        'lookback_period': {'min': 10, 'max': 30}
    }
    
    parameter_tuner = AdaptiveParameterTuner(
        base_params=base_params,
        param_bounds=param_bounds,
        optimization_frequency=7,
        learning_rate=0.1
    )
    
    # Check if optimization is due
    is_due = parameter_tuner.should_optimize()
    print(f"Optimization due: {is_due}")
    
    # Update performance history
    print("Updating performance history...")
    
    # Good performance
    parameter_tuner.update_performance({
        'win_rate': 0.7,
        'profit_factor': 2.0,
        'sharpe_ratio': 1.5
    })
    
    # Test parameter tuning
    print("Tuning parameters for 'volatile' market regime...")
    tuned_params = parameter_tuner.tune_parameters(
        {
            'win_rate': 0.6,
            'profit_factor': 1.8,
            'sharpe_ratio': 1.2
        },
        'volatile'
    )
    
    print("\nTuned parameters:")
    for param, value in tuned_params.items():
        original = base_params.get(param, 'N/A')
        print(f"  {param}: {original} -> {value}")
    
    # Reset parameters
    print("\nResetting parameters to base values...")
    reset_params = parameter_tuner.reset_to_base()
    
    print("✅ Parameter Tuner test completed")

if __name__ == "__main__":
    print("Testing Enhanced Trading Bot Features")
    
    try:
        test_ml_enhancer()
        test_strategy_allocator()
        test_portfolio_optimizer()
        test_performance_analyzer()
        test_parameter_tuner()
        
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        raise 