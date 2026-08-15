# Stage 4 & 5 Debugging Log

This is an honest record of every real issue hit while building ORION's
`ros2_control` integration — mock hardware (Stage 4) and the Gazebo backend
(Stage 5) — and how each was actually found and fixed. Kept for two reasons:
some of these will recur on future joints/controllers, and the debugging
*process* here (how to narrow down a silent failure) is reusable even when
the specific bug isn't.

Each entry: **Symptom → Root cause → Fix**, in the order encountered.

---

## Stage 4 — Mock hardware

### 1. `ExpatError: not well-formed (invalid token)` on launch

**Symptom:** `xacro` failed to parse the URDF immediately after adding the
`<ros2_control>` block, even though the block looked syntactically correct.

**Root cause:** `colcon build` copies source files into `install/` at build
time — it does not read `src/` live. The launch file's `xacro.process_file()`
reads from the *installed* copy. The description package hadn't been
rebuilt after the edit, so xacro was parsing a stale/incomplete version of
the file from before the edit finished.

**Fix:** Rebuild with `--symlink-install`, which symlinks `install/` back to
`src/` so edits are picked up without rebuilding for non-compiled files
(URDF, YAML, launch `.py`). This was the single most recurring category of
bug across the whole project — **always rebuild the specific package you
just edited, or use `--symlink-install` from the start.**

### 2. `TypeError: Node.__init__() missing 1 required keyword-only argument: 'executable'`

**Root cause:** Typo in the launch file — `execuitable=` instead of
`executable=` on one `Node(...)` call.

**Fix:** Corrected the spelling. Two more typos were caught in the same
pass while checking: `ros2_contrrol_node` (extra `r`) and
`join_state_broadcaster` (missing `t`) — neither would have crashed
Python, they'd have failed later at runtime with much less obvious errors
("executable not found", "controller not found").

**Lesson:** A `TypeError` on one `Node()` call is a good reason to read
*every* `Node()` call in the file, not just the one that crashed.

### 3. YAML parse error: `Cannot have a value before ros__parameters`

**Root cause:** Three separate typos in `orion_controllers.yaml`:
- `ros_parameters:` instead of `ros__parameters:` (double underscore is a
  fixed ROS 2 keyword, not a name you choose)
- `update_rate: 50 "Hz"` — not valid YAML for an integer; should be
  `update_rate: 50  # Hz` (comment, not part of the value)
- `joint_state_broadcaster/joint_state_broadcaster` instead of
  `joint_state_broadcaster/JointStateBroadcaster` — the part after the
  slash is a C++ class name (CamelCase), not the package name again

**Fix:** Corrected all three. Verified with `cat -A` to reveal invisible
whitespace/tab issues as part of the same pass (none were present here, but
worth checking whenever YAML indentation looks suspicious).

### 4. `invalid tag name 'command_interface'` after adding remaining joints

**Root cause:** Two `<joint>` tags were accidentally self-closed
(`<joint name="...">/>` written as `<joint name="..."/>`), which made XML
treat them as complete elements with no children — so the
`<command_interface>`/`<state_interface>` lines meant to be inside them
ended up floating outside any `<joint>`, which `ros2_control`'s parser
correctly rejected.

**Fix:** Changed `/>` to `>` on the affected joints, with a proper matching
`</joint>` already present further down.

### 5. `rear_left_wheel_joint/velocity is not available`

**Root cause:** The very first joint declared (back in the mock-hardware
step) had been accidentally deleted while editing in the other five joints.
Nothing about the remaining XML looked *wrong* — it just wasn't *complete*,
which is an easy category of mistake to miss on a visual scan.

**Fix:** Re-added the missing `<joint>` block. Lesson: count declared
joints against a checklist before moving on, don't just confirm the visible
XML parses.

### 6. `front_left_steerong_joint/position is not available`

**Root cause:** Typo in `orion_controllers.yaml`'s joint list —
`steerong` instead of `steering`.

**Fix:** Corrected spelling. This one was caught directly from the error
message, which named the exact (misspelled) interface it was looking for.

---

## Stage 5 — Gazebo backend

### 7. `XacroException: invalid syntax` evaluating `'arg use_mock'`

**Root cause:** Used `${arg use_mock}` (curly braces — xacro's Python
*expression* evaluator) instead of `$(arg use_mock)` (parentheses — xacro's
*substitution* syntax). `${...}` tries to execute the contents as Python
code; `arg use_mock` isn't valid Python.

**Fix:** Corrected to parentheses in both the `<xacro:if>` and
`<xacro:unless>` conditions. Caught in the same pass: `GenericSystems`
(extra `s`) instead of `GenericSystem` in the mock plugin name — valid XML,
would have failed at runtime with a pluginlib "class not found" error
instead.

### 8. Controllers load but never activate; spawners retry forever, `controller_manager` node never appears

This was the long one. Multiple false leads before finding the real cause.

**False lead A — plugin path.** `GZ_SIM_SYSTEM_PLUGIN_PATH` was empty, so
Gazebo had no way to find `libgz_ros2_control-system.so` even though it
existed at `/opt/ros/jazzy/lib/`. This **was** a real bug and was fixed
(`SetEnvironmentVariable` added to the launch file), but fixing it alone
did not resolve the underlying issue — `controller_manager` still never
appeared. This taught us the failure was layered: more than one thing was
wrong at once.

**False lead B — URDF→SDF conversion via `ros_gz_sim create -topic`.**
Isolated testing (spawning a hand-written minimal SDF directly with
`gz sim -s -r`) proved the `gz_ros2_control` plugin itself worked
correctly in isolation — it loaded, created a node, exposed
`controller_manager` services. This ruled out "the plugin is broken."
Comparing that against the real pipeline (which spawns via
`ros_gz_sim create -topic robot_description`, converting URDF-over-ROS-topic
to SDF internally) suggested the topic-based conversion path might be
losing the `<ros2_control>` block differently than the command-line
`gz sdf -p` conversion.

**False lead C — XML formatting (minified vs pretty-printed).** Attempting
to route around the topic-based spawn by pre-converting the URDF to SDF
with `gz sdf -p` and spawning from a file instead, the generated `.sdf`
still had a `0` count for the plugin block. Comparing minified
(`.toxml()`) vs pretty-printed (`.toprettyxml()`) output theorized that
`gz sdf -p`'s handling of non-native elements like `<ros2_control>` was
whitespace-sensitive. This was also not the actual cause.

**Actual root cause:** A `diff` between the launch-generated URDF and an
earlier manually-generated one (from the CLI `xacro` tool) revealed the
launch-generated file was missing the entire
`<gazebo><plugin filename="gz_ros2_control-system">...</plugin></gazebo>`
block — not the `<ros2_control>` interface block (which was present and
had been the whole time; `grep -c ros2_control` was a misleading test
because it matches the *substring* inside `GazeboSimROS2ControlPlugin`
too, not just the actual tag). Checking the *installed* copy of
`orion_vehicle.gazebo.xacro` against the *source* copy confirmed it:
`grep -c "gz_ros2_control-system"` returned `0` in `install/` and `1` in
`src/`. **`project_orion_simulation` had never been rebuilt** since the
plugin block was added to it — every `colcon build` command since then had
used `--packages-select project_orion_control` only, silently excluding
the package that actually needed rebuilding.

**Fix:**
```bash
colcon build --symlink-install --packages-select project_orion_simulation project_orion_control
```

**Lesson (the important one):** when editing files across multiple
packages, always rebuild *all* the packages you touched, every time — not
just the one whose launch file you're about to run. This single stale
install was the root cause underneath roughly half of this debugging
session; every other lead was a real, independently-fixed issue, but none
of them were sufficient on their own because this one masked the result.

### 9. `Switch controller timed out after 5 seconds!` on activation

**Symptom:** Controllers loaded, configured, then failed specifically at
the activation step, every time, exactly 5 seconds in.

**Root cause:** Log line right above it:
`Desired controller update period (0.02 s) is slower than the gazebo
simulation period (0 s)`. Gazebo starts **paused** by default — simulation
time isn't advancing. `controller_manager` (`use_sim_time:=true`) waits
for `/clock` to tick through a full control cycle to confirm activation; if
sim time is frozen, that wait never completes.

**Fix:** Added `-r` to Gazebo's launch args (`gz_args`) to start the
simulation running immediately instead of paused.

### 10. Wheels kept spinning after `Ctrl+C`-ing the velocity command publisher

**Not a bug** — `velocity_controllers/JointGroupVelocityController` has no
default behavior to stop on lost command source; it repeats the last
received command every control cycle indefinitely. Stopping the publisher
just means no *new* commands arrive — the controller has no way to know
the publisher is gone.

**Resolution:** Publish an explicit zero-velocity command
(`--once` flag so it sends exactly once and exits) to stop the wheels.
Flagged as a real safety gap worth addressing in a later stage — a command
timeout / watchdog / heartbeat pattern, not something to solve now but
worth not forgetting.

---

## Cross-cutting lessons

- **Rebuild the package you edited. Every time.** Multiple issues in this
  log (#1, and the big one, #8) were purely stale-install problems wearing
  the costume of a different bug.
- **A crash with a clear error is easier than success-looking silence.**
  The hardest bug (#8) never threw an error — everything reported success
  right up until `controller_manager` simply never existed. Isolating with
  `-v 4` verbosity, standalone SDF tests, and direct `grep` checks against
  generated files (not just trusting "it built") was what eventually
  narrowed it down.
- **When two processes/terminals seem to disagree with reality** (e.g. a
  node existing in one check and not another), suspect ROS 2 discovery —
  `ros2 daemon stop && ros2 daemon start`, matching `ROS_DOMAIN_ID`, or in
  one case here, a full reboot — before assuming the code itself is wrong.
- **A passing test after a partial fix might just mean leftover state.**
  The first "success" after the plugin-path fix turned out to be a stale
  `controller_manager` from an earlier run still listening in the
  background, not the new launch actually working. Always retest from a
  fully clean process state (`pkill`, daemon restart) before trusting a
  result.