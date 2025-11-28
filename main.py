from framework import Simulator
from strategies import EchoProtocol, RandomAsynchronousScheduler, AllToAllTrafficGenerator

if __name__ == "__main__":
    # Configuration
    N_NODES = 10
    MAX_STEPS = 1000
    SEED = 42

    # Setup
    sim = Simulator(
        n=N_NODES,
        protocol=EchoProtocol(),
        traffic_generator=AllToAllTrafficGenerator(),
        scheduler=RandomAsynchronousScheduler(seed=SEED)
    )

    # Run
    sim.run(max_steps=MAX_STEPS)

    # Analyze
    avg_delay = sim.get_average_delay()
    connected, total = sim.get_connectivity_stats()

    print("\n--- Analysis Results ---")
    print(f"Average Delay: {avg_delay:.2f} time ticks")
    print(f"Connectivity: {connected}/{total} pairs communicated ({connected / total:.1%})")

    sim.print_logs(limit=5)
