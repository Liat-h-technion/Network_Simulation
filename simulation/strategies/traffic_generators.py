import random
from typing import Set
from simulation.framework import TrafficGenerator, Network


class AllToAllTrafficGenerator(TrafficGenerator):
    """
    Strategy: Every process sends a message to every other process.
    Total messages = n * (n - 1).
    """

    def generate(self, network: Network):
        for sender in range(network.n):
            for receiver in range(network.n):
                if sender != receiver:
                    network.create_initial_message(
                        sender_id=sender,
                        receiver_id=receiver,
                        content=f"INIT {sender}->{receiver}"
                    )


class CommitteeTrafficGenerator(TrafficGenerator):
    """
    Generates initial traffic respecting the committee topology.
    Can operate in two modes:
    1. 'all-to-committee': All nodes send a request to the committee.
    2. 'committee-to-all': The committee broadcasts to everyone.
    """
    def __init__(self, committee_ids: Set[int], mode):
        self.committee_ids = committee_ids
        self.mode = mode

    def generate(self, network: Network):
        if self.mode == 'all-to-committee':
            for sender in range(network.n):
                for receiver in self.committee_ids:
                    if sender != receiver:
                        network.create_initial_message(sender, receiver, f"INIT_REQUEST {sender}->{receiver}")

        elif self.mode == 'committee-to-all':
            for sender in self.committee_ids:
                for receiver in range(network.n):
                    if sender != receiver:
                        network.create_initial_message(sender, receiver, f"INIT_COMMAND {sender}->{receiver}")

        else:
            raise ValueError(f"Invalid mode '{self.mode}'. Expected 'all-to-committee' or 'committee-to-all'.")


class Algorithm3TrafficGenerator(TrafficGenerator):
    def __init__(self, input_strategy="random"):
        self.input_strategy = input_strategy

    def generate(self, network: Network):
        for sender_pid in range(network.n):
            process = network.processes[sender_pid]

            if self.input_strategy == "random":
                v = random.choice([0, 1])
            else:
                v = self.input_strategy

            # Add the value v with sender_pid as the origin id and self signature
            process.data["v_map"][sender_pid] = (v, frozenset([sender_pid]))
            print(f"Process {sender_pid} initial input is {v}")

            content = {
                "v_map": process.data["v_map"],
                "round": process.data["round"],
                "phase": process.data["phase"]
            }

            for receiver_pid in range(network.n):
                if sender_pid != receiver_pid:
                    network.create_initial_message(sender_pid, receiver_pid, content)
