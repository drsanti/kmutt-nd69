//! Typed IMU subscriber: `cargo run -p rust-subscriber`.
//!
//! Transport is configured via `ROBOTOS_*` env vars
//! (`ROBOTOS_CONNECT`, `ROBOTOS_LISTEN`, `ROBOTOS_MULTICAST`,
//! `ROBOTOS_DOMAIN`); with none set it uses Zenoh peer mode with
//! multicast discovery (works on localhost/LAN).

use std::time::Duration;

use robotos::messages::sensor::v1::Imu;
use robotos::{Node, NodeConfig, Result, TransportConfig};

/// Optional flags: `--expect N` (exit 0 once N messages received —
/// used by the interop harness), `--timeout-s S` (exit 1 on timeout
/// while --expect is active; default 30) and `--topic T` (default
/// /robot/01/sensor/imu).
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
    let expect = arg_flag(&args, "--expect");
    let timeout_s = arg_flag(&args, "--timeout-s").unwrap_or(30);
    let topic = arg_str(&args, "--topic")
        .unwrap_or("/robot/01/sensor/imu")
        .to_string();

    let mut config = NodeConfig::new("imu_logger")?;
    config.transport = TransportConfig::from_env();
    let node = Node::with_config(config).await?;
    println!("node '{}' ({}) up", node.name(), node.id());

    let mut subscriber = node.subscriber::<Imu>(&topic).await?;

    println!("listening on {topic} — Ctrl-C to stop");
    let deadline = tokio::time::Instant::now() + Duration::from_secs(timeout_s);
    let mut received = 0u64;
    loop {
        tokio::select! {
            res = subscriber.recv_with_meta() => match res {
                Ok((meta, msg)) => {
                    received += 1;
                    if received.is_multiple_of(100) || received == 1 || expect.is_some() {
                        println!(
                            "#{received} seq={} from={} ts={} frame={} accel.z={:.2}",
                            meta.sequence,
                            meta.publisher_uuid,
                            msg.timestamp_ns,
                            msg.frame_id,
                            msg.acceleration.map(|a| a.z).unwrap_or(f64::NAN),
                        );
                    }
                    if expect.is_some_and(|n| received >= n) {
                        println!("received {received} messages — expectation met");
                        node.shutdown().await?;
                        return Ok(());
                    }
                }
                Err(e) => {
                    eprintln!("recv error: {e}");
                    break;
                }
            },
            _ = tokio::time::sleep_until(deadline), if expect.is_some() => {
                eprintln!("timed out after {timeout_s}s with {received} messages");
                let _ = node.shutdown().await;
                std::process::exit(1);
            }
            _ = tokio::signal::ctrl_c() => break,
        }
    }
    println!(
        "received {received} messages, {} dropped, {} schema-mismatched",
        subscriber.dropped(),
        subscriber.schema_mismatches(),
    );
    node.shutdown().await?;
    println!("shut down cleanly");
    Ok(())
}
