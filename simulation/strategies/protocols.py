import random
from typing import List, Tuple, Any, Set
from simulation.framework import Protocol, Message


class BroadcastInitMixin:
    """
    A Mixin that provides a standard broadcast initialization.
    Add this to any Protocol class to automatically get this behavior.
    """
    def create_initial_messages(self, my_pid: int, n: int, process_data: dict = None) -> List[Tuple[int, Any]]:
        """
        Broadcasts to every other process.
        Returns:
            List of (receiver, content) for the messages I want to send. This list is returned to the network, which
            creates the messages and schedules them.
        """
        messages_data = []
        for target_id in range(n):
            if target_id != my_pid:
                messages_data.append((target_id, f"INIT {my_pid}->{target_id}"))
        return messages_data


class EchoAllProtocol(BroadcastInitMixin, Protocol):
    """
    Upon receiving any message, broadcast a new message to every other process.
    Initial traffic: Sends a messages to every other process.
    """

    def handle_message(self, my_pid: int, process_data: dict, msg: Message, n: int) -> List[Tuple[int, Any]]:
        responses = []
        # Broadcast to everyone except myself
        for target_id in range(n):
            if target_id != my_pid:
                responses.append((target_id, f"Response from {my_pid} to msg {msg.id}"))
        return responses

    def create_initial_messages(self, my_pid: int, n: int, process_data: dict = None) -> List[Tuple[int, Any]]:
        messages_data = []
        for target_id in range(n):
            if target_id != my_pid:
                messages_data.append((target_id, f"INIT {my_pid}->{target_id}"))
        return messages_data


class RandomSingleMessageProtocol(Protocol):
    """
    Upon receiving any message, sends a new message to a single process, chosen randomly with uniform probability.
    Initial traffic: Sends a messages to a single random node.
    """
    def handle_message(self, my_pid: int, process_data: dict, msg: Message, n: int) -> List[Tuple[int, Any]]:
        responses = []
        candidates = [pid for pid in range(n) if pid != my_pid]
        if candidates:
            target_id = random.choice(candidates)
            content = f"Random forwarding from {my_pid} (origin: {msg.sender_id})"
            responses.append((target_id, content))
        return responses

    def create_initial_messages(self, my_pid: int, n: int, process_data: dict = None) -> List[Tuple[int, Any]]:
        messages_data = []
        candidates = [pid for pid in range(n) if pid != my_pid]
        if candidates:
            target_id = random.choice(candidates)
            content = f"Random init {my_pid}->{target_id}"
            messages_data.append((target_id, content))
        return messages_data


class RequestResponseProtocol(BroadcastInitMixin, Protocol):
    """
    Upon receiving a message, responds only to the original sender, and only if the sender's message isn't a response.
    In this protocol, each pair of nodes will communicate only once as request-response.
    Initial traffic: Sends a messages to every other process.
    """
    def handle_message(self, my_pid: int, process_data: dict, msg: Message, n: int) -> List[Tuple[int, Any]]:
        if "RESPONSE" not in str(msg.content):
            return [(msg.sender_id, f"RESPONSE from {my_pid}")]
        return []


class PingPongProtocol(BroadcastInitMixin, Protocol):
    def handle_message(self, my_pid: int, process_data: dict, msg: Message, n: int) -> List[Tuple[int, Any]]:
        # Responds to the sender of the received message.
        return [(msg.sender_id, f"Response from {my_pid}")]


class CommitteeProtocol(Protocol):
    """
    A Committee-to-All network:
    1. Committee Members: Can send messages to anyone.
    2. Regular Nodes: Can send messages only to Committee Members.
    Upon receiving any message, broadcasts to the committee members.
    Initial traffic: Sends a message to all committee members.
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

    def create_initial_messages(self, my_pid: int, n: int, process_data: dict = None) -> List[Tuple[int, Any]]:
        messages_data = []
        for receiver in self.committee_ids:
            if my_pid != receiver:
                content = f"INIT from {my_pid} to committee member {receiver}"
                messages_data.append((receiver, content))
        return messages_data


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

    def print_decision(self, pid: int, process_data: dict) -> bool:
        print(f"Process {pid} decided {process_data['final_v']}")
        return True

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

        # valid is the amount of messages from distinct processes, sent in the current phase and round.
        # We assume the process has also "sent to itself" a message, so that the condition valid >= n-f can be
        # satisfied in case of f faults.
        valid = len(process_data['phase_round_senders'][(curr_phase, curr_round)]) + 1

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

    def create_initial_messages(self, my_pid: int, n: int, process_data: dict) -> List[Tuple[int, Any]]:
        """
            The process with id `my_pid` and data `process_data` is assigned a random initial value v from {0,1}. v is
            added to the `v_map` of the process with its own signature and its id ad the origin id.
            To kickstart the simulation, the process broadcast its v_map (with the initial value) to all other nodes.
        """
        v = random.choice([0, 1])
        # Add the value v with sender_pid as the origin id and self signature
        process_data["v_map"][my_pid] = (v, frozenset([my_pid]))
        print(f"Process {my_pid} initial input is {v}")

        content = {
            "v_map": process_data["v_map"],
            "round": process_data["round"],
            "phase": process_data["phase"]
        }

        messages_data = []
        for receiver_pid in range(n):
            if my_pid != receiver_pid:
                messages_data.append((receiver_pid, content))
        return messages_data
