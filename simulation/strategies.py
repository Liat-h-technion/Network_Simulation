import random
from collections import defaultdict, deque
from typing import List, Tuple, Any, Dict, Set
from simulation.framework import Scheduler, Protocol, TrafficGenerator, Message, Network


# ---------------------------------------------------------
# Protocol Strategies
# ---------------------------------------------------------
class RespondToAllProtocol(Protocol):
    """
    Upon receiving any message, broadcast a new message to every other process.
    """

    def handle_message(self, my_pid: int, process_data: dict, msg: Message, n: int) -> List[Tuple[int, Any]]:
        responses = []
        # Broadcast to everyone except myself
        for target_id in range(n):
            if target_id != my_pid:
                responses.append((target_id, f"Response from {my_pid} to msg {msg.id}"))
        return responses


class RandomSingleMessageProtocol(Protocol):
    """
    Upon receiving any message, sends a new message to a single process, chosen randomly with uniform probability.
    """

    def handle_message(self, my_pid: int, process_data: dict, msg: Message, n: int) -> List[Tuple[int, Any]]:
        responses = []
        candidates = [pid for pid in range(n) if pid != my_pid]
        if candidates:
            target_id = random.choice(candidates)
            content = f"Random forwarding from {my_pid} (origin: {msg.sender_id})"
            responses.append((target_id, content))
        return responses


class RequestResponseProtocol(Protocol):
    def handle_message(self, my_pid: int, process_data: dict, msg: Message, n: int) -> List[Tuple[int, Any]]:
        # Responds only to the original sender, and only if the sender's message isn't a response.
        # In this protocol, each pair of nodes will communicate only once as request-response.
        if "RESPONSE" not in str(msg.content):
            return [(msg.sender_id, f"RESPONSE from {my_pid}")]
        return []


class PingPongProtocol(Protocol):
    def handle_message(self, my_pid: int, process_data: dict, msg: Message, n: int) -> List[Tuple[int, Any]]:
        # Responds to the sender of the received message.
        return [(msg.sender_id, f"Response from {my_pid}")]


class CommitteeProtocol(Protocol):
    """
    A Committee-to-All network:
    1. Committee Members: Can send messages to anyone.
    2. Regular Nodes: Can send messages only to Committee Members.
    """
    def __init__(self, committee_ids: Set[int]):
        """
        Args:
            committee_ids: A set of process IDs that belong to the committee.
        """
        self.committee_ids = committee_ids

    def handle_message(self, my_pid: int, process_data: dict, msg: Message, n: int) -> List[Tuple[int, Any]]:
        responses = []

        if my_pid in self.committee_ids:
            # The process is a Committee Member.
            # Behavior: Broadcast to everyone (except myself).
            for target_id in range(n):
                if target_id != my_pid:
                    responses.append((target_id, f"Committee Broadcast from {my_pid}"))

        else:
            # The process is a regular node.
            # Behavior: Reply only to committee members.
            for target_id in self.committee_ids:
                responses.append((target_id, f"User Report from {my_pid} to Committee"))

        return responses


class Algorithm3Protocol(Protocol):
    def __init__(self, f, R):
        self.f = f
        self.R = R

    def initialize_process_data(self) -> dict:
        """
        Create The process initial data dictionary (initial state), with relevant keys:
        phase: The phase number between 1 and f+1. After f+1 phases, the process decides and terminates.
        round: The round number between 1 and R. After R rounds, the process starts a new phase.
        v_map: Map from processes to signed values. The key is the origin pid.
        phase_round_senders: A dictionary mapping (phase, round) to a set of processes that delivered me messages in
            that phase and round. This is used to keep track of the "valid" number in the algorithm for the current
            round and for future rounds.
            We assume that messages received "too early" are kept for future handling. This assumption was not mentioned
            explicitly in the article, but is needed to ensure termination.
        decided: Boolean, true if the process has decided and otherwise false.
        final_v: The value that the process decided on. While not decided, final_v = -1.
        """
        return {
            "phase": 1,
            "round": 1,
            "v_map": {},
            "phase_round_senders": dict(),  # {(phase, round): set of sender pids}
            "decided": False,
            "final_v": -1
        }

    def print_decision(self, pid: int, process_data: dict):
        print(f"Process {pid} decided {process_data['final_v']}")

    def handle_message(self, my_pid: int, process_data: dict, msg: Message, n: int) -> List[Tuple[int, Any]]:
        """
            The handling logic of Algorithm 3 - Binary Byzantine consensus for n = 2f + 1.
            In this protocol, messages content is a dict with keys:
                phase: The phase in which the message was sent
                round: The round in which the message was sent
                v_map: The v_map of the process that sent the message, updated to when it was sent.

            We check the following conditions on the received v_map:
                1. My process have not yet signed a value from the origin process.
                2. The value is already signed by at least p distinct processes, in current phase p.
            If the conditions hold, the process will sign the value and add it to its v_map.
            After hearing from (n - f) distinct processes in the same round and phase (meaning valid = n - f), we
            advance to the next round. When starting a new round, the process will broadcast its v_map to all others.
            There are f+1 phases in total, and R rounds in each phase.
            After the final phase finishes, the process decides and terminates.
        """
        # If the process has already decided, it will not handle new messages.
        if process_data.get('decided', False):
            return []

        received_v_map = msg.content.get('v_map')
        msg_phase = msg.content.get('phase')
        msg_round = msg.content.get('round')

        curr_phase = process_data['phase']
        curr_round = process_data['round']

        # The outer if statement is for optimization, since we require at least p signatures for current phase p.
        if msg_phase >= curr_phase:
            for origin_pid, (v, signatures) in received_v_map.items():
                if len(signatures) >= curr_phase and origin_pid not in process_data["v_map"]:
                    new_signatures = frozenset(signatures | {my_pid})
                    process_data['v_map'][origin_pid] = (v, new_signatures)

        if msg_phase < curr_phase or (msg_phase == curr_phase and msg_round < curr_round):
            #  Message is from a previous phase / round.
            #  This if statement is for efficiency, to avoid saving past data
            return []

        if (msg_phase, msg_round) not in process_data['phase_round_senders']:
            process_data['phase_round_senders'][(msg_phase, msg_round)] = set()
        process_data['phase_round_senders'][(msg_phase, msg_round)].add(msg.sender_id)

        # valid is the amount of messages from distinct processes, sent in the current phase and round
        valid = len(process_data['phase_round_senders'][(curr_phase, curr_round)])

        responses = []
        if valid >= (n - self.f):
            # Starting a new round.
            process_data['phase_round_senders'].pop((curr_phase, curr_round))  # Cleanup old data (memory optimization)
            if curr_round < self.R:
                process_data['round'] += 1
            else:
                # After R rounds, starting a new phase / terminating when last phase ends.
                process_data['round'] = 1
                if curr_phase < (self.f + 1):
                    process_data['phase'] += 1
                else:
                    process_data['decided'] = True

                    values = [val for val, sigs in process_data['v_map'].values()]
                    process_data['final_v'] = max(set(values), key=values.count)
                    return []

            # Broadcast my v_map to everyone at the start of a new round.
            new_msg_content = {
                "v_map": process_data['v_map'],
                "round": process_data['round'],
                "phase": process_data['phase']
            }
            for target_id in range(n):
                if target_id != my_pid:
                    responses.append((target_id, new_msg_content))

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
        print(f"--- Generating Committee Traffic (Mode: {self.mode}, Committee Size: {len(self.committee_ids)}) ---")

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
