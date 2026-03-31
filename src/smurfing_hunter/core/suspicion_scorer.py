"""
Suspicion Scoring Module
Calculates suspicion scores for wallets based on centrality, connections to illicit nodes,
and participation in detected patterns
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Tuple
from scipy import stats


class SuspicionScorer:
    """
    Calculates suspicion scores for wallets in the blockchain graph
    """
    
    def __init__(self, blockchain_graph, pattern_detector):
        self.graph = blockchain_graph.graph
        self.blockchain = blockchain_graph
        self.pattern_detector = pattern_detector
        self.wallet_scores = {}
        
    def calculate_all_scores(self) -> Dict[str, float]:
        """
        Calculate comprehensive suspicion scores for all wallets
        Combines multiple metrics: centrality, illicit connections, pattern involvement
        """
        print("Calculating suspicion scores...")
        
        # Calculate individual components
        centrality_scores = self._calculate_centrality_scores()
        illicit_proximity_scores = self._calculate_illicit_proximity_scores()
        pattern_involvement_scores = self._calculate_pattern_involvement_scores()
        structural_anomaly_scores = self._calculate_structural_anomaly_scores()
        
        # Combine scores with weights
        weights = {
            'centrality': 0.35,        # Alpha (Important)
            'illicit_proximity': 0.35, # Beta (Important)
            'pattern_involvement': 0.20,
            'structural_anomaly': 0.10
        }
        
        for wallet in self.graph.nodes():
            combined_score = (
                weights['centrality'] * centrality_scores.get(wallet, 0) +
                weights['illicit_proximity'] * illicit_proximity_scores.get(wallet, 0) +
                weights['pattern_involvement'] * pattern_involvement_scores.get(wallet, 0) +
                weights['structural_anomaly'] * structural_anomaly_scores.get(wallet, 0)
            )
            
            self.wallet_scores[wallet] = combined_score
        
        print(f"Calculated scores for {len(self.wallet_scores)} wallets")
        return self.wallet_scores
    
    def _calculate_centrality_scores(self) -> Dict[str, float]:
        """
        Calculate scores based on various centrality measures
        High centrality = more connections = potentially more suspicious
        """
        scores = {}
        
        # PageRank - measures importance in the network
        pagerank = nx.pagerank(self.graph, alpha=0.85)
        
        # Betweenness centrality - measures how often a node appears on shortest paths
        # (may indicate money laundering intermediary)
        try:
            betweenness = nx.betweenness_centrality(self.graph, k=min(100, len(self.graph.nodes())))
        except:
            betweenness = {node: 0 for node in self.graph.nodes()}
        
        # Closeness centrality - measures how close a node is to all others
        try:
            closeness = nx.closeness_centrality(self.graph)
        except:
            closeness = {node: 0 for node in self.graph.nodes()}
        
        # Normalize and combine
        pr_values = list(pagerank.values())
        bt_values = list(betweenness.values())
        cl_values = list(closeness.values())
        
        pr_norm = self._normalize_scores(pr_values)
        bt_norm = self._normalize_scores(bt_values)
        cl_norm = self._normalize_scores(cl_values)
        
        for i, wallet in enumerate(pagerank.keys()):
            # Combine centrality measures
            scores[wallet] = (0.4 * pr_norm[i] + 0.4 * bt_norm[i] + 0.2 * cl_norm[i]) * 100
        
        return scores
    
    def _calculate_illicit_proximity_scores(self) -> Dict[str, float]:
        """
        Calculate scores based on proximity to known illicit wallets
        Closer to illicit nodes = higher score
        """
        scores = {}
        
        for wallet in self.graph.nodes():
            # Direct check: is this wallet illicit?
            if wallet in self.blockchain.illicit_wallets:
                scores[wallet] = 100.0
                continue
            
            # Calculate shortest path to any illicit wallet
            path, distance = self.pattern_detector.find_shortest_path_to_illicit(wallet)
            
            if distance == float('inf'):
                # No connection to illicit wallets
                scores[wallet] = 0.0
            else:
                # Score decreases exponentially with distance
                # Distance 1 = 90, Distance 2 = 70, Distance 3 = 50, etc.
                scores[wallet] = 100 * np.exp(-0.3 * (distance - 1))
            
            # Bonus: count direct connections to illicit wallets
            illicit_neighbors = sum(
                1 for neighbor in self.blockchain.get_neighbors(wallet)
                if neighbor in self.blockchain.illicit_wallets
            )
            
            if illicit_neighbors > 0:
                scores[wallet] = min(scores[wallet] + illicit_neighbors * 10, 100.0)
        
        return scores
    
    def _calculate_pattern_involvement_scores(self) -> Dict[str, float]:
        """
        Calculate scores based on involvement in detected laundering patterns
        """
        scores = {wallet: 0.0 for wallet in self.graph.nodes()}
        
        # Check each detected pattern
        for pattern in self.pattern_detector.detected_patterns:
            # All wallets involved in the pattern get score based on pattern suspicion
            involved_wallets = (pattern.source_wallets | pattern.intermediate_wallets | 
                              pattern.destination_wallets)
            
            for wallet in involved_wallets:
                if wallet in scores:
                    # Add pattern's suspicion score (weighted by role)
                    if wallet in pattern.source_wallets or wallet in pattern.destination_wallets:
                        # Sources and destinations get higher score
                        scores[wallet] += pattern.suspicion_score * 1.0
                    else:
                        # Intermediates get medium score
                        scores[wallet] += pattern.suspicion_score * 0.7
        
        # Normalize to 0-100 range
        if scores:
            max_score = max(scores.values())
            if max_score > 0:
                scores = {w: min((s / max_score) * 100, 100) for w, s in scores.items()}
        
        return scores
    
    def _calculate_structural_anomaly_scores(self) -> Dict[str, float]:
        """
        Calculate scores based on structural anomalies
        (unusual fan-out/fan-in ratios, rapid transactions, etc.)
        """
        scores = {}
        
        # Get all wallet features
        all_features = []
        wallet_list = []
        
        for wallet in self.graph.nodes():
            features = self.blockchain.get_wallet_features(wallet)
            if features:
                all_features.append([
                    features['in_degree'],
                    features['out_degree'],
                    features['fanout_ratio'],
                    features['fanin_ratio'],
                    features['transaction_count']
                ])
                wallet_list.append(wallet)
        
        if not all_features:
            return {wallet: 0.0 for wallet in self.graph.nodes()}
        
        all_features = np.array(all_features)
        
        # Calculate z-scores for each feature (how many std devs from mean)
        anomaly_scores = []
        for i in range(all_features.shape[1]):
            feature_values = all_features[:, i]
            if np.std(feature_values) > 0:
                z_scores = np.abs(stats.zscore(feature_values, nan_policy='omit'))
            else:
                z_scores = np.zeros_like(feature_values)
            anomaly_scores.append(z_scores)
        
        anomaly_scores = np.array(anomaly_scores)
        
        # Combined anomaly score (max z-score across features)
        combined_anomalies = np.max(anomaly_scores, axis=0)
        
        # Normalize to 0-100
        if np.max(combined_anomalies) > 0:
            normalized = (combined_anomalies / np.max(combined_anomalies)) * 100
        else:
            normalized = combined_anomalies
        
        scores = {wallet: float(score) for wallet, score in zip(wallet_list, normalized)}
        
        # Fill in any missing wallets
        for wallet in self.graph.nodes():
            if wallet not in scores:
                scores[wallet] = 0.0
        
        return scores
    
    def get_top_suspicious_wallets(self, n: int = 10) -> List[Tuple[str, float]]:
        """
        Get the top N most suspicious wallets
        """
        if not self.wallet_scores:
            self.calculate_all_scores()
        
        sorted_wallets = sorted(self.wallet_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_wallets[:n]
    
    def get_wallet_risk_assessment(self, wallet: str) -> Dict:
        """
        Get detailed risk assessment for a specific wallet
        """
        if wallet not in self.graph.nodes():
            return {'error': 'Wallet not found'}
        
        if not self.wallet_scores:
            self.calculate_all_scores()
        
        # Get component scores
        centrality = self._calculate_centrality_scores().get(wallet, 0)
        illicit_proximity = self._calculate_illicit_proximity_scores().get(wallet, 0)
        pattern_involvement = self._calculate_pattern_involvement_scores().get(wallet, 0)
        structural_anomaly = self._calculate_structural_anomaly_scores().get(wallet, 0)
        
        # Get wallet features
        features = self.blockchain.get_wallet_features(wallet)
        
        # Find patterns involving this wallet
        involved_patterns = [
            p for p in self.pattern_detector.detected_patterns
            if wallet in (p.source_wallets | p.intermediate_wallets | p.destination_wallets)
        ]
        
        # Distance to illicit
        path, distance = self.pattern_detector.find_shortest_path_to_illicit(wallet)
        
        assessment = {
            'wallet_id': wallet,
            'overall_suspicion_score': self.wallet_scores.get(wallet, 0),
            'risk_level': self._get_risk_level(self.wallet_scores.get(wallet, 0)),
            'score_components': {
                'centrality_score': centrality,
                'illicit_proximity_score': illicit_proximity,
                'pattern_involvement_score': pattern_involvement,
                'structural_anomaly_score': structural_anomaly
            },
            'wallet_features': features,
            'illicit_connection': {
                'is_illicit': wallet in self.blockchain.illicit_wallets,
                'distance_to_illicit': distance if distance != float('inf') else None,
                'path_to_illicit': path if path else None
            },
            'patterns_involved': len(involved_patterns),
            'pattern_types': [p.pattern_type for p in involved_patterns]
        }
        
        return assessment
    
    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """
        Normalize scores to 0-1 range
        """
        if not scores:
            return []
        
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score - min_score == 0:
            return [0.5] * len(scores)
        
        return [(s - min_score) / (max_score - min_score) for s in scores]
    
    def _get_risk_level(self, score: float) -> str:
        """
        Convert numerical score to risk level
        """
        if score >= 80:
            return "CRITICAL"
        elif score >= 60:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        elif score >= 20:
            return "LOW"
        else:
            return "MINIMAL"
    
    def generate_risk_report(self, output_file: str = "risk_report.txt"):
        """
        Generate a comprehensive risk report
        """
        if not self.wallet_scores:
            self.calculate_all_scores()
        
        top_wallets = self.get_top_suspicious_wallets(20)
        
        with open(output_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("BLOCKCHAIN MONEY LAUNDERING RISK ASSESSMENT REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Total wallets analyzed: {len(self.wallet_scores)}\n")
            f.write(f"Known illicit wallets: {len(self.blockchain.illicit_wallets)}\n")
            f.write(f"Detected patterns: {len(self.pattern_detector.detected_patterns)}\n\n")
            
            # Risk distribution
            risk_levels = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'MINIMAL': 0}
            for score in self.wallet_scores.values():
                risk_levels[self._get_risk_level(score)] += 1
            
            f.write("Risk Level Distribution:\n")
            for level, count in risk_levels.items():
                f.write(f"  {level}: {count} wallets\n")
            f.write("\n")
            
            f.write("=" * 80 + "\n")
            f.write("TOP 20 MOST SUSPICIOUS WALLETS\n")
            f.write("=" * 80 + "\n\n")
            
            for i, (wallet, score) in enumerate(top_wallets, 1):
                assessment = self.get_wallet_risk_assessment(wallet)
                
                f.write(f"{i}. Wallet: {wallet}\n")
                f.write(f"   Overall Suspicion Score: {score:.2f}/100\n")
                f.write(f"   Risk Level: {assessment['risk_level']}\n")
                f.write(f"   Is Known Illicit: {assessment['illicit_connection']['is_illicit']}\n")
                
                if assessment['illicit_connection']['distance_to_illicit']:
                    f.write(f"   Distance to Illicit Wallet: {assessment['illicit_connection']['distance_to_illicit']} hops\n")
                
                f.write(f"   Patterns Involved: {assessment['patterns_involved']}\n")
                
                components = assessment['score_components']
                f.write(f"   Score Components:\n")
                f.write(f"     - Centrality: {components['centrality_score']:.2f}\n")
                f.write(f"     - Illicit Proximity: {components['illicit_proximity_score']:.2f}\n")
                f.write(f"     - Pattern Involvement: {components['pattern_involvement_score']:.2f}\n")
                f.write(f"     - Structural Anomaly: {components['structural_anomaly_score']:.2f}\n")
                f.write("\n")
        
        print(f"Risk report saved to {output_file}")
