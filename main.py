import argparse

from simulation.framework import Simulator
from simulation.strategies.protocols import *
from simulation.strategies.schedulers import *
from simulation.strategies.fault_injectors import *


PROTOCOLS = {
    "alg3": Algorithm3Protocol,
    "echo_all": EchoAllProtocol,
    "ping_pong": PingPongProtocol,
    "random_single_message": RandomSingleMessageProtocol,
    "committee": CommitteeProtocol
}

SCHEDULERS = {
    "random": RandomAsynchronousScheduler
}

FAULT_INJECTORS = {
    "probabilistic": ProbabilisticFaultInjector
}


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--protocol", type=str, required=True, choices=PROTOCOLS.keys())
    parser.add_argument("--scheduler", type=str, required=True, choices=SCHEDULERS.keys())
    parser.add_argument("--fault-injector", type=str, required=False, choices=FAULT_INJECTORS.keys())

    parser.add_argument("--nodes", type=int, default=20)
    parser.add_argument("--max-steps", type=int, default=None,
                        help="Maximum simulation steps. If omitted, the simulation runs until there are no pending "
                             "messages in the network.\nNote: some protocols may run indefinitely without this limit.")

    parser.add_argument("--f", type=int, default=None, help="By default, algorithm 3 uses n = 2f + 1.")
    parser.add_argument("--R", type=int, default=None,
                        help="Amount of rounds in each phase. Required parameter when running Algorithm 3.")
    parser.add_argument("--committee-size", type=int, help="Required parameter when using committee protocol.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for the scheduler.")
    parser.add_argument("--fault-prob", type=float, default=1.0,
                        help="The probability of a crash fault occurring in a time step. This argument is used when "
                             "simulating with a probabilistic fault injector.")

    parser.add_argument("--analysis-interval", type=int, default=None)
    parser.add_argument("--enable-full-logs", action="store_true")
    parser.add_argument("--display-plots", action="store_true")

    args = parser.parse_args()

    # Select Protocol
    if args.protocol == "alg3":
        if args.R is None:
            parser.error("argument --R is required when --protocol is set to 'alg3'")
        f = args.f if args.f is not None else (args.nodes - 1) // 2
        protocol = Algorithm3Protocol(f=f, R=args.R)
    elif args.protocol == "committee":
        # The committee members are consistently the nodes numbered between [0, committee-size].
        if args.committee_size is None:
            parser.error("argument --committee-size is required when --protocol is set to 'committee'")
        committee = set(range(args.committee_size))
        protocol = CommitteeProtocol(committee_ids=committee)
    else:
        protocol = PROTOCOLS[args.protocol]()

    # Select Scheduler
    scheduler = SCHEDULERS[args.scheduler](seed=args.seed)

    # Select Fault Injector
    if args.fault_injector == "probabilistic":
        if args.f is None:
            parser.error("argument --f is required when --fault-injector is set to 'probabilistic'")
        fault_injector = ProbabilisticFaultInjector(
            p=args.fault_prob,
            max_faults=args.f,
            seed=args.seed
        )
    elif args.fault_injector is not None:
        fault_injector = FAULT_INJECTORS[args.fault_injector]()
    else:
        fault_injector = None

    # Initialize and run Simulator
    sim = Simulator(
        n=args.nodes,
        protocol=protocol,
        scheduler=scheduler,
        fault_injector=fault_injector,
        enable_full_logs=args.enable_full_logs,
        analysis_interval=args.analysis_interval,
        display_plots=args.display_plots
    )

    total_steps = sim.run(max_steps=args.max_steps)

    # Logs
    if args.enable_full_logs:
        sim.print_logs(limit=total_steps)

    # Analysis
    print("\n--- Analysis Results ---")
    sim.analyzer.print_connectivity_stats()
    sim.analyzer.print_connectivity_milestones()
    sim.analyzer.print_delay_stats()
    if sim.display_plots:
        sim.analyzer.plot_delay_histogram()


if __name__ == "__main__":
    main()
