# Project ORION — ROS 2 Foundation

This section documents the current implemented milestone: the ORION ROS 2
Foundation and System State Manager. For the full project vision, philosophy,
and long-term roadmap, see below.

## Packages

- **`project_orion`** — Python (ament_python) package containing the system
  state manager node, state monitor node, launch file, and tests.
- **`project_orion_interfaces`** — C++ (ament_cmake) package containing the
  custom message and service definitions used for state communication.

## Architecture

- `orion_state_machine.py` — pure Python, no ROS 2 dependency, defines the
  8 ORION system states and the legal transitions between them. Fully unit
  tested in isolation.
- `state_manager_node.py` — wraps the state machine in a ROS 2 node. Exposes
  the `/orion/request_state_transition` service (other nodes request state
  changes; the manager validates and accepts/rejects them) and publishes the
  current state on `/orion/system_state` whenever it changes.
- `state_monitor_node.py` — a minimal, independent node that subscribes to
  `/orion/system_state` and logs updates, demonstrating that other nodes can
  observe ORION's state without any knowledge of the state manager's internals.
- `orion_foundation.launch.py` — starts both nodes together.
### System States

```text
OFF, BOOTING, INITIALIZING, READY, MISSION, EMERGENCY, RECOVERY, SHUTDOWN
```

### Legal Transitions

```text
OFF -> BOOTING
BOOTING -> INITIALIZING, EMERGENCY
INITIALIZING -> READY, EMERGENCY
READY -> MISSION, SHUTDOWN, EMERGENCY
MISSION -> READY, EMERGENCY, RECOVERY
EMERGENCY -> RECOVERY, SHUTDOWN
RECOVERY -> READY, EMERGENCY, SHUTDOWN
SHUTDOWN -> OFF
```

EMERGENCY is reachable from nearly any active state, but can only be exited
through RECOVERY or SHUTDOWN — never directly back into MISSION — enforcing a
deliberate recovery step before resuming a mission after a fault.
## Architectural Decisions

- **State transitions are externally requested (service-based), not
  internally auto-advanced.** Other nodes (or an operator) call
  `/orion/request_state_transition`; the manager only changes state on a
  valid request. Internally-driven auto-transitions (e.g. auto-advancing
  through boot stages) are a planned future addition on top of this.
- **State constants are duplicated as plain integers** across
  `orion_state_machine.py`, `OrionState.msg`, and
  `RequestStateTransition.srv`, rather than sharing a single generated
  source. This was a deliberate simplicity tradeoff for this milestone: the
  three definitions must be kept in sync manually if a state is ever added,
  renamed, or renumbered.
- **State machine logic is kept ROS 2-free** so it can be unit tested
  directly with pytest, without spinning up any ROS 2 node or middleware.

## Building

From a clean clone:

```bash
cd ~/ros2_ws
colcon build --packages-select project_orion_interfaces project_orion
source install/setup.bash
```

## Running

**Option A — launch both nodes together:**

```bash
ros2 launch project_orion orion_foundation.launch.py
```

**Option B — run nodes individually (separate terminals, each sourced):**

```bash
ros2 run project_orion state_manager_node
ros2 run project_orion state_monitor_node
```

**Requesting a state transition** (from any sourced terminal, while the
manager is running):

```bash
ros2 service call /orion/request_state_transition \
  project_orion_interfaces/srv/RequestStateTransition "{requested_state: 1}"
```

State values: `OFF=0, BOOTING=1, INITIALIZING=2, READY=3, MISSION=4,
EMERGENCY=5, RECOVERY=6, SHUTDOWN=7`

## Testing

```bash
cd src/project_orion/project_orion
python3 -m pytest test/test_orion_state_machine.py -v
```

---

# Project ORION (Full Vision)

*(existing vision document content continues below unchanged)*
# Project ORION

### Engineering the Future of Intelligent Autonomous Systems

> **A modular, research-driven platform for designing, simulating, validating, and deploying intelligent autonomous systems.**

---

## 🚀 Overview

**Project ORION** is a long-term autonomous systems engineering initiative focused on the design and development of intelligent robotic systems through a rigorous, simulation-first and research-driven methodology.

ORION is not intended to be a single autonomous vehicle or a one-off robotics project. It is conceived as a **modular research and engineering platform** where perception, localization, mapping, planning, control, artificial intelligence, embedded systems, and autonomous decision-making can be developed, evaluated, and continuously improved within a unified ecosystem.

The first physical implementation of ORION will be a **research-oriented autonomous racing vehicle**. The racing platform will serve as a demanding experimental testbed for investigating autonomous driving technologies, where high-speed perception, real-time decision-making, localization, motion planning, and vehicle control must operate together reliably.

The project will follow a deliberate progression:

**Concept → Requirements → Architecture → Simulation → Validation → Hardware → Real-World Deployment**

The ultimate goal is to bridge the gap between theoretical research, robotics simulation, and physical autonomous systems.

---

## 🎯 Vision

> **To establish Project ORION as an open, modular, and research-grade autonomous systems platform that accelerates innovation in intelligent robotics through rigorous engineering, simulation-first development, and seamless transition from virtual environments to real-world deployment.**

---

## 🧭 Mission

The mission of Project ORION is to:

* Design modular architectures for intelligent autonomous systems.
* Develop and evaluate perception, localization, mapping, planning, and control technologies.
* Use simulation as a primary environment for safe experimentation and rapid iteration.
* Bridge simulated robotics systems with real-world hardware.
* Establish reproducible engineering and research practices.
* Benchmark alternative algorithms and system configurations using measurable performance criteria.
* Create an extensible platform that can support future autonomous systems research beyond the initial racing vehicle.

---

## 🔬 Why ORION?

Autonomous systems combine several complex disciplines, including robotics, artificial intelligence, computer vision, embedded systems, control engineering, sensor fusion, and real-time computing.

However, these disciplines are often developed and studied independently.

Project ORION seeks to bring them together within a single, continuously evolving engineering platform.

The project is driven by a simple principle:

> **Autonomous systems should be engineered as complete systems, not assembled as disconnected components.**

ORION therefore emphasizes:

* Systems engineering before implementation.
* Clear requirements before architecture.
* Architecture before coding.
* Simulation before physical deployment.
* Measurement before optimization.
* Documentation throughout development.
* Continuous iteration based on evidence.

---

## 🏎️ The First ORION Platform: Autonomous Racing

The first implementation of ORION is an autonomous racing vehicle.

Racing provides a challenging and controlled environment for autonomous systems research. The platform must operate under demanding conditions involving:

* High-speed perception.
* Real-time localization.
* Accurate mapping.
* Low-latency planning.
* Dynamic obstacle handling.
* Precise trajectory tracking.
* Real-time control.
* Computational constraints.
* Sensor uncertainty.
* System failures and recovery.

The racing platform is therefore not the final objective of ORION.

It is the **first research testbed** through which the ORION architecture will be developed and validated.

---

## 🧠 Core Research Areas

ORION is designed to support research and experimentation across multiple autonomous systems domains.

### Perception

Understanding the environment using cameras, LiDAR, and other sensors.

### Localization

Estimating the vehicle's position and orientation within its environment.

### Mapping and SLAM

Building and maintaining spatial representations of unknown environments.

### Sensor Fusion

Combining information from multiple sensors to improve state estimation and environmental understanding.

### Motion Planning

Generating safe and efficient paths and trajectories.

### Vehicle Control

Executing planned trajectories through steering, speed, and motion control.

### Autonomous Decision-Making

Selecting actions based on mission objectives, environmental conditions, uncertainty, and system state.

### Adaptive Autonomy

Investigating how autonomous systems can respond to changing environments, uncertainty, and component degradation.

### System Health and Diagnostics

Monitoring the health of sensors, computation, power, and vehicle subsystems.

### Digital Twins

Maintaining a high-fidelity simulation environment that mirrors the physical platform and supports rapid experimentation.

---

## 🏗️ Engineering Philosophy

ORION follows a set of principles that guide the development of the entire platform.

### 1. Design Before Implementation

We define the problem, requirements, and architecture before writing substantial code.

### 2. Simulation Before Hardware

Simulation provides a safe and efficient environment for experimentation, failure, and iteration before physical deployment.

### 3. Evidence Over Assumptions

Engineering decisions should be supported by measurements, experiments, benchmarks, or documented reasoning.

### 4. Modularity Over Shortcuts

Subsystems should be replaceable and independently testable wherever practical.

### 5. Documentation Is Engineering

Design decisions, experiments, failures, and lessons learned are part of the engineering process and should be documented.

### 6. Benchmark Before Optimization

Performance improvements should be demonstrated through measurable evaluation rather than subjective observation.

### 7. Build for Evolution

The architecture should support future research and new robotic platforms without requiring complete redesign.

### 8. Safety Is a First-Class Requirement

Safety mechanisms, failure detection, and controlled system behavior are considered from the beginning rather than added at the end.

---

## 🔄 Development Methodology

ORION follows an iterative engineering cycle:

```text
Question
   ↓
Research
   ↓
Discuss
   ↓
Challenge
   ↓
Design
   ↓
Review
   ↓
Iterate
   ↓
Validate
   ↓
Document
   ↓
Build
   ↓
Test
   ↓
Improve
   ↓
Repeat
```

The project is organized around formal **Design Reviews (DRs)** that provide checkpoints before major development stages.

---

## 🧩 Development Roadmap

### Phase 0 — Genesis

**Project Foundation**

* Project vision
* Mission
* Project charter
* Engineering principles
* Research philosophy

**Status:** 🟢 In Progress

---

### Phase 1 — Systems Engineering

**Requirements and Architecture**

* System requirements
* Operational concept
* Functional architecture
* Information architecture
* Physical architecture
* Interface definitions
* Requirements traceability

**Status:** 🟡 In Progress

---

### Phase 2 — Software Architecture

**ROS 2 Foundation**

* ROS 2 workspace
* Core package structure
* System state management
* Diagnostics
* Interfaces and messages
* Launch architecture
* Configuration management

**Status:** ⚪ Planned

---

### Phase 3 — Digital Twin

**Simulation Environment**

* Vehicle model
* Sensor simulation
* Gazebo environment
* ROS 2 integration
* RViz visualization
* Vehicle dynamics

**Status:** ⚪ Planned

---

### Phase 4 — Autonomous Navigation

**Core Autonomy**

* Localization
* SLAM
* Mapping
* Perception
* Sensor fusion
* Navigation
* Motion planning

**Status:** ⚪ Planned

---

### Phase 5 — Intelligent Driving

**Decision and Control**

* Trajectory generation
* Vehicle control
* Adaptive control
* Behavioral planning
* Risk-aware decision-making
* AI-assisted autonomy

**Status:** ⚪ Planned

---

### Phase 6 — Hardware

**Physical ORION Vehicle**

* Mechanical design
* Electrical architecture
* Compute platform
* Sensors
* Actuators
* Power system
* Embedded interfaces

**Status:** ⚪ Planned

---

### Phase 7 — Simulation-to-Reality

**Hardware Integration**

* ROS 2 deployment
* Sensor integration
* Hardware-in-the-loop testing
* Real-world localization
* Physical navigation
* Autonomous driving

**Status:** ⚪ Planned

---

### Phase 8 — Research Platform

**Advanced Experiments**

* Algorithm benchmarking
* Failure analysis
* Adaptive autonomy
* Multi-agent systems
* Advanced perception
* Intelligent decision-making
* Research publications

**Status:** ⚪ Planned

---

## 🛠️ Technology Stack

The technology stack will evolve throughout the project.

The current planned ecosystem includes:

* **ROS 2** — Robotics middleware and distributed system architecture
* **Gazebo** — Physics-based simulation and digital twin development
* **RViz2** — Visualization and system debugging
* **SLAM** — Mapping and localization
* **Nav2** — Autonomous navigation framework
* **C++** — High-performance robotics components
* **Python** — AI, experimentation, tooling, and rapid prototyping
* **OpenCV** — Computer vision
* **Linux / Ubuntu** — Development and deployment environment
* **Git / GitHub** — Version control and collaborative development

Technology selections will be evaluated through documented engineering decisions rather than adopted solely because of popularity.

---

## 📊 Research and Evaluation

ORION is intended to be a measurable research platform.

System performance will be evaluated using metrics such as:

* Localization accuracy.
* Mapping quality.
* Path tracking error.
* Lap completion rate.
* Average and maximum speed.
* Planning latency.
* Control response.
* Computational resource utilization.
* Sensor reliability.
* System recovery performance.
* Mission success rate.

Where possible, alternative algorithms and configurations will be evaluated experimentally.

---

## 🧪 Research Questions

The ORION research program will evolve over time.

Initial research questions may include:

* How can autonomous racing platforms balance navigation accuracy, computational cost, and real-time performance?
* Which localization approaches provide the best robustness under constrained onboard computing?
* How can perception uncertainty be incorporated into motion planning?
* How should autonomous vehicles respond to degraded or failing sensors?
* Can autonomous systems dynamically adapt their planning and control strategies based on environmental uncertainty?
* How can simulation-based development be transferred reliably to physical autonomous vehicles?

These questions will be refined as the platform develops.

---

## 📁 Repository Structure

```text
project_orion/
│
├── README.md
├── CHANGELOG.md
├── PROJECT_STATUS.md
├── LICENSE
├── .gitignore
│
├── docs/
│   ├── 00_Project_Foundation/
│   ├── 01_Requirements/
│   ├── 02_Architecture/
│   ├── 03_Research/
│   ├── 04_Simulation/
│   ├── 05_Hardware/
│   ├── 06_Software/
│   ├── 07_Testing/
│   ├── 08_Experiments/
│   └── ADR/
│
├── software/
│
├── simulation/
│
├── hardware/
│
├── experiments/
│
├── media/
│
└── papers/
```

The repository structure will evolve alongside the project.

---

## 📌 Current Status

**Development Stage:** Design Review 1 — Systems Engineering

**Current Focus:**

* Project definition.
* Requirements engineering.
* System architecture.
* Operational concept.
* ROS 2 software architecture planning.

**Next Milestone:**

> Complete the ORION System Definition and Architecture Specification before beginning full-scale implementation.

---

## 🌟 Long-Term Vision

The autonomous racing vehicle is only the beginning.

ORION is intended to evolve into a broader autonomous systems research platform capable of supporting future robotic applications and experimental platforms.

Potential future directions include:

* Autonomous ground vehicles.
* Intelligent mobile robots.
* Multi-agent autonomous systems.
* Cooperative robotics.
* Adaptive autonomous systems.
* Advanced perception and decision-making.
* Digital twin research.
* Autonomous systems education.

The underlying philosophy remains constant:

> **Design. Simulate. Validate. Deploy. Iterate.**

---

## 🚧 Project Status

ORION is currently under active development.

The project is being developed incrementally, with system architecture and requirements being established before major implementation.

This repository documents the evolution of the platform from its initial concept through simulation, hardware development, and real-world validation.

---

## 👨‍💻 Development

Project ORION is being developed as a long-term engineering and research initiative.

Contributions, discussions, research collaboration, and technical feedback will be welcomed as the platform matures.

---

## 📜 License

License information will be finalized as the project architecture and contribution model mature.

---

> **Project ORION**
>
> *Engineering the Future of Intelligent Autonomous Systems.*
