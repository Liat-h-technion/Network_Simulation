import random
from simulation.framework import Network, FaultInjector


class ProbabilisticFaultInjector(FaultInjector):
    """
    At each step, with probability p, kills ONE randomly selected alive process, up to a maximum of 'max_faults' total
    crashes. The "victim" process is chosen uniformly from the group of alive processes.
    """
    def __init__(self, p: float, max_faults: int, seed: int = None):
        self.probability = p
        self.max_faults = max_faults
        self.faults_generated = 0
        self.rng = random.Random(seed)

    def generate_faults(self, network: Network):
        if self.faults_generated >= self.max_faults:
            return

        if self.rng.random() < self.probability:
            alive_pids = [p.id for p in network.processes.values() if p.alive]
            if len(alive_pids) == 0:
                return

            victim_pid = self.rng.choice(alive_pids)
            network.kill_process(victim_pid)
            self.faults_generated += 1
