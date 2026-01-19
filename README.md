# Network Simulation Framework & Random Asynchronous Model

A Python discrete-event simulator designed to analyze distributed algorithms under the **Random Asynchronous Model**.

This project implements the theoretical framework and algorithms described in the paper *Byzantine Consensus in the Random Asynchronous Model*. It allows for the simulation of message passing, network connectivity analysis, and specific consensus protocols (like Algorithm 3) to verify theoretical probabilistic guarantees.

## Features

* **Random Asynchronous Scheduler:** Implements a non-adversarial scheduler where message delivery order is determined by randomly selecting sender-receiver pairs.
In each time-step of the simulation, a ***single*** sender-receiver link is chosen ***with uniform probability*** from the current active links.


* **Consensus Simulation:** Full implementation of **Algorithm 3** (Binary Byzantine Consensus for n=2f+1) from the source paper.


* **Connectivity Analysis:** Mid-simulation tracking of network topology (Weakly/Strongly Connected components) and partition detection, at chosen time intervals.


* **Visualizations:** Histograms of message delays and network topology graphs using `matplotlib` and `networkx`.


* **Crash Fault Injection:** Support for probabilistic crash faults (halting failures) during simulation execution.


* **Modular Design:** Modular architecture for Protocols, Schedulers, and Traffic Generators.

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/Liat-h-technion/Network_Simulation.git
cd Network_Simulation

```


2. **Install dependencies:**
It is recommended to use a virtual environment.
```bash
pip install -r requirements.txt

```



## Usage

The simulation is controlled via `main.py` using command-line arguments.

### Basic Example

Run a simple "Echo" protocol where nodes broadcast messages upon receipt:

```bash
python main.py --protocol echo_all --scheduler random --nodes 10 --max-steps 1000
```

### Running Algorithm 3 (Consensus)

To simulate the Byzantine Consensus algorithm (n=2f+1) described in the paper:

```bash
python main.py --protocol alg3 --scheduler random --nodes 11 --R 20 --display-plots
```

* **Note:** When running `alg3`, the `--R` (rounds per phase) argument is **required**.

### Running with Fault Injection
To simulate a network where nodes crash probabilistically during execution:
```bash
python main.py --protocol alg3 --scheduler random --nodes 21 --R 20 --f 10 --fault-injector probabilistic --fault-prob 0.05
```

* **Note:** When using the probabilistic fault injector, the argument --f is **required**.

### Running the Committee Protocol

To simulate a network with a specific subset of "privileged" nodes:

```bash
python main.py --protocol committee --scheduler random --nodes 20 --committee-size 5

```
**Note:** 
* In this protocol, upon receiving a message, a committee node will broadcast to the entire network, and a regular node will broadcast to committee members only. For example, a committee-size of 1 will create a star topology.
* **Fixed committee**: The committee members are predetermined as the nodes with IDs [0, size-1].

## Configuration & Flags

Below is a detailed list of all available flags in `main.py`:

| Flag | Type | Required | Description                                                                                                                                                                                                                                                      |
| --- | --- | --- |------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--protocol` | `str` | **Yes** | The behavior logic for the nodes. Options: `alg3`, `echo_all`, `random_single_message`, `ping_pong`, `committee`.                                                                                                                                                 |
| `--scheduler` | `str` | **Yes** | The message delivery strategy. Options: `random` (Random Asynchronous Model).                                                                                                                                                                                    |
| `--nodes` | `int` | No | Total number of processes (`n`) in the network. Default: `20`.                                                                                                                                                                                                   |
| `--max-steps` | `int` | No | Stop simulation after this many delivery events. If omitted, runs until no messages remain.                                                                                                                                                                      |
| `--seed` | `int` | No | Seed for the random number generator to ensure reproducibility.                                                                                                                                                                                                  |
| `--analysis-interval` | `int` | No | Step interval to perform heavy network connectivity analysis (e.g., check for strong connectivity). A smaller value will give higher precision, but will slow down the simulation. The analysis is performed until the network forms a strongly-connected graph. |
| `--display-plots` | `flag` | No | If set, displays `matplotlib` charts for delay distributions and topology.                                                                                                                                                                                       |
| `--enable-full-logs` | `flag` | No | If set, prints every single message delivery event to the console. **This flag is not recommended without a small `--max-steps` restriction.**                                                                                                                   |

### Algorithm 3 Specific Flags

| Flag  | Type | Description                                                                            |
|-------| --- |----------------------------------------------------------------------------------------|
| `--R` | `int` | **Required for alg3**. The number of communication rounds per phase.                   |
| `--f` | `int` | The number of faulty nodes tolerated. Default is calculated as `(n-1)//2`. |

### Committee Specific Flags

| Flag | Type | Description |
| --- | --- | --- |
| `--committee-size` | `int` | **Required for committee**. The number of nodes in the committee (IDs `0` to `size-1`). |

### Fault Injection Flags

| Flag | Type    | Description                                                                                                                      |
| --- |---------|----------------------------------------------------------------------------------------------------------------------------------|
| `--fault-injector` | `str`   | Type of fault injection to use. Options: `probabilistic`.                                                                        |
| `--fault-prob` | `float` | Used with `probabilistic` fault injector. The probability (0.0 to 1.0) of a crash fault occurring in a time step. Default: `1.0`. |
| `--f` | `int` | **Required for `probabilistic` fault injector**. The maximum number of faults injected to the network during the simulation.     |


## Implemented Strategies

### Protocols (Node Behavior)

Each protocol defines:
1. Initialization: How the process acts at the beginning of the simulation (generating initial traffic in the network to kickstart the simulation).
2. Incoming message handling: How the process reacts to an incoming message.

The provided protocols are as follows:
* **`alg3` (Algorithm 3):** Implements the protocol for Algorith 3 from the paper *Byzantine Consensus in the Random Asynchronous Model*. Nodes maintain a map of signed values (`v_map`), exchange them over `R` rounds, and advance through phases to reach agreement.

    Initialization: Broadcast the `v_map` with the initial self-signed value `v` to every other node.


* **`echo_all`:** When a node receives a message, it broadcasts a response to everyone else.

    Initialization: Broadcast to every other node.


* **`ping_pong`:** A node replies only to the sender of the received message. 

    Initialization: Broadcast to every other node.


* **`random_single_message`**: Upon receiving a message, sends a new message to a single process chosen randomly with uniform probability.

    Initialization: Broadcast to every other node.


* **`committee`:** Nodes with IDs `0` to `committee_size` broadcast to everyone. Regular nodes only report back to the committee.

    Initialization: Broadcast to every committee member.

### Schedulers

* **`random` (Random Asynchronous):** The core of this research. At every step, the scheduler identifies all active links (pairs of sender->receiver with pending messages) and selects **one link** uniformly at random. The earliest message on that link is delivered.



### Fault Injectors

* **`probabilistic`**: At each simulation step, with probability `p` (`--fault-prob`), kills **one** randomly selected alive process. This continues until a maximum of f faults is reached.


## Project Structure

```
.
├── main.py                         # Entry point: Argument parsing and simulation setup
├── requirements.txt                # Python dependencies
└── simulation/
    ├── analysis.py                 # Network connectivity stats and plotting (Analyzer class)
    ├── framework.py                # Core classes: Message, Network, Process, Simulator
    └── strategies/                 
        ├── protocols.py            # Implementations of Protocol strategies
        ├── schedulers.py           # Implementations of Scheduler strategies
        └── fault_injector.py       # Implementations of Fault Injector strategies
```
