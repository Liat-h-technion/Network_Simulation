# Network Simulation Framework & Random Asynchronous Model

A Python discrete-event simulator designed to analyze distributed algorithms under the **Random Asynchronous Model**.

This project implements the theoretical framework and algorithms described in the paper *Byzantine Consensus in the Random Asynchronous Model*. It allows for the simulation of message passing, network connectivity analysis, and specific consensus protocols (like Algorithm 3) to verify theoretical probabilistic guarantees.

## Features

* **Random Asynchronous Scheduler:** Implements a non-adversarial scheduler where message delivery order is determined by randomly selecting sender-receiver pairs.
In each time-step of the simulation, a ***single*** sender-receiver link is chosen ***with uniform probability*** from the current active links.


* **Consensus Simulation:** Full implementation of **Algorithm 3** (Binary Byzantine Consensus for n=2f+1) from the source paper.


* **Connectivity Analysis:** Mid-simulation tracking of network topology (Weakly/Strongly Connected components) and partition detection, at chosen time intervals.


* **Visualizations:** Histograms of message delays and network topology graphs using `matplotlib` and `networkx`.


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
python main.py --protocol echo_all --scheduler random --initial-traffic all_to_all --nodes 10 --max-steps 1000

```

### Running Algorithm 3 (Consensus)

To simulate the Byzantine Consensus algorithm (n=2f+1) described in the paper:

```bash
python main.py --protocol alg3 --scheduler random --initial-traffic alg3 --nodes 11 --R 20 --display-plots

```

* **Note:** When running `alg3`, the `--R` (rounds per phase) argument is **required**.

### Running the Committee Protocol

To simulate a network with a specific subset of "privileged" nodes:

```bash
python main.py --protocol committee --scheduler random --initial-traffic committee --nodes 20 --committee-size 5

```
**Note:** 
* In this protocol, upon receiving a message, a committee node will broadcast to the entire network, and a regular node will broadcast to committee members only. For example, a committee-size of 1 will create a star topology.
* **Fixed committee**: The committee members are predetermined as the nodes with IDs [0, size-1].

## Configuration & Flags

Below is a detailed list of all available flags in `main.py`:

| Flag | Type | Required | Description                                                                                                                                                                        |
| --- | --- | --- |------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--protocol` | `str` | **Yes** | The behavior logic for the nodes. Options: `alg3`, `echo_all`, `ping_pong`, `committee`.                                                                                           |
| `--scheduler` | `str` | **Yes** | The message delivery strategy. Options: `random` (Random Asynchronous Model).                                                                                                      |
| `--initial-traffic` | `str` | **Yes** | How the simulation creates initial messages. Options: `all_to_all`, `alg3`, `committee`.                                                                                           |
| `--nodes` | `int` | No | Total number of processes (`n`) in the network. Default: `20`.                                                                                                                       |
| `--max-steps` | `int` | No | Stop simulation after this many delivery events. If omitted, runs until no messages remain.                                                                                        |
| `--seed` | `int` | No | Seed for the random number generator to ensure reproducibility.                                                                                                                    |
| `--analysis-interval` | `int` | No | Step interval to perform heavy network connectivity analysis (e.g., check for strong connectivity). A smaller value will give higher precision, but will slow down the simulation. |
| `--display-plots` | `flag` | No | If set, displays `matplotlib` charts for delay distributions and topology.                                                                                                         |
| `--enable-full-logs` | `flag` | No | If set, prints every single message delivery event to the console. **This flag is not recommended without a small `--max-steps` restriction.**                                     |

### Algorithm 3 Specific Flags

| Flag  | Type | Description |
|-------| --- | --- |
| `--R` | `int` | **Required for alg3**. The number of communication rounds per phase. |
| `--f` | `int` | The number of faulty nodes tolerated. Default is calculated as `(n-1)//2`. |

### Committee Specific Flags

| Flag | Type | Description |
| --- | --- | --- |
| `--committee-size` | `int` | **Required for committee**. The number of nodes in the committee (IDs `0` to `size-1`). |

## Implemented Strategies

### Protocols (Node Behavior)

* **`alg3` (Algorithm 3):** Implements the protocol for Algorith 3 from the paper *Byzantine Consensus in the Random Asynchronous Model*. Nodes maintain a map of signed values (`v_map`), exchange them over `R` rounds, and advance through phases to reach agreement.


* **`echo_all`:** When a node receives a message, it broadcasts a response to everyone else.
* **`ping_pong`:** A node replies only to the sender of the received message.
* **`committee`:** Nodes with IDs `0` to `committee_size` broadcast to everyone. Regular nodes only report back to the committee.

### Schedulers

* **`random` (Random Asynchronous):** The core of this research. At every step, the scheduler identifies all active links (pairs of sender->receiver with pending messages) and selects **one link** uniformly at random. The earliest message on that link is delivered.



### Traffic Generators

* **`all_to_all`:** Injects an initial message from every node to every other node.
* **`alg3`:** Initializes nodes with random binary inputs (0 or 1) and broadcasts the initial `v_map` to start the consensus process.
* **`committee`:** Generates traffic either from everyone to the committee OR from the committee to everyone.

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
        └── traffic_generators.py   # Implementations of Traffic Generator strategies
```
