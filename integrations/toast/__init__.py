"""Read-only Toast POS API puller for daily sales and cash flow baselines.

Hard exclusions (do not wire here): inventory automation, order adjustments,
bank sweeps, velocity banking, Home Assistant, Frigate, Alexa, Beekeeper,
or any write/mutation endpoints.
"""

from .config import ToastConfig, missing_credentials
from .report import DailyBaselineReport

__all__ = [
    "ToastConfig",
    "DailyBaselineReport",
    "missing_credentials",
]

__version__ = "0.1.0"
