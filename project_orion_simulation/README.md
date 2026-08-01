# project_orion_simulation

Stage 3 — **Digital Twin Foundation** for Project ORION.

Gazebo-based digital twin: spawns the ORION vehicle into a clean test
world and publishes simulated IMU, 2D LiDAR, and RGB camera data. No
autonomy, control, or ros2_control — publishing only.

## Package Contents

```
project_orion_simulation/
├── package.xml
├── CMakeLists.txt
├── README.md
├── urdf/
│   └── orion_vehicle.gazebo.xacro   # includes project_orion_description's
│                                     # xacro unmodified, adds Gazebo-only tags
├── launch/
│   └── orion_digital_twin.launch.py # starts Gazebo + RSP + spawns vehicle + RViz
├── worlds/
│   └── orion_world.world            # ground plane, sun, physics, camera view
└── config/
    ├── orion_gz_bridge.yaml         # ROS 2 <-> Gazebo topic bridge config
    └── orion_sim_params.yaml        # documented reference defaults
```

## Why the Gazebo tags live here, not in `project_orion_description`

`orion_vehicle.gazebo.xacro` in this package does
`xacro:include $(find project_orion_description)/urdf/orion_vehicle.urdf.xacro`
and layers `<gazebo>` material/friction/contact tags and sensor
definitions on top, by referencing the existing link names
(`base_link`, `*_wheel_link`, `imu_link`, `lidar_link`, `camera_link`).

Consequences of this design:

- **Zero changes to `project_orion_description`.** The Stage 2 milestone
  is untouched; `display.launch.py` and RViz validation continue to work
  exactly as before.
- **Simulator isolation.** If a different simulator were adopted later,
  it would need its own composition file in its own package — not a
  rewrite of the base vehicle description.
- **Trade-off:** the fully assembled sim-ready `robot_description` only
  exists when this package's xacro is processed, not the description
  package's directly.

  ## Simulator Used: Gazebo Sim (`gz sim`), not Gazebo Classic

This milestone targets **Gazebo Sim** (the `gz sim` / Harmonic-generation
simulator, via `ros_gz_sim` and `ros_gz_bridge`), not Gazebo Classic
(`gazebo_ros_pkgs`). This wasn't an arbitrary choice — Gazebo Classic
isn't released for ROS 2 Jazzy at all; `gz sim` is the only
officially-paired simulator for this ROS 2 distribution.

Practical implications of this choice, since most Gazebo tutorials still
assume Classic:

- Sensor `<gazebo>` tags use `type="gpu_lidar"` (not `type="ray"`) and
  have no `<plugin filename="libgazebo_ros_*.so">` block — `gz sim`
  handles sensors via world-level system plugins instead of one plugin
  per sensor.
- ROS 2 topics for sensor data do **not** come directly from the sensor
  tags. Sensor data publishes on Gazebo's own transport layer first;
  `ros_gz_bridge` (config in `config/orion_gz_bridge.yaml`) translates
  each topic into ROS 2.
- The world file needs explicit `<plugin>` entries at the world level
  (physics, sensors, IMU, scene broadcaster, user commands) — Classic
  loads these implicitly, `gz sim` does not.

  ## Building

```bash
cd ~/ros2_ws
colcon build --packages-select project_orion_description project_orion_simulation
source install/setup.bash
```

Requires `ros_gz_sim`, `ros_gz_bridge`, `robot_state_publisher`,
`joint_state_publisher`, and `rviz2` installed (all standard for a
ROS 2 Jazzy desktop install alongside `gz sim`).

## Launching

One command starts the complete digital twin — Gazebo, the vehicle
spawned, `robot_state_publisher`, `joint_state_publisher`, the ROS 2
bridge, and RViz, all together:

```bash
ros2 launch project_orion_simulation orion_digital_twin.launch.py
```

RViz opens by default (`use_rviz` defaults to `true`). To run headless
(Gazebo server + all ROS nodes, no GUIs) — useful on a loaded machine,
or when you don't need to look at anything, just want the topics running:

```bash
ros2 launch project_orion_simulation orion_digital_twin.launch.py use_rviz:=false
```

**Important:** click the ▶ play button in the bottom-left of the Gazebo
window if the simulation appears frozen — Gazebo Sim starts **paused**
by default. Nothing publishes sensor data or moves physics forward
until you press play.

## Published ROS 2 Topics

Bridged from Gazebo via `config/orion_gz_bridge.yaml`:

| Topic | Type | Notes |
|---|---|---|
| `/clock` | `rosgraph_msgs/msg/Clock` | Required for `use_sim_time` to work on any node |
| `/orion/imu/data` | `sensor_msgs/msg/Imu` | ~100 Hz target (actual rate depends on host CPU) |
| `/orion/scan` | `sensor_msgs/msg/LaserScan` | ~10 Hz target, 360 beams, 0.12-12.0m range |
| `/orion/camera/image_raw` | `sensor_msgs/msg/Image` | ~30 Hz target, 640x480 RGB |
| `/orion/camera/camera_info` | `sensor_msgs/msg/CameraInfo` | Calibration data, computed from FOV/resolution |

Published directly by ROS 2 nodes (not bridged):

| Topic | Type | Source |
|---|---|---|
| `/robot_description` | `std_msgs/msg/String` | `robot_state_publisher` |
| `/joint_states` | `sensor_msgs/msg/JointState` | `joint_state_publisher` (default zero-position; no motion yet) |
| `/tf` | `tf2_msgs/msg/TFMessage` | `robot_state_publisher`, non-fixed joints |
| `/tf_static` | `tf2_msgs/msg/TFMessage` | `robot_state_publisher`, fixed joints |

**Known quirk:** `sensor_msgs/msg/Imu`'s `orientation_covariance` and
`angular_velocity_covariance` fields are always zero. In ROS 2
convention all-zero covariance normally signals "data unavailable," but
the orientation/angular velocity data itself is real and correct — this
is a known limitation of Gazebo Sim's IMU plugin, not a bug in this
package.


## Known Limitations

- **No vehicle motion.** No `ros2_control`, no drive/steering
  controller, no `cmd_vel` interface. `joint_state_publisher` publishes
  default zero positions for all 6 non-fixed joints so the TF tree is
  complete, but nothing commands them. Deliberate Stage 3 scope.

- **Significant CPU headroom required.** Running Gazebo (server +
  GUI rendering), RViz (its own rendering), the ROS 2/Gazebo bridge,
  `robot_state_publisher`, and `joint_state_publisher` simultaneously is
  genuinely CPU-intensive. On a loaded machine (e.g. running other heavy
  software alongside), `joint_state_publisher`'s sim-time-driven publish
  timer can get starved of CPU time and silently stop producing
  `/joint_states` messages — no error is thrown, the node stays alive,
  the topic still technically exists, it just stops updating. Symptoms:
  RViz's RobotModel display shows red "No transform" errors for the
  wheel/steering links; `ros2 topic hz /joint_states` hangs with no
  output. Fix: close other heavy processes, or launch with
  `use_rviz:=false` to shed the RViz rendering load. This is a resource
  constraint, not a bug in this package — confirmed by running the same
  stack headless (`gz sim -s -r ...`), which publishes cleanly.

- **Achieved sensor rates are lower than configured targets** under
  normal load: IMU configured for 100Hz typically achieves ~65-70Hz,
  LiDAR configured for 10Hz achieves ~7Hz. This scales with
  `real_time_factor` (observed ~0.84 on the reference dev machine, i.e.
  simulation runs slightly slower than real time) and host CPU
  availability. Not a bug — the sensor plugins publish once per
  simulated update, and simulated time itself was running below 1.0
  real-time factor under normal load.

- **`/tf_static` vs `/tf` deliver differently to late-joining
  subscribers.** Fixed-joint frames (`camera_link`, `imu_link`,
  `lidar_link`) publish on the latched `/tf_static` topic and are
  immediately available to any new subscriber. Non-fixed joint frames
  (wheels, steering) publish on plain `/tf` and are only delivered to
  subscribers actively listening at publish time. A slow-starting
  subscriber (e.g. RViz launched simultaneously with everything else on
  a loaded machine) can appear to permanently miss these until a fresh
  restart — in practice this compounds with the CPU-starvation issue
  above rather than being a separate root cause.

- **Wheel/ground contact parameters (`mu1`, `mu2`, `kp`, `kd`) are
  engineering defaults, not measured data.** No physical hardware
  exists yet, so these were chosen for stable, plausible behavior at
  this vehicle's scale rather than derived from real tire/actuator data.

- **Fixed-joint sensor links get lumped in the generated SDF.**
  Gazebo's URDF-to-SDF conversion merges `imu_link`, `lidar_link`, and
  `camera_link` into `base_footprint` in the physics/rendering
  representation (visible as `base_footprint_fixed_joint_lump__*_link`
  names in `gz model --list` / pose topics). Sensor behavior is
  unaffected — the `<sensor>` tag carries its own pose offset — but the
  naming is worth knowing if inspecting the running world directly.

- **World is intentionally empty** beyond a ground plane — no track, no
  obstacles. Matches this milestone's explicit scope; also means
  LiDAR scans read `.inf` (no obstacles in range) and the camera image
  is two flat color bands (ground + sky) by default. Both confirmed
  correct behavior for this world, not sensor faults.

- **Gazebo Sim, not Classic** — see "Simulator Used" above. Correct for
  this ROS 2 distribution, but worth knowing if referencing Gazebo
  tutorials/documentation elsewhere, most of which still assume Classic.

  ## Validation Summary

All checks below were performed against the actual running simulation,
not assumed:

- ✅ **Vehicle spawns successfully** — confirmed via `gz model --list`
  and visually in the Gazebo GUI, resting on the ground plane at its
  natural settled height (~0.08m, wheel-radius-limited, down from the
  0.15m spawn height).
- ✅ **TF tree is correct and complete** — all 11 frames present via
  `ros2 run tf2_tools view_frames` (`base_footprint`, `base_link`, 4
  wheels, 2 steering links, `imu_link`, `lidar_link`, `camera_link`),
  matching the Stage 2 structure.
- ✅ **Physics is stable** — vehicle pose compared bit-for-bit identical
  across a 40-real-second (~34 sim-second) idle window; no drift, no
  sinking, no jitter.
- ✅ **All 3 sensors publish real, physically plausible data**: IMU
  reports `linear_acceleration.z ≈ 9.8` (gravity) at rest; LiDAR reports
  correct `.inf` ranges for the current empty world; camera reports
  correctly-computed intrinsics (`k[0] ≈ 381.46`, matching the
  configured FOV/resolution) and a coherent (if plain) rendered image.
- ✅ **RViz and Gazebo run together** — RobotModel, TF, and the full
  mesh render correctly when the host machine has adequate CPU headroom
  (see Known Limitations).
- ✅ **Stage 2 remains unaffected** — `project_orion_description` was
  not modified; its own `display.launch.py` continues to work
  independently of this package.

  ## Recommended Next Milestone

**`ros2_control` + a minimal Ackermann drive/steering controller**, so
the vehicle can move under commanded velocity/steering in simulation.
Stage 2 already built (but deliberately left unpowered) the steering
joint chain; Stage 3 has now made all 6 wheel/steering joints physically
simulated with real contact/friction and a complete, verified TF/sensor
pipeline. Control is the one remaining piece needed before perception or
planning (SLAM, Nav2) would have anything meaningful to act on.
Recommend scoping it to open-loop command tracking only — no planner, no
perception — continuing the "one milestone, one clear capability"
pattern this project has followed so far.