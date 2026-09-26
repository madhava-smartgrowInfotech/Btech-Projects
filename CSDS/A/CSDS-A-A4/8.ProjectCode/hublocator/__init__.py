"""HubLocator - Advanced Optimization in E-Commerce Logistics:
Combining Matheuristics With Random Forests for Hub Location Efficiency.

Predict-then-optimise pipeline adopted from the base paper:
    1. historical logistics data      -> hublocator.data
    2. Random Forest demand forecast  -> hublocator.forecast
    3. hub location model (MIP)       -> hublocator.model
    4. matheuristic solver            -> hublocator.matheuristic
    5. re-optimisation over time      -> hublocator.rolling
    6. comparison with baselines      -> hublocator.baselines / hublocator.evaluate
"""
__version__ = "1.0.0"
