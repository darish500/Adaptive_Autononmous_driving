# Physics & Math Reference

Explanations for every formula and numeric parameter used in ORION's URDF
and Gazebo configuration — so the numbers mean something instead of being
copied blind.

---

## 1. Inertia tensors

Every `<link>` with mass needs an `<inertial>` block describing how that
mass is distributed in space — this is what makes physics simulation (and
eventually motor torque requirements) meaningful. The tensor has six
independent values:

```xml
<inertia ixx="..." iyy="..." izz="..." ixy="0" ixz="0" iyz="0"/>
```

`ixx`, `iyy`, `izz` are the moments of inertia about the x, y, z axes
through the link's center of mass — resistance to rotational acceleration
about each axis. `ixy`, `ixz`, `iyz` are products of inertia — they're
zero here because every shape in ORION (box, cylinder) is symmetric about
its own local axes, so there's no coupling between rotation axes.

### Box (the chassis, `base_link`)

For a solid rectangular box of mass `m`, width `w` (x), depth `d` (y),
height `h` (z), rotating about its center:

```
ixx = (1/12) * m * (d² + h²)
iyy = (1/12) * m * (w² + h²)
izz = (1/12) * m * (w² + d²)
```

In the xacro:
```xml
ixx="${(1/12) * chassis_mass * (chassis_width*chassis_width + chassis_height*chassis_height)}"
iyy="${(1/12) * chassis_mass * (chassis_length*chassis_length + chassis_height*chassis_height)}"
izz="${(1/12) * chassis_mass * (chassis_length*chassis_length + chassis_width*chassis_width)}"
```

This is the standard closed-form solution for a uniform-density rectangular
prism (derivable from the moment-of-inertia integral
`I = ∫(r²) dm`, integrated over the box's volume) — not something to
derive from scratch each time, just the correct formula for this specific
shape.

### Cylinder (wheels, lidar mount)

For a solid cylinder of mass `m`, radius `r`, length `L`, with its axis
along one of the local axes (wheels rotate about the y-axis here, per
`<axis xyz="0 1 0"/>` on the wheel joints):

```
izz (about the cylinder's own axis) = (1/2) * m * r²
ixx = iyy (about axes perpendicular to the cylinder's axis)
    = (1/12) * m * (3r² + L²)
```

In the xacro (note: here the cylinder is rotated 90° via
`rpy="${pi/2} 0 0"` so its axis lines up with the joint's rotation axis —
the formula assignment to `ixx`/`iyy`/`izz` follows that orientation):
```xml
ixx="${(1/12) * wheel_mass * (3*wheel_radius*wheel_radius + wheel_width*wheel_width)}"
iyy="${(1/12) * wheel_mass * (3*wheel_radius*wheel_radius + wheel_width*wheel_width)}"
izz="${0.5 * wheel_mass * wheel_radius * wheel_radius}"
```

The `(1/2)mr²` term is the same formula used for any spinning disk/wheel/
flywheel — it's why flywheels are shaped the way they are (mass
concentrated far from the axis increases `r²`'s contribution, increasing
angular momentum storage for the same mass).

### Small sensor links (IMU, camera)

These use placeholder values (`0.0001` for all three) rather than computed
ones, since their mass (`0.01`–`0.05` kg) is negligible relative to the
chassis and their exact inertial contribution doesn't meaningfully affect
overall vehicle dynamics. This is a common, deliberate simplification —
not every link needs a precisely derived tensor, just a non-zero one (a
zero inertia tensor can make physics engines behave unpredictably or
refuse to simulate the link at all).

---

## 2. Vehicle geometry

```xml
<xacro:property name="wheelbase" value="0.45"/>
<xacro:property name="track_width" value="0.32"/>
```

**Wheelbase** — distance between front and rear axles, measured along the
vehicle's length (x-axis). Used to place wheels fore/aft:
```xml
xyz="${-wheelbase/2} ${track_width/2} ${-ground_clearance}"   <!-- rear -->
xyz="${wheelbase/2} ${track_width/2} ${-ground_clearance}"    <!-- front -->
```
Half the wheelbase forward and backward from `base_link`'s origin, which
sits at the vehicle's geometric center.

**Track width** — distance between left and right wheels on the same
axle (y-axis). Same halving pattern for left (`+track_width/2`) vs right
(`-track_width/2`).

These two numbers are what a future Ackermann steering controller will
need to compute correct per-wheel steering angles during a turn (the
inside wheel needs a sharper angle than the outside wheel — the math for
that, when we get to it, is entirely a function of wheelbase, track width,
and turn radius).

**Ground clearance** — set equal to `wheel_radius`, since that's the
minimum clearance for the wheel to touch the ground without the chassis
intersecting it:
```xml
<xacro:property name="ground_clearance" value="${wheel_radius}"/>
```

---

## 3. Gazebo contact/friction parameters

```xml
<gazebo reference="front_left_wheel_link">
  <mu1>1.2</mu1>
  <mu2>1.2</mu2>
  <kp>1e6</kp>
  <kd>1.0</kd>
  <minDepth>0.001</minDepth>
  <maxVel>1.0</maxVel>
</gazebo>
```

**`mu1`/`mu2`** — Coulomb friction coefficients along the two principal
friction directions of the contact surface (`mu1` = primary direction,
`mu2` = secondary/orthogonal direction). Higher values = more grip, less
sliding. Wheels use `1.2` (high grip, since wheels shouldn't slide under
normal driving); the chassis body (`base_link`, in case it ever contacts
the ground) uses a lower `0.3`; steering links use `0.1` (low friction is
appropriate for a joint's swivel point, not a driving surface).

**`kp`/`kd`** — contact stiffness and damping, from the same
spring-damper model used in general rigid-body contact simulation:
```
contact_force = kp * penetration_depth + kd * penetration_velocity
```
`kp` (`1e6`) is the "spring constant" — how hard the surfaces push apart
when they overlap. `kd` (`1.0`) damps oscillation from that push. These
values aren't derived from a formula here — they're standard starting
points from Gazebo's own model examples, tuned by trial and error
(too-low `kp` lets objects sink into the ground; too-high `kp` causes
jittery, unstable contacts).

**`minDepth`**/**`maxVel`** — solver tolerances: `minDepth` is the
penetration depth allowed before the contact is enforced at full
strength (a small allowed overlap improves solver stability); `maxVel` caps
the correction velocity used to push overlapping surfaces apart, preventing
physics-engine "explosions" when two shapes briefly interpenetrate.

---

## 4. Joint limits

```xml
<limit lower="-0.6" upper="0.6" effort="10" velocity="2"/>
```
On the steering joints. `lower`/`upper` are in radians — `±0.6 rad ≈
±34.4°`, a reasonable maximum steering angle for a small ground vehicle.
`effort` (10, in N·m for a revolute joint) and `velocity` (2 rad/s) are
placeholder actuator limits — the maximum torque and angular speed the
(currently notional) steering motor could apply, used by the physics
engine to prevent Gazebo from letting an actuator apply infinite
force/speed. These will need real values once actual actuator hardware is
selected.

---

## 5. `ros2_control` update rate

```yaml
controller_manager:
  ros__parameters:
    update_rate: 50  # Hz
```

How often `controller_manager` reads state interfaces and writes command
interfaces — a 50 Hz control loop, i.e. one cycle every 20 ms. This is a
fairly standard rate for non-time-critical mobile robot control (fast
enough for smooth velocity/position tracking, well below what would
require true real-time scheduling guarantees). It's also why Gazebo's
`-r` flag (start simulation running, not paused) mattered in Stage 5 —
`controller_manager`'s activation step needs the simulation clock to
actually advance through at least one 20 ms window to confirm the
control loop is functioning.