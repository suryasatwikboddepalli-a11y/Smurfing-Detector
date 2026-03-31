"""
Visualization Module
Creates interactive and static visualizations of the blockchain graph
and detected money laundering patterns
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import plotly.graph_objects as go
from pyvis.network import Network
import numpy as np
from typing import Dict, List, Set
import os


class GraphVisualizer:
    """
    Visualizes blockchain transaction graphs and detected patterns
    """
    
    def __init__(self, blockchain_graph, pattern_detector, suspicion_scorer):
        self.graph = blockchain_graph.graph
        self.blockchain = blockchain_graph
        self.pattern_detector = pattern_detector
        self.suspicion_scorer = suspicion_scorer
        
    def visualize_full_graph(self, output_file: str = "full_graph.html",
                            max_nodes: int = 500):
        """
        Create an interactive visualization of the entire graph
        Uses PyVis for interactive HTML output
        """
        print(f"Creating interactive graph visualization...")
        
        # Limit nodes if graph is too large
        if self.graph.number_of_nodes() > max_nodes:
            # Get top suspicious nodes + illicit nodes
            top_nodes = set([w for w, _ in self.suspicion_scorer.get_top_suspicious_wallets(max_nodes // 2)])
            illicit = set(self.blockchain.illicit_wallets)
            
            # Add some random nodes for context
            all_nodes = set(self.graph.nodes())
            remaining = all_nodes - top_nodes - illicit
            random_nodes = set(list(remaining)[:max_nodes // 4])
            
            selected_nodes = top_nodes | illicit | random_nodes
            subgraph = self.graph.subgraph(selected_nodes)
        else:
            subgraph = self.graph
        
        # Create PyVis network
        net = Network(height="800px", width="100%", directed=True, notebook=False)
        net.barnes_hut(gravity=-10000, central_gravity=0.3, spring_length=100)
        
        # Get wallet scores
        scores = self.suspicion_scorer.wallet_scores
        
        # Add nodes with styling based on suspicion score
        for node in subgraph.nodes():
            score = scores.get(node, 0)
            is_illicit = node in self.blockchain.illicit_wallets
            
            # Color based on suspicion score
            if is_illicit:
                color = '#FF0000'  # Red for known illicit
                size = 30
            elif score >= 80:
                color = '#FF4500'  # Orange-red for critical
                size = 25
            elif score >= 60:
                color = '#FF8C00'  # Dark orange for high
                size = 20
            elif score >= 40:
                color = '#FFA500'  # Orange for medium
                size = 15
            elif score >= 20:
                color = '#FFD700'  # Gold for low
                size = 12
            else:
                color = '#90EE90'  # Light green for minimal
                size = 10
            
            # Create node label
            label = f"{node[:8]}..."
            title = (f"Wallet: {node}<br>"
                    f"Suspicion Score: {score:.2f}<br>"
                    f"Illicit: {is_illicit}<br>"
                    f"In-degree: {self.graph.in_degree(node)}<br>"
                    f"Out-degree: {self.graph.out_degree(node)}")
            
            net.add_node(node, label=label, title=title, color=color, size=size)
        
        # Add edges
        for source, dest, data in subgraph.edges(data=True):
            amount = data.get('amount', 0)
            width = min(np.log10(amount + 1) * 2, 10)
            
            title = f"Amount: {amount:.2f}"
            net.add_edge(source, dest, width=width, title=title, arrows='to')
        
        # Save
        net.save_graph(output_file)
        print(f"Interactive graph saved to {output_file}")
        
    def visualize_pattern(self, pattern, output_file: str = "pattern.png"):
        """
        Visualize a specific detected pattern
        """
        # Create subgraph with pattern nodes
        pattern_nodes = (pattern.source_wallets | pattern.intermediate_wallets | 
                        pattern.destination_wallets)
        
        # Add some connecting edges
        subgraph_nodes = set()
        for node in pattern_nodes:
            subgraph_nodes.add(node)
            # Add neighbors to show connections
            subgraph_nodes.update(list(self.graph.successors(node))[:3])
            subgraph_nodes.update(list(self.graph.predecessors(node))[:3])
        
        subgraph = self.graph.subgraph(subgraph_nodes)
        
        # Create layout
        plt.figure(figsize=(14, 10))
        pos = nx.spring_layout(subgraph, k=2, iterations=50)
        
        # Color nodes by role
        node_colors = []
        node_sizes = []
        
        for node in subgraph.nodes():
            if node in pattern.source_wallets:
                node_colors.append('#FF6B6B')  # Red
                node_sizes.append(1000)
            elif node in pattern.destination_wallets:
                node_colors.append('#4ECDC4')  # Cyan
                node_sizes.append(1000)
            elif node in pattern.intermediate_wallets:
                node_colors.append('#FFE66D')  # Yellow
                node_sizes.append(700)
            else:
                node_colors.append('#C7CEEA')  # Light blue
                node_sizes.append(400)
        
        # Draw graph
        nx.draw_networkx_nodes(subgraph, pos, node_color=node_colors, 
                              node_size=node_sizes, alpha=0.8)
        nx.draw_networkx_edges(subgraph, pos, edge_color='gray', 
                              arrows=True, arrowsize=20, alpha=0.5,
                              connectionstyle='arc3,rad=0.1')
        
        # Labels
        labels = {node: node[:8] for node in subgraph.nodes()}
        nx.draw_networkx_labels(subgraph, pos, labels, font_size=8)
        
        # Legend
        legend_elements = [
            mpatches.Patch(color='#FF6B6B', label='Source Wallet'),
            mpatches.Patch(color='#FFE66D', label='Intermediate Wallet'),
            mpatches.Patch(color='#4ECDC4', label='Destination Wallet'),
            mpatches.Patch(color='#C7CEEA', label='Connected Wallet')
        ]
        plt.legend(handles=legend_elements, loc='upper left')
        
        plt.title(f"{pattern.pattern_type.upper()} Pattern\n"
                 f"Suspicion Score: {pattern.suspicion_score:.2f} | "
                 f"Total Amount: {pattern.total_amount:.2f}")
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Pattern visualization saved to {output_file}")
    
    def visualize_all_patterns(self, output_dir: str = "patterns"):
        """
        Create visualizations for all detected patterns
        """
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Creating visualizations for {len(self.pattern_detector.detected_patterns)} patterns...")
        
        for i, pattern in enumerate(self.pattern_detector.detected_patterns[:20]):  # Limit to top 20
            output_file = os.path.join(output_dir, f"pattern_{i+1}_{pattern.pattern_type}.png")
            self.visualize_pattern(pattern, output_file)
        
        print(f"Pattern visualizations saved to {output_dir}/")
    
    def visualize_illicit_subgraph(self, illicit_wallet: str, 
                                   hops: int = 2, output_file: str = "illicit_subgraph.png"):
        """
        Visualize the subgraph around an illicit wallet
        """
        if illicit_wallet not in self.graph.nodes():
            print(f"Wallet {illicit_wallet} not found in graph")
            return
        
        subgraph = self.blockchain.get_subgraph_around_wallet(illicit_wallet, hops)
        
        plt.figure(figsize=(16, 12))
        pos = nx.spring_layout(subgraph, k=1.5, iterations=50)
        
        # Get suspicion scores
        scores = self.suspicion_scorer.wallet_scores
        
        # Color by suspicion score
        node_colors = []
        node_sizes = []
        
        for node in subgraph.nodes():
            score = scores.get(node, 0)
            
            if node == illicit_wallet:
                node_colors.append('#FF0000')
                node_sizes.append(1200)
            elif score >= 80:
                node_colors.append('#FF4500')
                node_sizes.append(900)
            elif score >= 60:
                node_colors.append('#FF8C00')
                node_sizes.append(700)
            elif score >= 40:
                node_colors.append('#FFA500')
                node_sizes.append(600)
            else:
                node_colors.append('#90EE90')
                node_sizes.append(400)
        
        # Draw
        nx.draw_networkx_nodes(subgraph, pos, node_color=node_colors,
                              node_size=node_sizes, alpha=0.8)
        nx.draw_networkx_edges(subgraph, pos, edge_color='gray',
                              arrows=True, arrowsize=15, alpha=0.4,
                              connectionstyle='arc3,rad=0.1')
        
        labels = {node: node[:8] for node in subgraph.nodes()}
        nx.draw_networkx_labels(subgraph, pos, labels, font_size=7)
        
        plt.title(f"Subgraph around Illicit Wallet: {illicit_wallet[:16]}...\n"
                 f"Showing {hops} hops ({subgraph.number_of_nodes()} wallets, "
                 f"{subgraph.number_of_edges()} transactions)")
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Illicit subgraph visualization saved to {output_file}")
    
    def plot_suspicion_score_distribution(self, output_file: str = "score_distribution.png"):
        """
        Plot the distribution of suspicion scores
        """
        scores = list(self.suspicion_scorer.wallet_scores.values())
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Histogram
        ax1.hist(scores, bins=50, color='steelblue', alpha=0.7, edgecolor='black')
        ax1.set_xlabel('Suspicion Score')
        ax1.set_ylabel('Number of Wallets')
        ax1.set_title('Distribution of Suspicion Scores')
        ax1.axvline(x=60, color='orange', linestyle='--', label='High Risk Threshold')
        ax1.axvline(x=80, color='red', linestyle='--', label='Critical Risk Threshold')
        ax1.legend()
        ax1.grid(alpha=0.3)
        
        # Box plot
        ax2.boxplot(scores, vert=True)
        ax2.set_ylabel('Suspicion Score')
        ax2.set_title('Suspicion Score Statistics')
        ax2.grid(alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Score distribution plot saved to {output_file}")
    
    def create_network_statistics_plot(self, output_file: str = "network_stats.png"):
        """
        Create visualization of network statistics
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Degree distribution
        in_degrees = [d for n, d in self.graph.in_degree()]
        out_degrees = [d for n, d in self.graph.out_degree()]
        
        axes[0, 0].hist(in_degrees, bins=30, alpha=0.6, label='In-degree', color='blue')
        axes[0, 0].hist(out_degrees, bins=30, alpha=0.6, label='Out-degree', color='red')
        axes[0, 0].set_xlabel('Degree')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].set_title('Degree Distribution')
        axes[0, 0].legend()
        axes[0, 0].set_yscale('log')
        axes[0, 0].grid(alpha=0.3)
        
        # Transaction amounts
        amounts = [data['amount'] for _, _, data in self.graph.edges(data=True)]
        axes[0, 1].hist(amounts, bins=50, color='green', alpha=0.7)
        axes[0, 1].set_xlabel('Transaction Amount')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].set_title('Transaction Amount Distribution')
        axes[0, 1].set_yscale('log')
        axes[0, 1].grid(alpha=0.3)
        
        # Pattern statistics
        pattern_types = {}
        for pattern in self.pattern_detector.detected_patterns:
            pattern_types[pattern.pattern_type] = pattern_types.get(pattern.pattern_type, 0) + 1
        
        if pattern_types:
            axes[1, 0].bar(pattern_types.keys(), pattern_types.values(), color='orange', alpha=0.7)
            axes[1, 0].set_xlabel('Pattern Type')
            axes[1, 0].set_ylabel('Count')
            axes[1, 0].set_title('Detected Patterns by Type')
            axes[1, 0].tick_params(axis='x', rotation=45)
            axes[1, 0].grid(alpha=0.3)
        
        # Risk level distribution
        risk_levels = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'MINIMAL': 0}
        for score in self.suspicion_scorer.wallet_scores.values():
            risk_level = self.suspicion_scorer._get_risk_level(score)
            risk_levels[risk_level] += 1
        
        colors_risk = ['#FF0000', '#FF8C00', '#FFA500', '#FFD700', '#90EE90']
        axes[1, 1].bar(risk_levels.keys(), risk_levels.values(), color=colors_risk, alpha=0.7)
        axes[1, 1].set_xlabel('Risk Level')
        axes[1, 1].set_ylabel('Number of Wallets')
        axes[1, 1].set_title('Wallet Risk Level Distribution')
        axes[1, 1].tick_params(axis='x', rotation=45)
        axes[1, 1].grid(alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Network statistics plot saved to {output_file}")
    
    def create_dashboard(self, output_dir: str = "dashboard"):
        """
        Create a complete visualization dashboard
        """
        os.makedirs(output_dir, exist_ok=True)
        
        print("Creating comprehensive visualization dashboard...")
        
        # Full graph
        self.visualize_full_graph(os.path.join(output_dir, "full_graph.html"))
        
        # Score distribution
        self.plot_suspicion_score_distribution(os.path.join(output_dir, "score_distribution.png"))
        
        # Network stats
        self.create_network_statistics_plot(os.path.join(output_dir, "network_stats.png"))
        
        # Patterns
        patterns_dir = os.path.join(output_dir, "patterns")
        self.visualize_all_patterns(patterns_dir)
        
        # Illicit wallet subgraphs
        illicit_dir = os.path.join(output_dir, "illicit_wallets")
        os.makedirs(illicit_dir, exist_ok=True)
        
        for i, illicit_wallet in enumerate(list(self.blockchain.illicit_wallets)[:5]):
            if self.graph.has_node(illicit_wallet):
                output_file = os.path.join(illicit_dir, f"illicit_{i+1}_{illicit_wallet[:8]}.png")
                self.visualize_illicit_subgraph(illicit_wallet, hops=2, output_file=output_file)
        
        print(f"\nDashboard created in {output_dir}/")
        print(f"  - Interactive graph: full_graph.html")
        print(f"  - Score distribution: score_distribution.png")
        print(f"  - Network statistics: network_stats.png")
        print(f"  - Pattern visualizations: patterns/")
        print(f"  - Illicit wallet analysis: illicit_wallets/")
