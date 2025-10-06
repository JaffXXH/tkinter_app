# arbitrage checks:
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional

class SkewMatrixValidator:
    def __init__(self, tolerance: float = 1e-10):
        self.tolerance = tolerance
    
    def check_arbitrage_bounds(self, atm_vol: float, rr_25: float, str_25: float, 
                             rr_10: float, str_10: float) -> Dict[str, bool]:
        """
        Check no-arbitrage conditions for volatility spreads
        """
        checks = {
            'butterfly_positive_25': str_25 > 0,
            'butterfly_positive_10': str_10 > 0,
            'rr_symmetric_bounds_25': abs(rr_25) < 4 * str_25,
            'rr_symmetric_bounds_10': abs(rr_10) < 4 * str_10,
            'str_decreasing_with_delta': str_10 >= str_25,
        }
        return checks
    
    def check_volatility_monotonicity(self, vol_data: Dict[str, float]) -> Dict[str, bool]:
        """
        Check that implied volatilities are monotonically decreasing from ATM to wings
        """
        checks = {}
        
        # For 25 delta: vol_25C > vol_ATM > vol_25P (for normal skew)
        if all(k in vol_data for k in ['vol_25C', 'vol_ATM', 'vol_25P']):
            checks['monotonic_25_delta'] = (
                vol_data['vol_25C'] >= vol_data['vol_ATM'] >= vol_data['vol_25P']
            )
        
        # For 10 delta: vol_10C > vol_25C and vol_10P < vol_25P
        if all(k in vol_data for k in ['vol_10C', 'vol_25C', 'vol_25P', 'vol_10P']):
            checks['monotonic_10_delta'] = (
                vol_data['vol_10C'] >= vol_data['vol_25C'] and
                vol_data['vol_10P'] <= vol_data['vol_25P']
            )
        
        return checks
    
    def check_tenor_consistency(self, tenor_data: Dict[str, Dict]) -> Dict[str, bool]:
        """
        Check consistency across tenors
        """
        checks = {}
        tenors = list(tenor_data.keys())
        
        if len(tenors) < 2:
            return {'sufficient_tenors': False}
        
        # Check term structure monotonicity (usually vol increases with tenor)
        atm_vols = [tenor_data[t]['ATM'] for t in tenors]
        checks['atm_term_structure_monotonic'] = all(
            atm_vols[i] <= atm_vols[i+1] for i in range(len(atm_vols)-1)
        )
        
        # Check RR and STR consistency across tenors
        rr_25_values = [tenor_data[t]['RR_25'] for t in tenors]
        str_25_values = [tenor_data[t]['STR_25'] for t in tenors]
        
        # RR should not change sign arbitrarily across tenors
        rr_sign_changes = sum(
            1 for i in range(len(rr_25_values)-1) 
            if rr_25_values[i] * rr_25_values[i+1] < 0
        )
        checks['rr_sign_consistency'] = rr_sign_changes == 0
        
        return checks
    
    def check_smile_convexity(self, delta_points: List[float], 
                            volatilities: List[float]) -> bool:
        """
        Check that volatility smile is convex (second derivative positive)
        """
        if len(volatilities) < 3:
            return True
            
        # Calculate second differences
        second_diffs = []
        for i in range(1, len(volatilities)-1):
            second_diff = (volatilities[i+1] - 2*volatilities[i] + volatilities[i-1])
            second_diffs.append(second_diff)
        
        # Smile should be convex (positive second differences)
        return all(diff >= -self.tolerance for diff in second_diffs)
    
    def check_volatility_ranges(self, vol_data: Dict[str, float], 
                              min_vol: float = 0.001, max_vol: float = 5.0) -> Dict[str, bool]:
        """
        Check that volatilities are within reasonable bounds
        """
        checks = {}
        for key, vol in vol_data.items():
            if 'vol' in key.lower():
                checks[f'{key}_in_range'] = min_vol <= vol <= max_vol
        return checks
    
    def check_delta_consistency(self, rr_25: float, str_25: float, 
                              rr_10: float, str_10: float) -> Dict[str, bool]:
        """
        Check consistency between 10D and 25D parameters
        """
        checks = {
            'rr_magnitude_consistency': abs(rr_10) >= abs(rr_25),
            'str_magnitude_consistency': str_10 >= str_25,
            'rr_ratio_reasonable': abs(rr_10 / rr_25) < 3 if rr_25 != 0 else True,
            'str_ratio_reasonable': str_10 / str_25 < 3 if str_25 != 0 else True
        }
        return checks

    def check_butterfly_arbitrage(self, delta_points: List[float], 
                                volatilities: List[float]) -> bool:
        """
        Check for butterfly arbitrage using density constraints
        """
        if len(volatilities) < 3:
            return True
            
        # Simplified check: ensure no negative density
        # In practice, you'd implement more sophisticated checks
        for i in range(1, len(volatilities)-1):
            left_slope = (volatilities[i] - volatilities[i-1]) / (delta_points[i] - delta_points[i-1])
            right_slope = (volatilities[i+1] - volatilities[i]) / (delta_points[i+1] - delta_points[i])
            
            # Crude convexity check
            if right_slope < left_slope - 0.01:  # Allow small tolerance
                return False
                
        return True
