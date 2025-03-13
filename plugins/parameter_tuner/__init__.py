"""
Parameter Tuner Plugin - Optimizes strategy parameters using quantum-inspired algorithms.

This plugin provides parameter optimization capabilities for the KryptoBot trading system.
It uses quantum-inspired algorithms such as simulated annealing and quantum particle swarm
optimization to efficiently search the parameter space and find optimal strategy parameters.
"""

from .parameter_tuner import ParameterTunerPlugin

__all__ = ['ParameterTunerPlugin'] 