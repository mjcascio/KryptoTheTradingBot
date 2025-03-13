"""
Anomaly Detector Plugin - Detects market anomalies using deep learning.

This plugin provides real-time market anomaly detection capabilities for the KryptoBot trading system.
It uses deep neural networks to continuously monitor market data and flag unusual patterns or anomalies
that may indicate trading opportunities or risks.
"""

from .anomaly_detector import AnomalyDetectorPlugin

__all__ = ['AnomalyDetectorPlugin'] 