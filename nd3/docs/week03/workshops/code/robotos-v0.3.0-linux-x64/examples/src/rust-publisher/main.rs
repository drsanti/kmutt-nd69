//! Typed IMU publisher: `cargo run -p rust-publisher`.
//!
//! Transport is configured via `ROBOTOS_*` env vars
//! (`ROBOTOS_CONNECT`, `ROBOTOS_LISTEN`, `ROBOTOS_MULTICAST`,
//! `ROBOTOS_DOMAIN`); with none set it uses Zenoh peer mode with
//! multicast discovery (works on localhost/LAN).

use std::time::{Duration, SystemTime, UNIX_EPOCH};

use robotos::messages::sensor::v1::{Imu, Vector3};
use robotos::{Node, NodeConfig, Result, TransportConfig};

fn unix_now_ns() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_nanos() as u64)
        .unwrap_or(0)
}

/// Optional flags: `--count N` (exit after N messages, default
/// unlimited), `--interval-ms M` (default 10), `--topic T` (default
/// /robot/01/sensor/imu). Used by the cross-language interop harness.
fn arg_flag(args: &[String], name: &str) -> Option<u64> {
    args.windows(2)
        .find(|w| w[0] == name)
        .and_then(|w| w[1].parse().ok())
}

fn arg_str<'a>(args: &'a [String], name: &str) -> Option<&'a str> {
    args.windows(2)
        .find(|w| w[0] == name)
        .map(|w| w[1].as_str())
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt::init();

    let args: Vec<String> = std::env::args().collect();
    let max_count = arg_flag(&args, "--count");
    let interval_ms = arg_flag(&args, "--interval-ms").unwrap_or(10);
    let topic = arg_str(&args, "--topic")
        .unwrap_or("/robot/01/sensor/imu")
        .to_string();

    let mut config = NodeConfig::new("imu_sensor")?;
    config.transport = TransportConfig::from_env();
    let node = Node::with_config(config).await?;
    println!("node '{}' ({}) up", node.name(), node.id());

    let publisher = node.publisher::<Imu>(&topic).await?;

    // Declared parameters — visible via `robotos param list imu_sensor`
    // and writable remotely (`robotos param set`) since we opt in.
    node.declare_parameter(
        "control.kp",
        1.5f64,
        robotos::ParamDescriptor {
            description: "proportional gain".into(),
            range: Some((0.0, 100.0)),
            ..robotos::ParamDescriptor::default()
        },
    )?;
    node.declare_parameter(
        "id.serial",
        "imu-001",
        robotos::ParamDescriptor {
            description: "device serial (read-only)".into(),
            read_only: true,
            ..robotos::ParamDescriptor::default()
        },
    )?;
    node.set_allow_remote_params(true);

    println!("publishing on {topic} at {interval_ms} ms — Ctrl-C to stop");
    let mut timer = tokio::time::interval(Duration::from_millis(interval_ms));
    loop {
        tokio::select! {
            _ = timer.tick() => {
                let t = unix_now_ns();
                let msg = Imu {
                    timestamp_ns: t,
                    frame_id: "imu_link".into(),
                    acceleration: Some(Vector3 { x: 0.0, y: 0.0, z: 9.81 }),
                    angular_velocity: Some(Vector3 { x: 0.01, y: 0.0, z: 0.0 }),
                };
                publisher.publish(&msg).await?;
                let seq = publisher.sequence();
                if seq.is_multiple_of(100) {
                    println!("published {seq} samples (last ts={t} ns)");
                }
                if max_count.is_some_and(|max| seq >= max) {
                    println!("reached --count {seq}, stopping");
                    break;
                }
            }
            _ = tokio::signal::ctrl_c() => break,
        }
    }
    node.shutdown().await?;
    println!("shut down cleanly");
    Ok(())
}
