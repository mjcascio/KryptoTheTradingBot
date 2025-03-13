"""Market analysis functionality for the KryptoBot Trading System."""

from datetime import datetime, timedelta
import logging
import yfinance as yf
from typing import Dict, List, Any
from config.constants import SECTOR_MAPPING, RECOMMENDED_ALLOCATIONS

logger = logging.getLogger(__name__)

def get_sector_mappings(symbols: List[str]) -> Dict[str, str]:
    """Get sector mappings for a list of stock symbols"""
    result = {}
    for symbol in symbols:
        if symbol in SECTOR_MAPPING:
            result[symbol] = SECTOR_MAPPING[symbol]
        else:
            # If not in our mapping, try to fetch from yfinance
            try:
                stock = yf.Ticker(symbol)
                info = stock.info
                if 'sector' in info and info['sector']:
                    result[symbol] = info['sector']
                else:
                    result[symbol] = "Unknown"
            except Exception as e:
                logger.warning(f"Could not get sector for {symbol}: {str(e)}")
                result[symbol] = "Unknown"
    return result

def calculate_sector_allocation(positions: Dict[str, Dict], sector_mappings: Dict[str, str]) -> Dict[str, float]:
    """Calculate current sector allocation based on positions"""
    sector_values = {}
    total_value = 0
    
    # Calculate total value and value per sector
    for symbol, position in positions.items():
        if 'quantity' in position and 'current_price' in position:
            position_value = position['quantity'] * position['current_price']
            total_value += position_value
            
            sector = sector_mappings.get(symbol, "Unknown")
            if sector in sector_values:
                sector_values[sector] += position_value
            else:
                sector_values[sector] = position_value
    
    # Calculate percentages
    sector_allocation = {}
    if total_value > 0:
        for sector, value in sector_values.items():
            sector_allocation[sector] = value / total_value
    
    return sector_allocation

def get_recommended_allocation() -> Dict[str, float]:
    """Get recommended sector allocation based on current market conditions"""
    # This could be enhanced to dynamically determine market conditions
    # For now, we'll use a neutral market assumption
    return RECOMMENDED_ALLOCATIONS["neutral_market"]

def calculate_correlation_matrix(symbols: List[str]) -> Dict:
    """Calculate correlation matrix for a list of stock symbols"""
    if not symbols:
        return {"error": "No symbols provided"}
    
    try:
        # Get historical data for the past year
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        # Fetch data from yfinance
        data = yf.download(symbols, start=start_date, end=end_date)['Adj Close']
        
        # Calculate correlation matrix
        correlation = data.corr().round(2)
        
        # Convert to dictionary format for JSON
        result = {
            "symbols": symbols,
            "matrix": correlation.to_dict()
        }
        
        return result
    except Exception as e:
        logger.error(f"Error calculating correlation matrix: {str(e)}")
        return {"error": str(e)}

def calculate_diversification_score(sector_allocation: Dict[str, float]) -> float:
    """Calculate a diversification score (0-100) based on sector allocation"""
    if not sector_allocation:
        return 0
    
    # Calculate Herfindahl-Hirschman Index (HHI)
    # Lower HHI means better diversification
    hhi = sum(pct**2 for pct in sector_allocation.values())
    
    # Convert to a 0-100 score where 100 is perfectly diversified
    # Perfect diversification would be 1/n for each sector
    # For 9 sectors, perfect HHI would be 9 * (1/9)^2 = 1/9 ≈ 0.111
    perfect_hhi = 1 / len(RECOMMENDED_ALLOCATIONS["neutral_market"])
    
    # Scale the score: 100 for perfect diversification, 0 for complete concentration
    score = max(0, min(100, 100 * (1 - (hhi - perfect_hhi) / (1 - perfect_hhi))))
    
    return round(score, 1)

def generate_diversification_recommendations(
    positions: Dict[str, Dict],
    current_allocation: Dict[str, float],
    recommended_allocation: Dict[str, float],
    correlation_data: Dict,
    risk_metrics: Dict
) -> Dict[str, Any]:
    """Generate recommendations for improving portfolio diversification"""
    recommendations = {
        "overweight_sectors": [],
        "underweight_sectors": [],
        "high_correlation_pairs": [],
        "suggested_additions": []
    }
    
    # Identify overweight and underweight sectors
    for sector, recommended_pct in recommended_allocation.items():
        current_pct = current_allocation.get(sector, 0)
        difference = current_pct - recommended_pct
        
        if difference > 0.05:  # More than 5% overweight
            recommendations["overweight_sectors"].append({
                "sector": sector,
                "current_allocation": current_pct,
                "recommended_allocation": recommended_pct,
                "difference": difference
            })
        elif difference < -0.05:  # More than 5% underweight
            recommendations["underweight_sectors"].append({
                "sector": sector,
                "current_allocation": current_pct,
                "recommended_allocation": recommended_pct,
                "difference": difference
            })
    
    # Identify highly correlated pairs
    if "matrix" in correlation_data and "symbols" in correlation_data:
        symbols = correlation_data["symbols"]
        matrix = correlation_data["matrix"]
        
        for i, symbol1 in enumerate(symbols):
            for j, symbol2 in enumerate(symbols):
                if i < j:  # Only check each pair once
                    correlation = matrix.get(symbol1, {}).get(symbol2, 0)
                    if correlation > 0.8:  # High correlation threshold
                        recommendations["high_correlation_pairs"].append({
                            "symbol1": symbol1,
                            "symbol2": symbol2,
                            "correlation": correlation
                        })
    
    # Suggest additions from watchlist for underweight sectors
    underweight_sectors = [r["sector"] for r in recommendations["underweight_sectors"]]
    if underweight_sectors:
        for symbol in SECTOR_MAPPING.keys():
            if symbol not in positions:
                sector = SECTOR_MAPPING.get(symbol)
                if sector in underweight_sectors:
                    recommendations["suggested_additions"].append({
                        "symbol": symbol,
                        "sector": sector
                    })
    
    return recommendations 