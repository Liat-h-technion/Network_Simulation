from abc import ABC, abstractmethod
from typing import List, Tuple, Any, Dict
from simulation.analysis import Analyzer
from datetime import datetime


# ---------------------------------------------------------
# Message Class
# ---------------------------------------------------------
class Message:
    def __init__(self, msg_id, sender_id, receiver_id, create_time, content):
        self.id = msg_id
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.create_time = create_time
        self.deliver_time = None
        self.content = content

    def mark_delivered(self, time):
        self.deliver_time = time

    def __repr__(self):
        return f"<Msg {self.id}: {self.sender_id}->{self.receiver_id} content={self.content}>"


# --- Abstract Interfaces (Protocol, Scheduler, TrafficGenerator, FaultInjector) ---

# ---------------------------------------------------------
# Protocol Interface
# ---------------------------------------------------------
class Protocol(ABC):
    """
    Defines HOW a process reacts to a message.
    """

    @abstractmethod
    def handle_message(self, my_pid: int, process_data: dict, msg: Message, n: int) -> List[Tuple[int, Any]]:
        """
        Process an incoming message and determine the reaction.

        Args:
            my_pid: The ID of the process executing this logic.
            process_data: process_data: A dictionary storing the process's internal state,
                updated by the protocol to track algorithmic progress.
            msg: The message being received.
            n: Total number of processes in the network.

        Returns:
            A list of tuples, where each tuple contains:
            (target_receiver_id, content_of_response)
        """
        pass

    def initialize_process_data(self) -> dict:
        """
        TODO: Add a comment
        :return:
        """
        return {}

    def print_decision(self, pid: int, process_data: dict):
        """
        This function can be used in consensus-related protocols, where a process have a final "decision"
        :param pid: The id of the process that utilizes the protocol.
        :param process_data: The data dictionary of the process that utilizes the protocol.
        """
        pass


# ---------------------------------------------------------
# Scheduler Interface
# ---------------------------------------------------------
class Scheduler(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def send_pending_message(self) -> Message | None:
        """
            Selects and returns the next message to be delivered based on the scheduling algorithm.
            A single message is delivered in each global time unit.
            Returns None if no messages are pending.
        """
        pass

    @abstractmethod
    def add_message(self, msg: Message):
        pass

    @abstractmethod
    def has_pending_messages(self) -> bool:
        """Returns True if there is at least one message waiting in the network."""
        pass

    @abstractmethod
    def get_pending_links_count(self) -> int:
        """Returns the number of links (sender->receiver) that have messages waiting."""
        pass

    @abstractmethod
    def get_pending_messages_count(self) -> int:
        """Returns the total number of messages waiting across the entire system."""
        pass

    def handle_process_death(self, pid):
        """Remove all pending messages to the dead process."""
        pass


# ---------------------------------------------------------
# TrafficGenerator Interface
# ---------------------------------------------------------
class TrafficGenerator(ABC):
    """
    Abstract Base Class for traffic initialization strategies.
    Allows switching between different communication scenarios (All-to-All, One-to-One, etc.).
    """

    @abstractmethod
    def generate(self, network: 'Network'):
        """
        Generates the initial messages and injects them into the network.
        Args:
            network: The Network instance to inject messages into.
        """
        pass


# ---------------------------------------------------------
# FaultInjector Interface
# ---------------------------------------------------------
class FaultInjector(ABC):
    """
    Abstract Base Class for fault injections.
    Determines if and when processes crash during the simulation.
    """
    @abstractmethod
    def generate_faults(self, network: 'Network'):
        """
        Called at the beginning of every simulation step.
        Can kill processes by calling process.kill().
        """
        pass


# ---------------------------------------------------------
# Process Class
# ---------------------------------------------------------
class Process:
    def __init__(self, pid: int, my_protocol: Protocol, n: int, data: dict):
        self.id = pid
        self.protocol = my_protocol
        self.n = n
        self.data = data
        self.alive = True

    def handle_received_message(self, msg: Message) -> List[Tuple[int, Any]]:
        """
        Delegates logic to the protocol.
        Returns:
            A list of (receiver_id, content) tuples representing new messages to be sent.
            The messages will be generated by the network and passed to the scheduler.
        """
        return self.protocol.handle_message(self.id, self.data, msg, self.n)

    def kill(self):
        self.alive = False


# ---------------------------------------------------------
# Network Class
# ---------------------------------------------------------
class Network:
    def __init__(self, scheduler: Scheduler, n: int, protocol, enable_full_logs: bool = False):
        self.global_time = 0
        self.scheduler = scheduler
        self.n = n
        self.msg_id_counter = 0  # Used for assigning a unique msg id to a new message.

        # Initialize N processes in the network
        self.processes: Dict[int, Process] = {}
        for i in range(self.n):
            data = protocol.initialize_process_data()
            self.processes[i] = Process(i, protocol, self.n, data)

        # Fields for tracking messages and network connectivity:
        self.enable_full_logs: bool = enable_full_logs
        self.logs: List[Dict[str, Any]] = []  # Full logs are documented if enable_full_logs=True
        self.delay_logs: List[int] = []  # List of message delays (for delay distribution analysis)
        self.successful_links = set()  # Track (sender, receiver) links with successful communication

    def kill_process(self, pid: int):
        """Handle process death from the network. The scheduler removes pending messages to this process."""
        if self.processes[pid].alive:
            self.processes[pid].kill()
            # Remove pending messages to this node from the scheduler
            self.scheduler.handle_process_death(pid)

            if self.enable_full_logs:
                print(f"Process {pid} CRASHED at time step {self.global_time}")

    def create_initial_message(self, sender_id, receiver_id, content):
        """
        Helper to kickstart the simulation.
        Creates a new pending message from the sender to the receiver
        """
        if not self.processes[sender_id].alive or not self.processes[receiver_id].alive:
            return
        msg = Message(self.msg_id_counter, sender_id, receiver_id, self.global_time, content)
        self.msg_id_counter += 1
        self.scheduler.add_message(msg)
        self.log_msg(msg)

    def log_msg(self, msg: Message):
        delay = None
        if msg.deliver_time is not None:
            delay = msg.deliver_time - msg.create_time
            self.delay_logs.append(delay)
            self.successful_links.add((msg.sender_id, msg.receiver_id))

        if self.enable_full_logs:
            event = "DELIVERED" if msg.deliver_time is not None else "CREATED"
            self.logs.append({
                "event_type": event,
                "message_id": msg.id,
                "sender_id": msg.sender_id,
                "receiver_id": msg.receiver_id,
                "create_time": msg.create_time,
                "delay": delay,
                "content": str(msg.content)
            })

    def log_step_stats(self):
        """Logs the system state at the end of a step."""
        log_entry = {
            "event_type": "STEP_STATS",
            "global_time": self.global_time,
            "pending_links": self.scheduler.get_pending_links_count(),
            "total_pending_messages": self.scheduler.get_pending_messages_count()
        }
        self.logs.append(log_entry)

    def run_step(self):
        """
        Executes exactly one event delivery in the network.
        Returns False if there are no more pending messages in the network, and otherwise True.
        """
        if not self.scheduler.has_pending_messages():
            print("No more messages to deliver.")
            return False

        # Scheduler picks a message to deliver
        msg = self.scheduler.send_pending_message()
        if not msg:
            return False
        msg.mark_delivered(self.global_time)
        self.log_msg(msg)

        # Advance global time
        self.global_time += 1

        # Update the successful_links set, if this is the first communication for that (sender, receiver) link
        self.successful_links.add((msg.sender_id, msg.receiver_id))

        # Process handles message using its protocol to generate new traffic
        # Then, the network asks the scheduler to schedule each generated response
        receiver_process = self.processes[msg.receiver_id]
        raw_responses = receiver_process.handle_received_message(msg)

        for target_id, content in raw_responses:
            # The network doesn't schedule messages to dead nodes
            if not self.processes[target_id].alive:
                continue

            new_msg = Message(
                msg_id=self.msg_id_counter,
                sender_id=receiver_process.id,
                receiver_id=target_id,
                create_time=self.global_time,
                content=content
            )
            self.msg_id_counter += 1

            self.scheduler.add_message(new_msg)
            self.log_msg(new_msg)

        # self.log_step_stats()
        return True

    def print_processes_decisions(self):
        """
        Prints the decision of each process in the network.
        This method can be used with consensus protocols that implement the print_decision methods. Protocols that don't
        implement this method will print nothing.
        """
        print("\n")
        for pid, p in self.processes.items():
            if p.alive:
                p.protocol.print_decision(pid, p.data)
            else:
                print(f"Process {pid} crashed.")


# ---------------------------------------------------------
# Simulator Class
# ---------------------------------------------------------
class Simulator:
    """
    Encapsulates the simulation environment.
    Responsible for initialization, execution, and providing analysis tools.
    """

    def __init__(self, n: int, protocol: Protocol, traffic_generator: TrafficGenerator, scheduler: Scheduler,
                 fault_injector: FaultInjector | None, enable_full_logs: bool, analysis_interval: int, display_plots: bool):
        """
        Initialize the simulation environment.

        Args:
            n: Number of processes.
            protocol: The behavior strategy for processes. For now, we allow a single protocol of all process.
            traffic_generator: Strategy for initial traffic.
            scheduler: The scheduling algorithm instance.
        """
        self.n = n
        self.network = Network(scheduler, self.n, protocol, enable_full_logs)
        self.fault_injector = fault_injector
        self.traffic_generator = traffic_generator
        self.analyzer = Analyzer(self.network)
        self.analysis_interval = analysis_interval
        self.display_plots = display_plots

    def run(self, max_steps: int | None = None) -> int:
        """
        Runs the simulation.
        1. Triggers traffic generation.
        2. Runs the loop for `max_steps`. If 'max_steps' is not specified, will run indefinitely.
           Once in every analysis_interval steps, performs connectivity analysis. If analysis_interval is None, will
           not perform mid-simulation analysis.

        Returns:
            The number of steps actually executed.
        """
        sim_start = datetime.now()
        limit = max_steps if max_steps is not None else float('inf')

        print(f"--- Starting Simulation (Max Steps: {limit}) ---")

        # Generate Initial Traffic and run first step of the simulation
        # Processes may crash even before sending initial traffic
        if self.fault_injector:
            self.fault_injector.generate_faults(self.network)
        self.traffic_generator.generate(self.network)
        self.network.run_step()

        # Run the rest of the simulation until max_steps or until there are no pending messages in the network
        # In each step there might be crash-faults, and a single message is delivered in the network
        steps_executed = 1
        while steps_executed < limit:
            if self.fault_injector:
                self.fault_injector.generate_faults(self.network)

            if not self.network.run_step():
                print("Simulation stopped: No more pending messages.")
                break
            steps_executed += 1

            # Perform connectivity analysis every analysis_interval steps, until reaching strong connectivity.
            # If the graph is not yet weakly connected and display_plots flag was used, also plot the network graph.
            if self.analysis_interval and steps_executed % self.analysis_interval == 0 \
                    and self.analyzer.strongly_connected_at is None:
                self.analyzer.print_connectivity_stats()
                if self.display_plots and self.analyzer.weakly_connected_at is None:
                    self.analyzer.plot_network_topology()

        sim_end = datetime.now()
        print(f"\n--- Simulation Finished after {steps_executed} steps (run time: {sim_end - sim_start} seconds) ---")
        self.network.print_processes_decisions()

        return steps_executed

    def print_logs(self, limit=10):
        delivered = [x for x in self.network.logs if x['event_type'] == "DELIVERED"]
        if len(delivered) > 0:
            print(f"\n--- Message Delivery Logs ({limit} Steps) ---")
            for l in delivered[:limit]:
                print(
                    f"Create Time: {l['create_time']} | Deliver Time: {l['create_time'] + l['delay']} | From pid {l['sender_id']} to pid {l['receiver_id']} (Delay: {l['delay']}) with content: {l['content']}")

        stats = [x for x in self.network.logs if x['event_type'] == "STEP_STATS"]
        if len(stats) > 0:
            print(f"\n--- Network Logs ({limit} Steps) ---")
            for stat in stats[:limit]:
                print(f"Step {stat['global_time']}: ",
                      f"Pending links: {stat['pending_links']}, ",
                      f"pending messages: {stat['total_pending_messages']}")
