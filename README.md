# Network Simulation Framework

A Python simulator for testing the behaviour of the Random Asynchronous Model,
described in the article `Byzantine Consensus in the Random Asynchronous Model`.
The simulator creates traffic in a distributed network, using different protocols, scheduling, and initialization patterns.

## Quick Start

1. **Install requirements** (optional, for plotting graphs):
   ```bash
   pip install matplotlib
   ```
   
2. **Run the simulation**
   ```bash
   python main.py
   ```

## Configuration

Open ```main.py``` to adjust the basic simulation parameters:
    ```python
    N_NODES = 20           # Number of nodes
    COMMITTEE_SIZE = 4     # Number of committee members (if using CommitteeProtocol)
    MAX_STEPS = 5000       # Simulation duration limit
    SEED = 42              # Random seed for reproducibility    
    ```

## Changing Behavior
To change how nodes communicate, edit the Simulator initialization in ```main.py``` by swapping the classes below.

### Available Protocols (Node Logic)
Import these from ```simulation.strategies```
* EchoProtocol: Upon receiving a message, broadcasts to all nodes. 
* RandomSingleMessageProtocol: Forwards received messages to one random node. 
* PingPongProtocol: Replies only once to the sender (in a single request-response form).
* RespondToSenderProtocol: Always sends a response back to the sender. 
* CommitteeProtocol: Committee members broadcast; regular nodes only report to the committee.

### Traffic Generators (Initial Traffic in The Network)
* AllToAllTrafficGenerator: Every node sends a message to every other node.
* CommitteeTrafficGenerator: Sets up traffic either from everyone to the committee or from the committee to everyone.