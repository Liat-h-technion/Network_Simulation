import math

from simulation.framework import Simulator
from simulation.strategies import *

if __name__ == "__main__":
    # Configuration
    N_NODES = 20
    COMMITTEE_SIZE = int(math.sqrt(N_NODES))  # Here I chose a committee with size sqrt(n), we can change that.
    MAX_STEPS = 20
    SEED = 100

    # Setup
    # The committee members are consistently the nodes numbered between [0, COMMITTEE_SIZE], we can change that.
    committee = set(range(COMMITTEE_SIZE))
    sim = Simulator(
        n=N_NODES,
        protocol=RespondToAllProtocol(),
        traffic_generator=AllToAllTrafficGenerator(),
        scheduler=RandomAsynchronousScheduler(seed=SEED)
    )

    # Run
    sim.run(max_steps=MAX_STEPS)

    # Analyze
    print("\n--- Analysis Results ---")
    sim.analyzer.print_connectivity_stats()
    sim.analyzer.print_delay_stats()
    sim.analyzer.plot_delay_histogram()

    sim.print_logs(limit=5)
