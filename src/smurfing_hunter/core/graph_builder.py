"""
Graph Builder Module
Handles loading transaction data and building the blockchain transaction graph
"""

import pandas as pd
import networkx as nx
from datetime import datetime
from typing import Dict, List, Tuple, Set
import numpy as np


class BlockchainGraph:
    """
    Represents a blockchain transaction network as a directed graph
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.transactions = []
        self.illicit_wallets = set()
        self.wallet_metadata = {}
        
    def load_transactions(self, csv_path: str) -> None:
        """
        Load transactions from CSV file
        
        Expected columns: Source_Wallet_ID, Dest_Wallet_ID, Timestamp, Amount, Token_Type
        """
        df = pd.read_csv(csv_path)
        
        # Validate required columns
        required_cols = ['Source_Wallet_ID', 'Dest_Wallet_ID', 'Timestamp', 'Amount', 'Token_Type']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"CSV must contain columns: {required_cols}")
        
        # Parse timestamps
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        
        self.transactions = df.to_dict('records')
        self._build_graph(df)
        
        print(f"Loaded {len(self.transactions)} transactions")
        print(f"Graph has {self.graph.number_of_nodes()} wallets and {self.graph.number_of_edges()} edges")
        
    def _build_graph(self, df: pd.DataFrame) -> None:
        """
        Build directed graph from transaction dataframe
        """
        for _, row in df.iterrows():
            source = row['Source_Wallet_ID']
            dest = row['Dest_Wallet_ID']
            amount = row['Amount']
            timestamp = row['Timestamp']
            token_type = row['Token_Type']
            
            # Add nodes
            if not self.graph.has_node(source):
                self.graph.add_node(source, wallet_id=source, total_sent=0, total_received=0, 
                                   first_seen=timestamp, last_seen=timestamp, 
                                   transaction_count=0)
            if not self.graph.has_node(dest):
                self.graph.add_node(dest, wallet_id=dest, total_sent=0, total_received=0,
                                   first_seen=timestamp, last_seen=timestamp,
                                   transaction_count=0)
            
            # Update node metadata
            self.graph.nodes[source]['total_sent'] += amount
            self.graph.nodes[dest]['total_received'] += amount
            self.graph.nodes[source]['last_seen'] = max(self.graph.nodes[source]['last_seen'], timestamp)
            self.graph.nodes[dest]['last_seen'] = max(self.graph.nodes[dest]['last_seen'], timestamp)
            self.graph.nodes[source]['transaction_count'] += 1
            self.graph.nodes[dest]['transaction_count'] += 1
            
            # Add or update edge
            if self.graph.has_edge(source, dest):
                # Aggregate multiple transactions between same wallets
                self.graph[source][dest]['amount'] += amount
                self.graph[source][dest]['transaction_count'] += 1
                self.graph[source][dest]['timestamps'].append(timestamp)
            else:
                self.graph.add_edge(source, dest, amount=amount, token_type=token_type,
                                   timestamp=timestamp, timestamps=[timestamp],
                                   transaction_count=1)
    
    def load_illicit_wallets(self, csv_path: str) -> None:
        """
        Load known illicit wallets from CSV
        
        Expected columns: Wallet_ID, Reason (optional)
        """
        df = pd.read_csv(csv_path)
        
        if 'Wallet_ID' not in df.columns:
            raise ValueError("CSV must contain 'Wallet_ID' column")
        
        self.illicit_wallets = set(df['Wallet_ID'].values)
        
        # Mark illicit wallets in graph
        for wallet in self.illicit_wallets:
            if self.graph.has_node(wallet):
                self.graph.nodes[wallet]['illicit'] = True
                if 'Reason' in df.columns:
                    reason = df[df['Wallet_ID'] == wallet]['Reason'].iloc[0]
                    self.graph.nodes[wallet]['illicit_reason'] = reason
        
        print(f"Loaded {len(self.illicit_wallets)} illicit wallets")
        
    def get_neighbors(self, wallet: str, direction: str = 'both') -> Set[str]:
        """
        Get neighbors of a wallet
        
        Args:
            wallet: Wallet ID
            direction: 'in' (predecessors), 'out' (successors), or 'both'
        """
        if direction == 'in':
            return set(self.graph.predecessors(wallet))
        elif direction == 'out':
            return set(self.graph.successors(wallet))
        else:
            return set(self.graph.predecessors(wallet)) | set(self.graph.successors(wallet))
    
    def get_path_amount_flow(self, path: List[str]) -> float:
        """
        Calculate total amount flowing through a path
        """
        total = 0
        for i in range(len(path) - 1):
            if self.graph.has_edge(path[i], path[i+1]):
                total += self.graph[path[i]][path[i+1]]['amount']
        return total
    
    def get_wallet_features(self, wallet: str) -> Dict:
        """
        Extract features for a wallet node
        """
        if not self.graph.has_node(wallet):
            return {}
        
        node_data = self.graph.nodes[wallet]
        
        features = {
            'in_degree': self.graph.in_degree(wallet),
            'out_degree': self.graph.out_degree(wallet),
            'total_received': node_data.get('total_received', 0),
            'total_sent': node_data.get('total_sent', 0),
            'transaction_count': node_data.get('transaction_count', 0),
            'is_illicit': wallet in self.illicit_wallets,
        }
        
        # Calculate balance
        features['balance'] = features['total_received'] - features['total_sent']
        
        # Fan-out ratio (how much splitting occurs)
        features['fanout_ratio'] = features['out_degree'] / max(features['in_degree'], 1)
        
        # Fan-in ratio (how much aggregation occurs)
        features['fanin_ratio'] = features['in_degree'] / max(features['out_degree'], 1)
        
        return features
    
    def get_subgraph_around_wallet(self, wallet: str, hops: int = 2) -> nx.DiGraph:
        """
        Extract subgraph around a wallet within specified number of hops
        """
        if not self.graph.has_node(wallet):
            return nx.DiGraph()
        
        # BFS to get nodes within hops
        nodes = {wallet}
        current_level = {wallet}
        
        for _ in range(hops):
            next_level = set()
            for node in current_level:
                next_level.update(self.graph.successors(node))
                next_level.update(self.graph.predecessors(node))
            nodes.update(next_level)
            current_level = next_level
        
        return self.graph.subgraph(nodes).copy()
    

    
    def get_transaction_timeline(self, path: List[str]) -> List[datetime]:
        """
        Get transaction timestamps along a path
        """
        timestamps = []
        for i in range(len(path) - 1):
            if self.graph.has_edge(path[i], path[i+1]):
                timestamps.append(self.graph[path[i]][path[i+1]]['timestamp'])
        return timestamps
