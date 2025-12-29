import random
from collections import defaultdict, deque
from typing import Dict
from simulation.framework import Scheduler, Message


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
        self.active_links = []  # List of pending (sender, receiver) links. We use a list for O(1) random element choice
        self.links_indices = {}  # Mapping of (sender, receiver) to index in active_links (used for optimization)
        self.pending_messages_counter = 0

        # Create a dedicated random instance for this scheduler
        self.rng = random.Random(seed)

    def add_message(self, msg: Message):
        """Enqueues a message into the specific buffer for its (sender, receiver) link.
        If the link didn't have any pending messages, add it to the active_links list."""
        s, r = msg.sender_id, msg.receiver_id
        self.buffers[s][r].append(msg)
        self.pending_messages_counter += 1

        # If the (s, r) link didn't have messages in the deque, add it to active_links and save its index
        if (s, r) not in self.links_indices:
            self.links_indices[(s, r)] = len(self.active_links)
            self.active_links.append((s, r))

    def send_pending_message(self) -> Message | None:
        if not self.active_links:
            return None

        # Uniformly choose ONE pair of (sender, receiver)
        chosen_idx = self.rng.randrange(len(self.active_links))
        s, r = self.active_links[chosen_idx]

        # Pop the earliest message (FIFO)
        msg = self.buffers[s][r].popleft()
        self.pending_messages_counter -= 1

        # If the messages deque for this link is now empty, remove it from active_links (O(1) removal with Swap-and-Pop)
        if not self.buffers[s][r]:
            last_link = self.active_links[-1]
            self.active_links[chosen_idx] = last_link
            self.links_indices[last_link] = chosen_idx
            self.active_links.pop()
            del self.links_indices[(s, r)]

        return msg

    def has_pending_messages(self) -> bool:
        """Checks if any there are any active links with pending messages."""
        return len(self.active_links) > 0

    def get_pending_links_count(self) -> int:
        """Returns |P(t)| (The amount or (sender, receiver) pairs with pending messages.)"""
        return len(self.active_links)

    def get_pending_messages_count(self) -> int:
        """Returns the amount of pending messages that are waiting to be delivered."""
        return self.pending_messages_counter
