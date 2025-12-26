import statistics
import math
import networkx as nx
from typing import List, TYPE_CHECKING, Optional

# ---------------------------------------------------------
# Fix for Matplotlib/PyCharm Crash
# ---------------------------------------------------------
try:
    import matplotlib

    # Force Matplotlib to use 'TkAgg' (Standard Window) instead of PyCharm's backend
    # This bypasses the 'FigureCanvasInterAgg' error.
    matplotlib.use('TkAgg')

    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    import numpy as np

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    # Fallback if Tkinter is not installed or Matplotlib is missing
    try:
        import matplotlib.pyplot as plt

        MATPLOTLIB_AVAILABLE = True
    except ImportError:
        MATPLOTLIB_AVAILABLE = False
        print("Warning: Matplotlib not found. Plotting disabled.")

if TYPE_CHECKING:
    from simulation.framework import Network


class Analyzer:
    def __init__(self, network: 'Network'):
        self.network = network

    # ---------------------------------------------------------
    # Helper Methods
    # ---------------------------------------------------------
    def _get_delivered_logs(self):
        return [x for x in self.network.logs if x['event_type'] == 'DELIVERED']

    def _get_delays(self) -> List[int]:
        return self.network.delay_logs

    # ---------------------------------------------------------
    # Textual Analysis
    # ---------------------------------------------------------
    def print_connectivity_stats(self):
        """
        Analyzes the network topology based on delivered messages.
        Checks for Full Connectivity, Strong Connectivity, and Partitions.
        """
        links = self.network.successful_links
        n = self.network.n
        steps = self.network.global_time

        total_possible = n * (n - 1)
        connected_count = len(links)

        print(f"\n--- Connectivity Analysis (After {steps} Steps) ---")
        print(f"Direct Links: {connected_count}/{total_possible} ({connected_count / total_possible:.1%})")

        # Create undirected graph for partitions check
        G_undirected = nx.Graph()
        G_undirected.add_nodes_from(range(n))
        G_undirected.add_edges_from(links)

        # Partition Analysis
        partitions = list(nx.connected_components(G_undirected))
        num_partitions = len(partitions)

        if num_partitions > 1:
            print(f"Topology: PARTITIONED ({num_partitions} Groups)")
            for i, group in enumerate(partitions, 1):
                print(f"   Group {i}: {sorted(list(group))}")
            return  # Exit early: if partitioned, the graph can't be strongly connected

        # If not partitioned, create the Directed version for checking strong connectivity and full mesh
        G_directed = nx.DiGraph()
        G_directed.add_nodes_from(range(n))
        G_directed.add_edges_from(links)

        if nx.is_strongly_connected(G_directed):
            if connected_count == total_possible:
                print("Topology: FULLY CONNECTED (Clique / Full Mesh)")
                print("-> Every node communicated directly with every other node.")
            else:
                print("Topology: STRONGLY CONNECTED")
                print("-> A directed path exists between every pair of nodes (Information flows everywhere).")
        else:
            print("Topology: WEAKLY CONNECTED")
            print("-> The graph is one piece, but information cannot flow freely in all directions.")

    def print_delay_stats(self):
        """Prints statistical summary of message delays."""
        delays = self._get_delays()
        if not delays:
            print("\n--- Delay Statistics ---")
            print("No messages delivered.")
            return

        mean_val = statistics.mean(delays)
        median_val = statistics.median(delays)
        max_val = max(delays)
        min_val = min(delays)

        delays.sort()

        print(f"\n--- Delay Statistics ---")
        print(f"Mean:   {mean_val:.2f}")
        print(f"Median: {median_val}")
        print(f"Max:    {max_val}")
        print(f"Min:    {min_val}")

    # ---------------------------------------------------------
    # Plotting & Visualization
    # ---------------------------------------------------------
    def plot_delay_histogram(self, bins=20, filename: Optional[str] = None):
        if not MATPLOTLIB_AVAILABLE:
            print("Error: 'matplotlib' not installed.")
            return

        delays = self._get_delays()
        if not delays:
            print("No data to plot.")
            return

        plt.figure(figsize=(10, 6))
        plt.hist(delays, bins=bins, color='skyblue', edgecolor='black', alpha=0.7)

        mean_val = statistics.mean(delays)
        plt.axvline(mean_val, color='red', linestyle='dashed', linewidth=1, label=f'Mean: {mean_val:.1f}')

        plt.title('Message Delay Distribution')
        plt.xlabel('Delay (Time Steps)')
        plt.ylabel('Frequency')
        plt.legend()
        plt.grid(axis='y', alpha=0.5)

        if filename:
            plt.savefig(filename)
            print(f"Plot saved to {filename}")
        else:
            # This should now open a popup window without crashing PyCharm
            plt.show()

    def plot_network_topology(self):
        links = self.network.successful_links
        n = self.network.n

        plt.clf()  # Clear the current figure

        # Create the Graph
        G = nx.Graph()
        G.add_nodes_from(range(n))
        G.add_edges_from(links)

        pos = nx.spring_layout(G, k=1/math.sqrt(n), iterations=int(math.sqrt(n)))

        plt.title(f"Network Topology - Step {self.network.global_time}\nLinks: {len(links)}")
        nx.draw(G, pos, node_size=30, alpha=0.5)
        plt.pause(1)  # Keep the GUI open for 1s
