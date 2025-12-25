import statistics
import math
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
        # 1. Collect Data
        successful_links = set()
        for log in self._get_delivered_logs():
            successful_links.add((log['sender_id'], log['receiver_id']))

        n = self.network.n
        total_possible = n * (n - 1)
        connected_count = len(successful_links)

        # 2. Print Basic Stats
        print(f"\n--- Connectivity Analysis ---")
        if total_possible > 0:
            print(f"Direct Links: {connected_count}/{total_possible} ({connected_count / total_possible:.1%})")
        else:
            print("Direct Links: 0/0 (N < 2)")

        # ---------------------------------------------------------
        # 3. Partition Analysis (Weakly Connected Components)
        # ---------------------------------------------------------
        # Build UNDIRECTED adjacency list to find isolated islands
        adj_undirected = {i: set() for i in range(n)}
        for u, v in successful_links:
            adj_undirected[u].add(v)
            adj_undirected[v].add(u)

        partitions = []
        visited = set()

        for node_id in range(n):
            if node_id not in visited:
                # Start a new partition discovery
                component = set()
                queue = [node_id]
                visited.add(node_id)
                component.add(node_id)

                while queue:
                    curr = queue.pop(0)
                    for neighbor in adj_undirected[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            component.add(neighbor)
                            queue.append(neighbor)
                partitions.append(component)

        # ---------------------------------------------------------
        # 4. Strong Connectivity Analysis
        # ---------------------------------------------------------
        is_strongly_connected = False
        is_full_mesh = (connected_count == total_possible and n > 1)

        # We only check for strong connectivity if the graph is not partitioned
        if len(partitions) == 1:
            # Build DIRECTED adjacency list
            adj_directed = {i: set() for i in range(n)}
            for u, v in successful_links:
                adj_directed[u].add(v)

            # Check if every node can reach every other node
            is_strongly_connected = True
            for start_node in range(n):
                # BFS from start_node respecting direction
                bfs_visited = {start_node}
                bfs_queue = [start_node]
                while bfs_queue:
                    curr = bfs_queue.pop(0)
                    for neighbor in adj_directed[curr]:
                        if neighbor not in bfs_visited:
                            bfs_visited.add(neighbor)
                            bfs_queue.append(neighbor)

                if len(bfs_visited) != n:
                    is_strongly_connected = False
                    break

        # ---------------------------------------------------------
        # 5. Final Classification Print
        # ---------------------------------------------------------
        if is_full_mesh:
            print("Topology: FULLY CONNECTED (Clique / Full Mesh)")
            print("-> Every node communicated directly with every other node.")

        elif is_strongly_connected:
            print("Topology: STRONGLY CONNECTED")
            print("-> A directed path exists between every pair of nodes (Information flows everywhere).")

        elif len(partitions) == 1:
            print("Topology: WEAKLY CONNECTED")
            print("-> The graph is one piece, but information cannot flow freely in all directions.")

        else:
            print(f"Topology: PARTITIONED ({len(partitions)} Disconnected Groups)")
            print("-> The network is split. Nodes in one group cannot reach nodes in another.")
            for i, part in enumerate(partitions, 1):
                # Sort for cleaner printing
                print(f"   Group {i}: {sorted(list(part))}")

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

    def print_load_stats(self):
        """Prints average backlog and contention from stats logs."""
        stats_logs = [x for x in self.network.logs if x['event_type'] == 'STEP_STATS']

        if not stats_logs:
            print("No stats recorded.")
            return

        backlogs = [x['total_backlog'] for x in stats_logs]
        links = [x['pending_links'] for x in stats_logs]

        avg_backlog = sum(backlogs) / len(backlogs)
        avg_links = sum(links) / len(links)

        print(f"\n--- Network Load Statistics ---")
        print(f"Avg Backlog: {avg_backlog:.1f} messages")
        print(f"Max Backlog: {max(backlogs)} messages")
        print(f"Avg Pending Links: {avg_links:.1f}")

    # ---------------------------------------------------------
    # Plotting & Visualization
    # ---------------------------------------------------------
    def plot_delay_histogram(self, bins=20, filename: Optional[str] = None):
        """
        Standard plotting method using pyplot.
        """
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

    def get_histogram_as_array(self, bins=20):
        """
        Generates the plot in memory and returns it as a NumPy array.
        Uses a robust backend (Agg) to avoid GUI issues.
        """
        if not MATPLOTLIB_AVAILABLE:
            print("Error: 'matplotlib' or 'numpy' not installed.")
            return None

        delays = self._get_delays()
        if not delays:
            return None

        fig = Figure(figsize=(10, 6))
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)

        ax.hist(delays, bins=bins, color='lightgreen', edgecolor='black', alpha=0.7)
        ax.set_title('Delay Distribution (In-Memory)')
        ax.set_xlabel('Delay')
        ax.set_ylabel('Frequency')

        canvas.draw()
        rgba_buffer = canvas.buffer_rgba()
        img_array = np.asarray(rgba_buffer)
        rgb_array = img_array[:, :, :3]

        return rgb_array

    def print_network_partitions(self):
        """
        Identifies and prints network partitions (Weakly Connected Components).
        If the network is split, this will list the separate groups of nodes.
        """
        n = self.network.n

        # 1. Build an UNDIRECTED adjacency list
        # We treat communication as a connection regardless of direction.
        # If A talks to B, or B talks to A, they are in the same 'partition'.
        adj = {i: set() for i in range(n)}
        for log in self._get_delivered_logs():
            u, v = log['sender_id'], log['receiver_id']
            adj[u].add(v)
            adj[v].add(u)  # Add reverse link for undirected check

        # 2. Find Components using BFS
        visited = set()
        partitions = []

        for node_id in range(n):
            if node_id not in visited:
                # Found a new unvisited node -> It starts a new partition
                current_partition = set()
                queue = [node_id]
                visited.add(node_id)
                current_partition.add(node_id)

                while queue:
                    curr = queue.pop(0)
                    for neighbor in adj[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            current_partition.add(neighbor)
                            queue.append(neighbor)

                partitions.append(current_partition)

        # 3. Print Analysis
        print(f"\n--- Network Partition Analysis ---")
        if len(partitions) == 1:
            print(f"Status: Intact (1 Component)")
            print(f"Nodes:  {partitions[0]}")
        else:
            print(f"Status: PARTITIONED ({len(partitions)} disconnected groups)")
            for i, part in enumerate(partitions, 1):
                print(f"  Group {i} (Size {len(part)}): {sorted(list(part))}")
