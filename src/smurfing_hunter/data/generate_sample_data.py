"""
Sample Data Generator
Generates realistic blockchain transaction data with laundering patterns
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import string


class DataGenerator:
    """
    Generates synthetic blockchain transaction data with embedded laundering patterns
    """
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        np.random.seed(seed)
        self.wallet_counter = 0
        
    def generate_wallet_id(self) -> str:
        """Generate a realistic-looking wallet ID"""
        self.wallet_counter += 1
        prefix = '0x' + ''.join(random.choices(string.hexdigits.lower(), k=40))
        return prefix
    
    def generate_normal_transactions(self, n_wallets: int = 100, 
                                    n_transactions: int = 500) -> pd.DataFrame:
        """
        Generate normal (non-suspicious) transactions
        """
        wallets = [self.generate_wallet_id() for _ in range(n_wallets)]
        
        transactions = []
        start_time = datetime.now() - timedelta(days=30)
        
        for _ in range(n_transactions):
            source = random.choice(wallets)
            dest = random.choice([w for w in wallets if w != source])
            
            # Normal transaction amounts follow log-normal distribution
            amount = np.random.lognormal(mean=3, sigma=1.5)
            
            # Random timestamp within last 30 days
            time_offset = timedelta(seconds=random.randint(0, 30 * 24 * 3600))
            timestamp = start_time + time_offset
            
            token_type = random.choice(['ETH', 'BTC', 'USDT', 'BNB'])
            
            transactions.append({
                'Source_Wallet_ID': source,
                'Dest_Wallet_ID': dest,
                'Timestamp': timestamp,
                'Amount': round(amount, 6),
                'Token_Type': token_type
            })
        
        return pd.DataFrame(transactions), wallets
    
    def generate_fanout_fanin_pattern(self, n_intermediates: int = 10) -> pd.DataFrame:
        """
        Generate a fan-out/fan-in laundering pattern
        Source -> Multiple Intermediates -> Destination
        """
        source = self.generate_wallet_id()
        intermediates = [self.generate_wallet_id() for _ in range(n_intermediates)]
        destination = self.generate_wallet_id()
        
        transactions = []
        start_time = datetime.now() - timedelta(days=15)
        
        # Large initial amount
        total_amount = random.uniform(10000, 50000)
        
        # Phase 1: Fan-out (Source -> Intermediates)
        for i, intermediate in enumerate(intermediates):
            # Split amount with some variation
            amount = total_amount / n_intermediates * random.uniform(0.8, 1.2)
            timestamp = start_time + timedelta(minutes=i * 5)
            
            transactions.append({
                'Source_Wallet_ID': source,
                'Dest_Wallet_ID': intermediate,
                'Timestamp': timestamp,
                'Amount': round(amount, 6),
                'Token_Type': 'ETH'
            })
        
        # Phase 2: Delay and intermediate hops (optional)
        delay = timedelta(hours=random.randint(1, 24))
        
        # Phase 3: Fan-in (Intermediates -> Destination)
        for i, intermediate in enumerate(intermediates):
            # Slightly reduce amount (to simulate fees)
            original_amount = total_amount / n_intermediates * random.uniform(0.8, 1.2)
            amount = original_amount * random.uniform(0.95, 0.99)
            timestamp = start_time + delay + timedelta(minutes=i * 5)
            
            transactions.append({
                'Source_Wallet_ID': intermediate,
                'Dest_Wallet_ID': destination,
                'Timestamp': timestamp,
                'Amount': round(amount, 6),
                'Token_Type': 'ETH'
            })
        
        return pd.DataFrame(transactions), [source], intermediates, [destination]
    
    def generate_layered_pattern(self, n_layers: int = 3, 
                                 wallets_per_layer: int = 5) -> pd.DataFrame:
        """
        Generate a layered laundering pattern with multiple levels
        """
        layers = []
        for _ in range(n_layers + 1):
            layers.append([self.generate_wallet_id() for _ in range(wallets_per_layer)])
        
        transactions = []
        start_time = datetime.now() - timedelta(days=20)
        
        initial_amount = random.uniform(20000, 100000)
        
        # Go through each layer
        for layer_idx in range(n_layers):
            current_layer = layers[layer_idx]
            next_layer = layers[layer_idx + 1]
            
            for i, source_wallet in enumerate(current_layer):
                # Each wallet sends to multiple wallets in next layer
                for j, dest_wallet in enumerate(next_layer):
                    if random.random() < 0.6:  # 60% connection probability
                        # Amount diminishes slightly at each layer
                        amount = (initial_amount / (wallets_per_layer ** (layer_idx + 1))) * random.uniform(0.8, 1.2)
                        
                        # Add time delay
                        time_offset = timedelta(hours=layer_idx * 12 + random.randint(0, 360))
                        timestamp = start_time + time_offset
                        
                        transactions.append({
                            'Source_Wallet_ID': source_wallet,
                            'Dest_Wallet_ID': dest_wallet,
                            'Timestamp': timestamp,
                            'Amount': round(amount, 6),
                            'Token_Type': 'BTC'
                        })
        
        return pd.DataFrame(transactions), layers[0], sum(layers[1:-1], []), layers[-1]
    
    def generate_cyclic_pattern(self, cycle_length: int = 5) -> pd.DataFrame:
        """
        Generate a cyclic laundering pattern where money goes in a loop
        """
        wallets = [self.generate_wallet_id() for _ in range(cycle_length)]
        
        transactions = []
        start_time = datetime.now() - timedelta(days=10)
        
        amount = random.uniform(5000, 20000)
        
        for i in range(cycle_length):
            source = wallets[i]
            dest = wallets[(i + 1) % cycle_length]
            
            # Slightly reduce amount at each hop (peeling)
            current_amount = amount * (0.98 ** i)
            
            timestamp = start_time + timedelta(hours=i * 6)
            
            transactions.append({
                'Source_Wallet_ID': source,
                'Dest_Wallet_ID': dest,
                'Timestamp': timestamp,
                'Amount': round(current_amount, 6),
                'Token_Type': 'USDT'
            })
        
        return pd.DataFrame(transactions), wallets
    
    def generate_peeling_chain(self, chain_length: int = 10) -> pd.DataFrame:
        """
        Generate a peeling chain where small amounts are peeled off at each hop
        """
        wallets = [self.generate_wallet_id() for _ in range(chain_length + 1)]
        
        transactions = []
        start_time = datetime.now() - timedelta(days=5)
        
        initial_amount = random.uniform(10000, 30000)
        remaining = initial_amount
        
        for i in range(chain_length):
            source = wallets[i]
            dest = wallets[i + 1]
            
            # Peel off 0.5-2% to another wallet (simulating gas/small peel)
            peel_amount = remaining * random.uniform(0.005, 0.020)
            peel_dest = self.generate_wallet_id()
            
            # Main transfer (85-95% of remaining)
            main_amount = remaining - peel_amount
            
            timestamp = start_time + timedelta(minutes=i * 30)
            
            # Peeling transaction
            transactions.append({
                'Source_Wallet_ID': source,
                'Dest_Wallet_ID': peel_dest,
                'Timestamp': timestamp,
                'Amount': round(peel_amount, 6),
                'Token_Type': 'ETH'
            })
            
            # Main chain transaction
            transactions.append({
                'Source_Wallet_ID': source,
                'Dest_Wallet_ID': dest,
                'Timestamp': timestamp + timedelta(seconds=30),
                'Amount': round(main_amount, 6),
                'Token_Type': 'ETH'
            })
            
            remaining = main_amount
        
        return pd.DataFrame(transactions), wallets
    
    def generate_complete_dataset(self, output_dir: str = "."):
        """
        Generate a complete dataset with normal and suspicious transactions
        """
        print("Generating synthetic blockchain transaction dataset...")
        
        all_transactions = []
        illicit_wallets = []
        
        # Generate normal transactions
        print("  - Generating normal transactions...")
        normal_df, normal_wallets = self.generate_normal_transactions(
            n_wallets=150, n_transactions=800
        )
        all_transactions.append(normal_df)
        
        # Generate laundering patterns
        print("  - Generating fan-out/fan-in patterns...")
        for _ in range(5):
            pattern_df, sources, intermediates, dests = self.generate_fanout_fanin_pattern(
                n_intermediates=random.randint(8, 15)
            )
            all_transactions.append(pattern_df)
            illicit_wallets.extend(sources)
        
        print("  - Generating layered patterns...")
        for _ in range(3):
            pattern_df, sources, intermediates, dests = self.generate_layered_pattern(
                n_layers=random.randint(2, 4),
                wallets_per_layer=random.randint(4, 7)
            )
            all_transactions.append(pattern_df)
            illicit_wallets.extend(sources)
        
        print("  - Generating cyclic patterns...")
        for _ in range(4):
            pattern_df, wallets = self.generate_cyclic_pattern(
                cycle_length=random.randint(4, 8)
            )
            all_transactions.append(pattern_df)
            illicit_wallets.append(wallets[0])
        
        print("  - Generating peeling chains...")
        for _ in range(3):
            pattern_df, wallets = self.generate_peeling_chain(
                chain_length=random.randint(8, 12)
            )
            all_transactions.append(pattern_df)
            illicit_wallets.append(wallets[0])
        
        # Combine all transactions
        final_df = pd.concat(all_transactions, ignore_index=True)
        
        # Sort by timestamp
        final_df = final_df.sort_values('Timestamp').reset_index(drop=True)
        
        # Save transactions
        transactions_file = f"{output_dir}/transactions.csv"
        final_df.to_csv(transactions_file, index=False)
        print(f"\nTransactions saved to {transactions_file}")
        print(f"  Total transactions: {len(final_df)}")
        print(f"  Total wallets: {len(set(final_df['Source_Wallet_ID']) | set(final_df['Dest_Wallet_ID']))}")
        
        # Save illicit wallets
        reasons = ['Known hacker', 'Ransomware', 'Dark web marketplace', 'Money laundering']
        illicit_reasons = [reasons[i % len(reasons)] for i in range(len(illicit_wallets))]
        illicit_df = pd.DataFrame({
            'Wallet_ID': illicit_wallets,
            'Reason': illicit_reasons
        })
        
        illicit_file = f"{output_dir}/illicit_wallets.csv"
        illicit_df.to_csv(illicit_file, index=False)
        print(f"Illicit wallets saved to {illicit_file}")
        print(f"  Total illicit wallets: {len(illicit_wallets)}")
        
        return transactions_file, illicit_file


if __name__ == "__main__":
    generator = DataGenerator(seed=42)
    generator.generate_complete_dataset()
