# Simulator and SDK coordinate frames

The simulator uses a right-handed **Y-up** world: floor **XZ**, height **+Y**.
Core poses and the Three.js viewport share this frame. Yaw is about +Y;
zero faces +X and positive yaw turns toward -Z.

The warehouse topic contract remains ROS-compatible. All SDKs (Rust, C,
C++, Python, TypeScript, and web) carry the same protobuf fields unchanged;
the middleware does not infer or rotate coordinate frames.

| Quantity | Simulator / layout | Warehouse topics |
|----------|--------------------|------------------|
| Floor position | `x_m`, `z_m` | `pose.position.x = x_m`, `pose.position.y = -z_m` |
| Height | +Y | +Z; warehouse odom reports zero height |
| Yaw | About +Y | Quaternion about +Z, same yaw angle |
| Forward command | `linear_mps` | `Twist.linear.x` (m/s) |
| Turn command | `angular_rps` | `Twist.angular.z` (rad/s) |
| Laser beams | Right / front / left | `ranges[0]` / `[1]` / `[2]` |

For example, simulator `(x_m=4.25, z_m=-3)` becomes odom
`(x=4.25, y=3, z=0)`. Positive yaw is a left turn in both views.
The inverse floor mapping is `z_m = -odom.pose.position.y`.
Do not rename message fields to match the viewport or change the planar
quaternion formula to Y-up when reading `/robot/01/odom`.

For full 3D vectors, the corresponding axis rotation is
`(x_ros, y_ros, z_ros) = (x_sim, -z_sim, y_sim)`. This is a frame conversion,
not an instruction to change arbitrary sensor/body frames: use their
documented frame IDs and transforms. The warehouse adapter publishes planar
odom, not general drone or arm odometry.

The simulator decision is recorded in sibling `robotos-sim` ADR 0006,
`docs/adr/0006-y-up-world-frame.md`. The SDK compatibility decision is
robotos ADR 0028 (`docs/adr/0028-simulator-coordinate-compatibility.md`).

## Packaging

Y-up requires a rebuilt simulator binary with its embedded frontend.
It does not require an ABI or protobuf schema change, or a replacement
firmware archive. A current source checkout alone does not prove a student
bundle is current. Record the source revision, checksums, and checks actually
run in `robotos-workshop/packs/SMOKE.md`; build native apps on their target OS.


## New source APIs and installed-pack limits (2026-11-16)

Source SDKs now support Frame/Convention, directions/dirs, explicit startup files,
UUID metadata queries, host quantity bindings and same-origin BasisChange. Earlier
student packs do not provide the new feature. Keep these workshops on their
existing topics; do not infer new APIs or Y-up profile support from a source update.
Physical TF, recording frame snapshots and browser discovery remain roadmap work.
