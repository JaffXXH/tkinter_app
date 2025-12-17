import pandas as pd
import numpy as np
from typing import List, Tuple

class OptionsArbitrageCleaner:
    def __init__(self, spot_bid: float, spot_ask: float, r: float, T: float, q: float = 0.0):
        self.Sb, self.Sa = spot_bid, spot_ask
        self.r, self.T, self.q = r, T, q
        self.df_r = np.exp(-r * T)
        self.df_q = np.exp(-q * T)

    def identify_atm_strike(self, df: pd.DataFrame) -> float:
        """Identify the ATM strike (closest to spot mid)."""
        spot_mid = (self.Sb + self.Sa) / 2
        strikes = df['strike'].values
        atm_idx = np.argmin(np.abs(strikes - spot_mid))
        return strikes[atm_idx]

    def _check_vertical_no_arb(self, df: pd.DataFrame, price_type: str) -> List[int]:
        """Check monotonicity and convexity for 'call' or 'put'. Returns indices of violating rows."""
        violations = []
        df_sorted = df.sort_values('strike').reset_index(drop=True)
        n = len(df_sorted)

        # 1. Check Monotonicity
        for i in range(n-1):
            if price_type == 'call':
                # Call ask at lower strike must be >= Call bid at higher strike
                if df_sorted.loc[i, 'ask'] < df_sorted.loc[i+1, 'bid']:
                    violations.append(df_sorted.index[i+1])
            else:  # put
                # Put bid at lower strike must be <= Put ask at higher strike
                if df_sorted.loc[i, 'bid'] > df_sorted.loc[i+1, 'ask']:
                    violations.append(df_sorted.index[i+1])

        # 2. Check Convexity (for triplets)
        for i in range(1, n-1):
            K1, K2, K3 = df_sorted.loc[i-1, 'strike'], df_sorted.loc[i, 'strike'], df_sorted.loc[i+1, 'strike']
            if price_type == 'call':
                C1, C2, C3 = df_sorted.loc[i-1, 'ask'], df_sorted.loc[i, 'bid'], df_sorted.loc[i+1, 'ask']
                slope1 = (C2 - C1) / (K2 - K1)
                slope2 = (C3 - C2) / (K3 - K2)
                if slope1 > slope2 + 1e-10:
                    violations.append(df_sorted.index[i]) # Middle strike is problematic
            else:  # put
                P1, P2, P3 = df_sorted.loc[i-1, 'bid'], df_sorted.loc[i, 'ask'], df_sorted.loc[i+1, 'bid']
                slope1 = (P2 - P1) / (K2 - K1)
                slope2 = (P3 - P2) / (K3 - K2)
                if slope1 > slope2 + 1e-10:
                    violations.append(df_sorted.index[i])
        return list(set(violations))

    def _check_butterfly_no_arb(self, df: pd.DataFrame, price_type: str) -> List[int]:
        """Check butterfly no-arbitrage condition. Returns violating middle strike indices."""
        violations = []
        df_sorted = df.sort_values('strike').reset_index(drop=True)
        n = len(df_sorted)

        for i in range(1, n-1):
            K_prev, K, K_next = df_sorted.loc[i-1, 'strike'], df_sorted.loc[i, 'strike'], df_sorted.loc[i+1, 'strike']
            # Check for approximate equal spacing
            if abs((K - K_prev) - (K_next - K)) / K > 0.01:
                continue # Skip non-equally spaced for simplicity

            if price_type == 'call':
                # Cost of long butterfly (using bids for long legs, asks for short leg)
                cost = df_sorted.loc[i-1, 'bid'] - 2*df_sorted.loc[i, 'ask'] + df_sorted.loc[i+1, 'bid']
                # If cost > 0, you can pay to get a non-negative future payoff -> arbitrage
                if cost > 1e-10:
                    violations.append(df_sorted.index[i])
            else: # put
                cost = df_sorted.loc[i-1, 'bid'] - 2*df_sorted.loc[i, 'ask'] + df_sorted.loc[i+1, 'bid']
                if cost > 1e-10:
                    violations.append(df_sorted.index[i])
        return violations

    def _check_bounds(self, df: pd.DataFrame, price_type: str) -> List[int]:
        """Check if option prices are within rational bounds."""
        violations = []
        for idx, row in df.iterrows():
            K = row['strike']
            if price_type == 'call':
                lower_bound = max(self.Sb * self.df_q - K * self.df_r, 0)
                upper_bound = self.Sa
                if row['bid'] < lower_bound - 1e-10 or row['ask'] > upper_bound + 1e-10:
                    violations.append(idx)
            else: # put
                lower_bound = max(K * self.df_r - self.Sa * self.df_q, 0)
                upper_bound = K * self.df_r
                if row['bid'] < lower_bound - 1e-10 or row['ask'] > upper_bound + 1e-10:
                    violations.append(idx)
        return violations

    def clean_single_dataframe(self, df: pd.DataFrame, option_type: str, atm_strike: float, max_iter=20) -> pd.DataFrame:
        """Iteratively remove arbitrageable options from a single DataFrame."""
        df_clean = df.copy()
        atm_index = df_clean.index[df_clean['strike'] == atm_strike].tolist()[0]

        for iteration in range(max_iter):
            # Collect all potential violations
            v_vertical = self._check_vertical_no_arb(df_clean, option_type)
            v_butterfly = self._check_butterfly_no_arb(df_clean, option_type)
            v_bounds = self._check_bounds(df_clean, option_type)

            all_violations = set(v_vertical + v_butterfly + v_bounds)
            all_violations.discard(atm_index) # Never remove the ATM anchor

            if not all_violations:
                print(f"  Iteration {iteration+1}: Clean. No violations found.")
                break

            print(f"  Iteration {iteration+1}: Removing {len(all_violations)} violating options.")
            df_clean = df_clean.drop(index=list(all_violations)).reset_index(drop=True)
            # Re-identify ATM index in the new dataframe if it still exists
            if atm_strike in df_clean['strike'].values:
                atm_index = df_clean.index[df_clean['strike'] == atm_strike].tolist()[0]
            else:
                print("  Warning: ATM strike was removed. This shouldn't happen if data is sane.")
                break
        return df_clean

def clean_all_dataframes(list_of_dfs: List[pd.DataFrame],
                         option_types: List[str],
                         spot_bid: float,
                         spot_ask: float,
                         r: float,
                         T: float) -> Tuple[List[pd.DataFrame], dict]:
    """
    Main cleaning function.
    Returns: (cleaned_list_of_dfs, report_dictionary)
    """
    cleaner = OptionsArbitrageCleaner(spot_bid, spot_ask, r, T)
    cleaned_dfs = []
    report = {'removed_counts': [], 'arbitrage_types_found': []}

    for idx, (df, o_type) in enumerate(zip(list_of_dfs, option_types)):
        print(f"\n--- Processing DataFrame {idx} ({o_type.upper()}S) ---")
        print(f"  Initial number of options: {len(df)}")

        # 1. Identify ATM strike (assumed arbitrage-free)
        atm_strike = cleaner.identify_atm_strike(df)
        print(f"  Anchor ATM strike: {atm_strike}")

        # 2. Clean the dataframe iteratively
        df_cleaned = cleaner.clean_single_dataframe(df, o_type, atm_strike)

        # 3. Store results
        removed = len(df) - len(df_cleaned)
        cleaned_dfs.append(df_cleaned)
        report['removed_counts'].append(removed)
        print(f"  Final number of options: {len(df_cleaned)}")
        print(f"  Total removed: {removed}")

    # 4. (Optional) Cross-check Put-Call Parity across call and put dataframes
    # This step requires matching strikes between call and put DataFrames.
    # You would merge cleaned_dfs[call_idx] and cleaned_dfs[put_idx], then
    # check the parity condition using bid/ask spreads.
    # Violating strikes can be removed from both dataframes.

    print(f"\n=== Summary ===")
    total_initial = sum(len(df) for df in list_of_dfs)
    total_final = sum(len(df) for df in cleaned_dfs)
    print(f"Total options removed: {total_initial - total_final} out of {total_initial}")

    return cleaned_dfs, report

# Example Usage Structure
if __name__ == "__main__":
    # Assuming 'list_of_call_dfs' and 'list_of_put_dfs' are your lists of DataFrames
    # Each DataFrame has columns: ['strike', 'bid', 'ask', 'mid']
    # Combine them into one list and specify their types
    all_dfs = [calls_df_1, puts_df_1, calls_df_2, puts_df_2] # ... your list
    all_types = ['call', 'put', 'call', 'put'] # ... corresponding types

    spot_bid, spot_ask = 100.0, 100.1  # Example
    risk_free_rate = 0.03  # 3%
    time_to_maturity = 30/365  # 30 days

    cleaned_dfs, report = clean_all_dataframes(
        list_of_dfs=all_dfs,
        option_types=all_types,
        spot_bid=spot_bid,
        spot_ask=spot_ask,
        r=risk_free_rate,
        T=time_to_maturity
    )
    # 'cleaned_dfs' is your new arbitrage-free list of DataFrames
