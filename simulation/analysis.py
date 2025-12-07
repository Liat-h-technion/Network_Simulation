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
        return [x['delay'] for x in self._get_delivered_logs()]

    # ---------------------------------------------------------
    # Textual Analysis
    # ---------------------------------------------------------
    def print_connectivity_stats(self):
        """Prints how many pairs successfully communicated."""
        successful_links = set()
        for log in self._get_delivered_logs():
            successful_links.add((log['sender_id'], log['receiver_id']))

        n = self.network.n
        total_possible = n * (n - 1)
        connected = len(successful_links)

        print(f"\n--- Connectivity Analysis ---")
        if total_possible > 0:
            print(f"Active Links: {connected}/{total_possible} ({connected / total_possible:.1%})")
        else:
            print("Active Links: 0/0 (N < 2)")

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
        n = len(delays)
        # Safe calculation for percentiles even with small data
        p95_idx = min(math.ceil(0.95 * n) - 1, n - 1)
        p99_idx = min(math.ceil(0.99 * n) - 1, n - 1)

        p95 = delays[p95_idx]
        p99 = delays[p99_idx]

        print(f"\n--- Delay Statistics ---")
        print(f"Count:  {n}")
        print(f"Mean:   {mean_val:.2f}")
        print(f"Median: {median_val}")
        print(f"Max:    {max_val}")
        print(f"Min:    {min_val}")
        print(f"P95:    {p95}")
        print(f"P99:    {p99}")

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
