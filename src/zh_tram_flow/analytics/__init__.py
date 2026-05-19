"""
zh_tram_flow.analytics — analysis functions for all 6 analysis notebooks.

Usage:
    import zh_tram_flow.analytics as an
    an.plot_hour_of_day(lf)        # all functions accessible at package level
    an.temporal.plot_hour_of_day   # or via submodule
"""

from zh_tram_flow.analytics import target, network, temporal, spatial, meteo, events

from zh_tram_flow.analytics.target import *
from zh_tram_flow.analytics.network import *
from zh_tram_flow.analytics.temporal import *
from zh_tram_flow.analytics.spatial import *
from zh_tram_flow.analytics.meteo import *
from zh_tram_flow.analytics.events import *
