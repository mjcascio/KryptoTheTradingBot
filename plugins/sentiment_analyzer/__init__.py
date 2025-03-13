"""
Sentiment Analyzer Plugin - Analyzes market sentiment from various sources.

This plugin provides sentiment analysis capabilities for the KryptoBot trading system.
It analyzes sentiment from news articles, social media, and financial reports to
provide insights that can be used to adjust trading strategies.
"""

from .sentiment_analyzer import SentimentAnalyzerPlugin

__all__ = ['SentimentAnalyzerPlugin'] 