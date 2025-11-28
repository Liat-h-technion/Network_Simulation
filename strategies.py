import random
from collections import defaultdict, deque
from typing import List, Tuple, Any, Dict
from framework import Scheduler, Protocol, TrafficGenerator, Message, Network


# ---------------------------------------------------------
# Protocol Strategies
# ---------------------------------------------------------
class EchoProtocol(Protocol):
    """
    Upon receiving any message, broadcast a new message to every other process.
    """

    def handle_message(self, my_pid: int, msg: Message, n: int) -> List[Tuple[int, Any]]:
        responses = []
        # Broadcast to everyone except myself
        for target_id in range(n):
            if target_id != my_pid:
                responses.append((target_id, f"Response from {my_pid} to msg {msg.id}"))
        return responses


# ---------------------------------------------------------
# Scheduler Strategies
# ---------------------------------------------------------
class RandomAsynchronousScheduler(Scheduler):
    """
    A specific Scheduler implementation based on the 'Random Asynchronous' model.

    Mechanism:
    1. Messages are grouped by (Sender, Receiver) pairs (links).
    2. To pick the next message, the scheduler randomly selects one active pair.
    3. The earliest message (FIFO) on that specific link is delivered.
    """

    def __init__(self, seed: int = None):
        """
        Args:
            seed: An integer seed. If provided, the simulation run will be
            identical every time for the same seed.
            If None, it uses the system time (non-reproducible).
        """
        # Data Structure: buffers[sender_id][receiver_id] = deque([Msg1, Msg2...])
        super().__init__()
        self.buffers: Dict[int, Dict[int, deque]] = defaultdict(lambda: defaultdict(deque))

        # Create a dedicated random instance for this scheduler
        self.rng = random.Random(seed)

    def _get_pending_links(self):
        """Helper function to find all (sender, receiver) links that have waiting messages."""
        pending_links = []
        for s_id in self.buffers:
            for r_id in self.buffers[s_id]:
                if self.buffers[s_id][r_id]:  # If deque is not empty
                    pending_links.append((s_id, r_id))
        return pending_links

    def add_message(self, msg: Message):
        """Enqueues a message into the specific buffer for its (sender, receiver) link."""
        self.buffers[msg.sender_id][msg.receiver_id].append(msg)

    def send_pending_message(self) -> Message | None:
        pending_links = self._get_pending_links()

        if not pending_links:
            return None

        # Uniformly choose ONE pair of (sender, receiver)
        chosen_sender, chosen_receiver = self.rng.choice(pending_links)

        # Pop the earliest message (FIFO)
        return self.buffers[chosen_sender][chosen_receiver].popleft()

    def has_pending_messages(self) -> bool:
        """Checks if any buffer contains messages."""
        for s_id in self.buffers:
            for r_id in self.buffers[s_id]:
                if self.buffers[s_id][r_id]:
                    return True
        return False

    def get_pending_links_count(self) -> int:
        """Returns |P(t)| (The amount or (sender, receiver) pairs with pending messages.)"""
        return len(self._get_pending_links())

    def get_pending_messages_count(self) -> int:
        """Returns sum of all queue lengths."""
        counter = 0
        for s_id in self.buffers:
            for r_id in self.buffers[s_id]:
                counter += len(self.buffers[s_id][r_id])
        return counter


# ---------------------------------------------------------
# TrafficGenerator Strategies
# ---------------------------------------------------------
class AllToAllTrafficGenerator(TrafficGenerator):
    """
    Strategy: Every process sends a message to every other process.
    Total messages = n * (n - 1).
    """

    def generate(self, network: Network):
        print(f"--- Generating All-to-All Initial Traffic (N={network.n}) ---")
        for sender in range(network.n):
            for receiver in range(network.n):
                if sender != receiver:
                    network.create_initial_message(
                        sender_id=sender,
                        receiver_id=receiver,
                        content=f"INIT {sender}->{receiver}"
                    )
