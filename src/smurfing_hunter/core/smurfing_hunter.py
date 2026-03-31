"""
Smurfing Hunter - Main Analysis Pipeline
Detects money laundering patterns in blockchain transaction networks
"""

import argparse
import os
from datetime import datetime

from .graph_builder import BlockchainGraph
from .pattern_detector import PatternDetector
from .suspicion_scorer import SuspicionScorer
from ..utils.visualizer import GraphVisualizer
from ..data.generate_sample_data import DataGenerator


class SmurfingHunter:
    """
    Main class for detecting money laundering in blockchain transactions
    """
    
    def __init__(self, transactions_file: str, illicit_wallets_file: str):
        print("=" * 80)
        print("SMURFING HUNTER - Money Laundering Detection System")
        print("=" * 80)
        print()
        
        # Initialize components
        print("Initializing blockchain graph...")
        self.blockchain = BlockchainGraph()
        self.blockchain.load_transactions(transactions_file)
        self.blockchain.load_illicit_wallets(illicit_wallets_file)
        print()
        
        print("Initializing pattern detector...")
        self.pattern_detector = PatternDetector(self.blockchain)
        print()
        
        self.suspicion_scorer = None
        self.visualizer = None
        
    def run_analysis(self, output_dir: str = "output"):
        """
        Run complete money laundering analysis
        """
        os.makedirs(output_dir, exist_ok=True)
        
        print("=" * 80)
        print("PHASE 1: PATTERN DETECTION")
        print("=" * 80)
        print()
        
        # Detect patterns
        patterns = self.pattern_detector.detect_all_patterns_from_illicit()
        
        print()
        print("Pattern Detection Summary:")
        print("-" * 40)
        for pattern_type, pattern_list in patterns.items():
            print(f"  {pattern_type}: {len(pattern_list)} patterns detected")
        print()
        
        # Get pattern statistics
        stats = self.pattern_detector.get_pattern_statistics()
        if stats:
            print("Pattern Statistics:")
            print(f"  Total patterns: {stats['total_patterns']}")
            print(f"  Average suspicion score: {stats['avg_suspicion_score']:.2f}")
            print(f"  Maximum suspicion score: {stats['max_suspicion_score']:.2f}")
            print(f"  Total amount flagged: ${stats['total_amount_flagged']:,.2f}")
        print()
        
        print("=" * 80)
        print("PHASE 2: SUSPICION SCORING")
        print("=" * 80)
        print()
        
        # Calculate suspicion scores
        self.suspicion_scorer = SuspicionScorer(self.blockchain, self.pattern_detector)
        scores = self.suspicion_scorer.calculate_all_scores()
        print()
        
        # Get top suspicious wallets
        print("Top 10 Most Suspicious Wallets:")
        print("-" * 40)
        top_wallets = self.suspicion_scorer.get_top_suspicious_wallets(10)
        
        for i, (wallet, score) in enumerate(top_wallets, 1):
            risk_level = self.suspicion_scorer._get_risk_level(score)
            is_illicit = wallet in self.blockchain.illicit_wallets
            print(f"{i:2d}. {wallet[:16]}... | Score: {score:6.2f} | "
                  f"Risk: {risk_level:8s} | Known Illicit: {is_illicit}")
        print()
        
        # Generate risk report
        report_file = os.path.join(output_dir, "risk_report.txt")
        self.suspicion_scorer.generate_risk_report(report_file)
        print()
        
        print("=" * 80)
        print("PHASE 3: DETAILED WALLET ANALYSIS")
        print("=" * 80)
        print()
        
        # Analyze top 3 wallets in detail
        print("Detailed Risk Assessments:")
        print("-" * 40)
        
        for i, (wallet, score) in enumerate(top_wallets[:3], 1):
            assessment = self.suspicion_scorer.get_wallet_risk_assessment(wallet)
            
            print(f"\n{i}. Wallet: {wallet}")
            print(f"   Overall Score: {assessment['overall_suspicion_score']:.2f}/100")
            print(f"   Risk Level: {assessment['risk_level']}")
            print()
            print("   Score Components:")
            components = assessment['score_components']
            print(f"     - Centrality Score:         {components['centrality_score']:.2f}")
            print(f"     - Illicit Proximity Score:  {components['illicit_proximity_score']:.2f}")
            print(f"     - Pattern Involvement Score: {components['pattern_involvement_score']:.2f}")
            print(f"     - Structural Anomaly Score: {components['structural_anomaly_score']:.2f}")
            print()
            print("   Wallet Features:")
            features = assessment['wallet_features']
            print(f"     - In-degree:  {features.get('in_degree', 0)}")
            print(f"     - Out-degree: {features.get('out_degree', 0)}")
            print(f"     - Total received: ${features.get('total_received', 0):,.2f}")
            print(f"     - Total sent:     ${features.get('total_sent', 0):,.2f}")
            print(f"     - Balance:        ${features.get('balance', 0):,.2f}")
            print()
            print("   Illicit Connection:")
            illicit_conn = assessment['illicit_connection']
            print(f"     - Is known illicit: {illicit_conn['is_illicit']}")
            if illicit_conn['distance_to_illicit']:
                print(f"     - Distance to illicit wallet: {illicit_conn['distance_to_illicit']} hops")
            print()
            print(f"   Patterns Involved: {assessment['patterns_involved']}")
            if assessment['pattern_types']:
                print(f"   Pattern Types: {', '.join(set(assessment['pattern_types']))}")
            print()
        
        print("=" * 80)
        print("PHASE 4: VISUALIZATION")
        print("=" * 80)
        print()
        
        # Create visualizations
        self.visualizer = GraphVisualizer(self.blockchain, self.pattern_detector, 
                                         self.suspicion_scorer)
        
        viz_dir = os.path.join(output_dir, "visualizations")
        self.visualizer.create_dashboard(viz_dir)
        print()
        
        print("=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        print()
        print(f"All results saved to: {output_dir}/")
        print()
        print("Summary:")
        print(f"  - Total wallets analyzed: {len(scores)}")
        print(f"  - Known illicit wallets: {len(self.blockchain.illicit_wallets)}")
        print(f"  - Patterns detected: {sum(len(p) for p in patterns.values())}")
        print(f"  - High-risk wallets (score >= 60): {sum(1 for s in scores.values() if s >= 60)}")
        print(f"  - Critical-risk wallets (score >= 80): {sum(1 for s in scores.values() if s >= 80)}")
        print()
        print("Output Files:")
        print(f"  - Risk Report: {report_file}")
        print(f"  - Interactive Graph: {viz_dir}/full_graph.html")
        print(f"  - Visualizations: {viz_dir}/")
        print()
        
    def investigate_wallet(self, wallet_id: str):
        """
        Perform detailed investigation of a specific wallet
        """
        if not self.suspicion_scorer:
            self.suspicion_scorer = SuspicionScorer(self.blockchain, self.pattern_detector)
            self.suspicion_scorer.calculate_all_scores()
        
        if wallet_id not in self.blockchain.graph.nodes():
            print(f"Error: Wallet {wallet_id} not found in the graph")
            return
        
        print("=" * 80)
        print(f"WALLET INVESTIGATION: {wallet_id}")
        print("=" * 80)
        print()
        
        assessment = self.suspicion_scorer.get_wallet_risk_assessment(wallet_id)
        
        print(f"Overall Suspicion Score: {assessment['overall_suspicion_score']:.2f}/100")
        print(f"Risk Level: {assessment['risk_level']}")
        print()
        
        # More detailed analysis...
        print("Detailed findings have been generated.")
        
        # Create visualization
        if not self.visualizer:
            self.visualizer = GraphVisualizer(self.blockchain, self.pattern_detector, 
                                            self.suspicion_scorer)
        
        output_file = f"wallet_investigation_{wallet_id[:8]}.png"
        self.visualizer.visualize_illicit_subgraph(wallet_id, hops=3, output_file=output_file)
        print(f"\nVisualization saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Smurfing Hunter - Detect money laundering patterns in blockchain transactions"
    )
    parser.add_argument(
        '--transactions', 
        type=str, 
        default='data/transactions.csv',
        help='Path to transactions CSV file'
    )
    parser.add_argument(
        '--illicit',
        type=str,
        default='data/illicit_wallets.csv',
        help='Path to illicit wallets CSV file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='output',
        help='Output directory for results'
    )
    parser.add_argument(
        '--generate-data',
        action='store_true',
        help='Generate sample data before analysis'
    )
    parser.add_argument(
        '--investigate',
        type=str,
        help='Investigate a specific wallet ID'
    )
    
    args = parser.parse_args()
    
    # Generate sample data if requested
    if args.generate_data:
        print("Generating sample data...")
        generator = DataGenerator(seed=42)
        os.makedirs('data', exist_ok=True)
        transactions_file, illicit_file = generator.generate_complete_dataset(output_dir='data')
        print()
        args.transactions = transactions_file
        args.illicit = illicit_file
    
    # Check if input files exist
    if not os.path.exists(args.transactions):
        print(f"Error: Transactions file '{args.transactions}' not found!")
        print("\nTip: Use --generate-data to create sample data")
        return
    
    if not os.path.exists(args.illicit):
        print(f"Error: Illicit wallets file '{args.illicit}' not found!")
        print("\nTip: Use --generate-data to create sample data")
        return
    
    # Initialize hunter
    hunter = SmurfingHunter(args.transactions, args.illicit)
    
    # Run analysis
    if args.investigate:
        hunter.investigate_wallet(args.investigate)
    else:
        hunter.run_analysis(args.output)


if __name__ == "__main__":
    main()
