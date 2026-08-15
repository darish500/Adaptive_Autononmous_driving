# ADR-004: Hardware Abstraction via ros2_control (Not a Custom HAL)

**Status:** Accepted
**Date:** 2026-08
**Stages covered:** Stage 4 (mock hardware), Stage 5 (Gazebo backend)

## Context

Early in this project a custom "Vehicle Interface Layer" was proposed — a
hand-rolled `VehicleCommand`/`VehicleStatus` message pair with separate
`simulation_driver` and `hardware_driver` nodes, sitting between the planner
and whatever actually moves the robot. The stated goal was sound: the planner
should never need to know or care whether it's talking to Gazebo or a real
vehicle.

Before implementing that, we reviewed the proposal against what ROS 2 already
provides. `ros2_control` exists specifically to solve this problem. Building a
custom layer on top of it would have meant maintaining two hardware
abstractions doing the same job, and diverging from message types
(`ackermann_msgs`, `JointState`) that the rest of the ROS 2 ecosystem — RViz,
`ros2_controllers`, third-party planners — already expects.

## Decision

Use `ros2_control` as ORION's hardware abstraction layer. The
`<ros2_control>` block in the URDF declares command/state interfaces per
joint; the `<hardware><plugin>` line inside it is the only thing that changes
between backends:

| Backend  | Plugin                          | Status |
|----------|----------------------------------|--------|
| Mock     | `mock_components/GenericSystem`  | Done — Stage 4 |
| Gazebo   | `gz_ros2_control/GazeboSimSystem`| Done — Stage 5 |
| Hardware | (future, e.g. a CAN/serial plugin)| Not started |

A single `use_mock` xacro argument selects between them via
`<xacro:if>`/`<xacro:unless>`. No other part of the URDF, controller config,
or higher-level software changes when the backend changes.

## Consequences

**What we get:**
- One set of joint/interface declarations serves all three backends
- Standard ROS 2 controllers (`joint_state_broadcaster`,
  `velocity_controllers/JointGroupVelocityController`,
  `position_controllers/JointGroupPositionController`) — no custom message
  types to maintain
- A real, working proof that the abstraction holds: the *identical*
  `orion_controllers.yaml` drives both the mock backend and the Gazebo
  backend without modification

**What it cost:**
- `gz_ros2_control` integration was significantly harder to debug than a
  custom Python node would have been, precisely because it's a compiled
  plugin loaded by Gazebo's own systems rather than a ROS node we launch and
  can `print()`-debug directly. See `STAGE5-DEBUGGING-LOG.md` for the full
  account — several failure modes were silent by default and required
  deliberately increasing verbosity or bypassing layers of the pipeline to
  see what was actually happening.

## Alternatives considered

**Custom `VehicleCommand`/`VehicleStatus` HAL** (the original proposal) —
rejected. Would have required maintaining custom message definitions, a
hand-written driver node per backend, and translation layers to interoperate
with anything else in the ROS 2 ecosystem, for no capability `ros2_control`
doesn't already provide.

## Related

- ADR-001: Simulation-first methodology
- ADR-002: Gazebo Harmonic selection
- ADR-003 (superseded by this document): original custom-HAL proposal
- `STAGE5-DEBUGGING-LOG.md`: full account of the Stage 5 integration issues
- `PHYSICS-AND-MATH-REFERENCE.md`: explanation of the numeric values used in
  the URDF (inertia tensors, contact parameters, joint limits)