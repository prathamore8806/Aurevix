"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    AUREVIX TRAINING MODES PACKAGE                            ║
║                   🌟 Training Modes Initialization 🌟                         ║
╚═══════════════════════════════════════════════════════════════════════════════╝

This package contains all training mode implementations:
1. NeuralPracticeMode - Basic gesture training
2. GestureAnalyticsMode - Performance analytics with heatmaps
3. ReflexChallengeMode - Speed and memory challenges
4. AdaptiveTrainerMode - AI-adjusted difficulty training
"""

from .neural_practice import NeuralPracticeMode
from .gesture_analytics import GestureAnalyticsMode
from .reflex_challenge import ReflexChallengeMode
from .adaptive_trainer import AdaptiveTrainerMode

__all__ = [
    'NeuralPracticeMode',
    'GestureAnalyticsMode', 
    'ReflexChallengeMode',
    'AdaptiveTrainerMode'
]

__version__ = "1.0.0"
__author__ = "Aurevix Team"
