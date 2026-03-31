#!/usr/bin/env python
"""
Smurfing Hunter - Complete Demo Script
Runs the entire money laundering detection system and displays results
"""

import os
import sys
from datetime import datetime

# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

def print_banner(text, char="="):
    """Print a formatted banner"""
    width = 80
    print("\n" + char * width)
    print(text.center(width))
    print(char * width + "\n")

def print_section(text):
    """Print a section header"""
    print("\n" + "─" * 80)
    print(f"▶ {text}")
    print("─" * 80)

def main():
    print_banner("SMURFING HUNTER - COMPLETE DEMONSTRATION", "═")
    print("Money Laundering Detection in Blockchain Transactions")
    print("Domain: RegTech / Crypto-Forensics / Graph Theory")
    print(f"\nDemo Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Step 1: Generate Sample Data
    print_section("STEP 1: Generating Sample Blockchain Data")
    
    from smurfing_hunter.data.generate_sample_data import DataGenerator
    
    generator = DataGenerator(seed=42)
    os.makedirs('data', exist_ok=True)
    transactions_file, illicit_file = generator.generate_complete_dataset(output_dir='data')
    
    print(f"✓ Generated {transactions_file}")
    print(f"✓ Generated {illicit_file}")

    # Step 2: Load and Build Graph
    print_section("STEP 2: Building Blockchain Transaction Graph")
    
    from smurfing_hunter.core.graph_builder import BlockchainGraph
    
    blockchain = BlockchainGraph()
    blockchain.load_transactions(transactions_file)
    blockchain.load_illicit_wallets(illicit_file)
    
    print(f"✓ Loaded {len(blockchain.transactions)} transactions")
    print(f"✓ Graph contains {blockchain.graph.number_of_nodes()} wallets")
    print(f"✓ Graph contains {blockchain.graph.number_of_edges()} transaction edges")
    print(f"✓ Identified {len(blockchain.illicit_wallets)} illicit seed wallets")

    # Step 3: Detect Patterns
    print_section("STEP 3: Detecting Money Laundering Patterns")
    
    from smurfing_hunter.core.pattern_detector import PatternDetector
    
    detector = PatternDetector(blockchain)
    patterns = detector.detect_all_patterns_from_illicit()
    
    print("\nPattern Detection Results:")
    for pattern_type, pattern_list in patterns.items():
        print(f"  • {pattern_type.replace('_', ' ').title()}: {len(pattern_list)} patterns detected")
    
    total_patterns = sum(len(p) for p in patterns.values())
    print(f"\n✓ Total patterns detected: {total_patterns}")
    
    # Show pattern statistics
    stats = detector.get_pattern_statistics()
    if stats:
        print(f"✓ Average suspicion score: {stats['avg_suspicion_score']:.2f}/100")
        print(f"✓ Maximum suspicion score: {stats['max_suspicion_score']:.2f}/100")
        print(f"✓ Total amount flagged: ${stats['total_amount_flagged']:,.2f}")

    # Step 4: Calculate Suspicion Scores
    print_section("STEP 4: Calculating Wallet Suspicion Scores")
    
    from smurfing_hunter.core.suspicion_scorer import SuspicionScorer
    
    scorer = SuspicionScorer(blockchain, detector)
    scores = scorer.calculate_all_scores()
    
    print(f"✓ Calculated scores for {len(scores)} wallets")
    
    # Risk distribution
    risk_levels = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'MINIMAL': 0}
    for score in scores.values():
        risk_levels[scorer._get_risk_level(score)] += 1
    
    print("\nRisk Level Distribution:")
    for level, count in risk_levels.items():
        percentage = (count / len(scores)) * 100
        bar = "█" * int(percentage / 2)
        print(f"  {level:8s}: {count:3d} wallets ({percentage:5.1f}%) {bar}")

    # Step 5: Show Top Suspicious Wallets
    print_section("STEP 5: Top 10 Most Suspicious Wallets")
    
    top_wallets = scorer.get_top_suspicious_wallets(10)
    
    print("\n{:3s} {:20s} {:8s} {:10s} {:8s}".format(
        "Rnk", "Wallet ID", "Score", "Risk", "Illicit"))
    print("─" * 80)
    
    for i, (wallet, score) in enumerate(top_wallets, 1):
        risk_level = scorer._get_risk_level(score)
        is_illicit = wallet in blockchain.illicit_wallets
        illicit_str = "Yes" if is_illicit else "No"
        
        # Color coding
        if risk_level == "CRITICAL":
            color = "\033[91m"  # Red
        elif risk_level == "HIGH":
            color = "\033[93m"  # Yellow
        elif risk_level == "MEDIUM":
            color = "\033[94m"  # Blue
        else:
            color = "\033[92m"  # Green
        reset = "\033[0m"
        
        print(f"{color}{i:2d}. {wallet[:18]:18s}... {score:6.2f} {risk_level:10s} {illicit_str:8s}{reset}")

    # Step 6: Detailed Analysis of Top Wallet
    print_section("STEP 6: Detailed Risk Assessment - Top Wallet")
    
    top_wallet_id, top_score = top_wallets[0]
    assessment = scorer.get_wallet_risk_assessment(top_wallet_id)
    
    print(f"\nWallet: {top_wallet_id}")
    print(f"Overall Suspicion Score: {assessment['overall_suspicion_score']:.2f}/100")
    print(f"Risk Level: {assessment['risk_level']}")
    
    print("\nScore Components:")
    components = assessment['score_components']
    print(f"  • Centrality Score:         {components['centrality_score']:6.2f}/100")
    print(f"  • Illicit Proximity Score:  {components['illicit_proximity_score']:6.2f}/100")
    print(f"  • Pattern Involvement Score:{components['pattern_involvement_score']:6.2f}/100")
    print(f"  • Structural Anomaly Score: {components['structural_anomaly_score']:6.2f}/100")
    
    print("\nWallet Features:")
    features = assessment['wallet_features']
    print(f"  • In-degree:  {features.get('in_degree', 0)}")
    print(f"  • Out-degree: {features.get('out_degree', 0)}")
    print(f"  • Total received: ${features.get('total_received', 0):,.2f}")
    print(f"  • Total sent:     ${features.get('total_sent', 0):,.2f}")
    print(f"  • Balance:        ${features.get('balance', 0):,.2f}")
    
    print("\nIllicit Connection:")
    illicit_conn = assessment['illicit_connection']
    print(f"  • Is known illicit: {illicit_conn['is_illicit']}")
    if illicit_conn['distance_to_illicit']:
        print(f"  • Distance to illicit: {illicit_conn['distance_to_illicit']} hops")
    
    print(f"\nPatterns Involved: {assessment['patterns_involved']}")
    if assessment['pattern_types']:
        print(f"Pattern Types: {', '.join(set(assessment['pattern_types']))}")

    # Step 7: Generate Visualizations
    print_section("STEP 7: Creating Visualizations")
    
    from smurfing_hunter.utils.visualizer import GraphVisualizer
    
    output_dir = "demo_results"
    os.makedirs(output_dir, exist_ok=True)
    
    visualizer = GraphVisualizer(blockchain, detector, scorer)
    
    print("\nGenerating visualization dashboard...")
    print("  • Creating interactive graph...")
    visualizer.visualize_full_graph(f"{output_dir}/full_graph.html", max_nodes=200)
    
    print("  • Creating score distribution chart...")
    visualizer.plot_suspicion_score_distribution(f"{output_dir}/score_distribution.png")
    
    print("  • Creating network statistics...")
    visualizer.create_network_statistics_plot(f"{output_dir}/network_stats.png")
    
    print("  • Visualizing top patterns...")
    for i, pattern in enumerate(detector.detected_patterns[:5], 1):
        visualizer.visualize_pattern(pattern, f"{output_dir}/pattern_{i}.png")
    
    print("\n✓ Visualizations created in demo_results/")

    # Step 8: Generate Report
    print_section("STEP 8: Generating Risk Assessment Report")
    
    report_file = f"{output_dir}/risk_report.txt"
    scorer.generate_risk_report(report_file)
    
    print(f"✓ Risk report saved to {report_file}")

    # Summary
    print_banner("DEMONSTRATION COMPLETE", "═")
    
    print("Summary of Results:")
    print(f"  • Total wallets analyzed:     {len(scores)}")
    print(f"  • Known illicit wallets:      {len(blockchain.illicit_wallets)}")
    print(f"  • Patterns detected:          {total_patterns}")
    print(f"  • High-risk wallets (≥60):    {sum(1 for s in scores.values() if s >= 60)}")
    print(f"  • Critical-risk wallets (≥80): {sum(1 for s in scores.values() if s >= 80)}")
    
    print("\nGenerated Files:")
    print(f"  📄 Data Files:")
    print(f"     • {transactions_file}")
    print(f"     • {illicit_file}")
    print(f"\n  📊 Visualizations:")
    print(f"     • {output_dir}/full_graph.html (Interactive - Open in browser!)")
    print(f"     • {output_dir}/score_distribution.png")
    print(f"     • {output_dir}/network_stats.png")
    print(f"     • {output_dir}/pattern_1.png through pattern_5.png")
    print(f"\n  📋 Reports:")
    print(f"     • {output_dir}/risk_report.txt")
    
    print("\nNext Steps:")
    print("  1. Open demo_results/full_graph.html in your browser for interactive exploration")
    print("  2. Review demo_results/risk_report.txt for detailed analysis")
    print("  3. Check visualizations for pattern insights")
    print("  4. Run 'python smurfing_hunter.py --help' for more options")
    
    print(f"\nDemo Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "═" * 80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError during demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
