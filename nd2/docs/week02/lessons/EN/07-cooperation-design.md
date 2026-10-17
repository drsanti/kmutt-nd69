# From Capabilities to Cooperation

![An application and a device splitting real-time work from heavy thinking](../images/07-cooperation-design.png)

The channel is settled enough to use. The next question is how the two machines share the work. Cooperation design is the set of rules for that split: which direction each message travels, who is allowed to spend the small machine's budget, and who owns the truth when the link drops.

## Three directions, and only three

Every device interface, on every channel, reduces to three directions:

| Direction | Name | Examples |
|---|---|---|
| Device → application | **Telemetry** | Values the device emits on its own: battery, motion, sound level. A periodic stream, or a push when the value changes. |
| Application → device | **Command** | An instruction to act: set the LED color, play a tone, enable or disable a feature. |
| Device → application, when something happens | **Event** | A fact that occurred on the device: a touch, a fault, a state transition. It is not the reply to a command. It is an occurrence. |

The mistake at the start is to treat telemetry and events as the same stream. They are not.

- **Telemetry** is a sequence of samples. Battery every ten seconds is telemetry even when the number did not change. Motion at a high rate is telemetry because the quantity is continuous and you asked to follow it.
- **An event** is a single occurrence. One touch happened. One fault was raised. One threshold was crossed. You cannot reconstruct it by sampling a gauge more often. If you miss it, it is gone unless the device stored it.

They need different handling. Telemetry updates a gauge and a chart. An event updates a log, a state machine, or a user-visible moment. Putting both in one undifferentiated byte dump is how a UI starts showing "the last number we saw" as if it were "the thing that just happened."

A command can have a reply. That reply is an acknowledgement — success, failure, or a result — and it belongs to the command. It is not an event, and it is not telemetry. Keeping the ack on the command path is what lets a timeout mean "this order was not confirmed" rather than "the device has gone quiet."

## Event-driven, not polled

Serial and BLE arrive at the same rule from opposite directions. Serial makes you build the push model on top of a pipe. BLE already has notifications. The rule for the application is the same either way:

- **Polling** means the application asks, on a timer, "anything new?" It is easy to write and expensive to run. Asking when nothing changed wastes airtime and energy on both sides. Asking too slowly misses the event you were polling for. The two failures pull the interval in opposite directions, so the interval is always wrong for something.
- **Subscribe and push** means the device speaks when it has something to say. The application does no work until a real sample or a real event arrives.

The model to build: **the application is a receiver, not an interviewer.** The device decides when to report — a cadence for telemetry, an occurrence for events. The application's work is to subscribe to the right streams and react.

```
poll:      app ── ask ──► device ── reply ──► app     every interval, even when nothing changed
subscribe: device ── push when there is news ──► app  only when there is news
```

Polling still has a narrow use: a one-shot read of a value you need immediately after connect, before the subscription is live. That is a refresh, not a design. If the steady state of your page is a `setInterval` that reads every characteristic, the cooperation is wrong.

## The constrained side sets the budget

The standing rule: **the device is the constrained peer, and the application spends its budget.**

| Budget on the small side | What it means | What you do about it |
|---|---|---|
| Memory | The receive and send buffers are tiny | Keep payloads small. Do not send a document where a struct will do. |
| Bandwidth | The pipe or the radio is narrow | Do not request telemetry faster than the channel can carry, or faster than you can display. |
| Power | A battery, or a small supply | Every byte that moves costs energy. Ask for what you will use. |
| Compute | A small microcontroller | Do not make it run the analysis. Let it sample, filter lightly, and report. |

Practices that follow:

- **Subscribe only to what the screen needs.** "Turn everything on in case we want it" is how a coin cell dies during a demo.
- **Match the rate to the physics.** Battery state is meaningful on a scale of seconds, not milliseconds. Motion changes faster, so its stream is faster. A single global "update rate" is usually wrong for every signal but one.
- **Send a command when the command changes.** Repeating the same setpoint because a slider is still firing wastes the link and can queue the device behind work it has already done.
- **Batch when the protocol allows it.** One frame with three fields is cheaper than three frames, both in overhead and in how often the radio wakes.

"Be kind to the small side" is the short version of this rule. The long version is a budget: you can name, for each stream, why that rate is the one the device can afford.

## Who does which work

This is the architecture decision, not a performance tweak.

| Work | The side that should own it | Why |
|---|---|---|
| Read a sensor on a real-time cadence | **Device** | It is next to the physics. The loop cannot wait for a round trip. |
| Act immediately | **Device** | A stop, a limit, a local interlock has to run even if the page is gone. |
| Keep a long history | **Application, or a service** | Storage and retention live on the large side. |
| Visualize and analyze | **Application** | The display, the memory, and the charting belong here. |
| Heavy logic, including a model | **Application or cloud** | The compute budget is here. The device sends features, not a training loop. |
| Keep operating after the application exits | **Device** | A device that only works while a tab is open is a peripheral of the tab. |

One rule covers the table. **The device answers the world immediately. The application thinks, stores, and displays.** Do not put a heavy decision on the small side. Do not put a real-time loop on the large side and hope the network keeps the deadline.

A useful test: unplug the page. Whatever must still be safe and still be true has to live on the device. Whatever can wait for a human to look at it can live in the application.

## Who owns state — the shadow

The failure you will hit: **the application disconnects, and the device keeps going.** The LED stays on. A motor may still be turning. The microphone may still be open. The page's last render is a picture of a machine that has already moved on.

- **The device owns its state.** It is the physical object. The application holds a view.
- The application keeps a **shadow**: the picture it currently believes. The shadow updates when telemetry or an event says so. After a reconnect, the shadow is refreshed from the device before the UI treats it as current.
- A disconnect makes the shadow stale. The UI has to say that. Show "unknown" or "last seen at …", not a frozen number presented as live. A green "connected" dot next to a two-minute-old battery reading is a false instrument.

This is why a serious dashboard distinguishes **now** from **last value we received**. They are different states. Collapsing them is how an operator acts on a machine that is no longer in the condition on screen.

Commands interact with the shadow in one direction only. Sending "set LED red" may update the shadow optimistically, but the device remains the authority. If an acknowledgement never arrives, or a later telemetry sample disagrees, the optimistic value is wrong and the UI should give it up. Optimism is a latency hiding trick, not a second source of truth.

## The teaching board, under these rules

Mapped onto the capabilities you already have:

- **Telemetry streams:** battery (slow), motion (fast), audio level (in between). The rates differ because the quantities change at different speeds.
- **Commands:** set the LED, play a tone, enable or disable capture. Each one is fired and finished. It does not become a stream in the return direction.
- **Events:** a touch on the screen. A point in time, not a sample series.
- **State:** which color the LED holds, whether the microphone is open. The device owns both. The application tracks them in the shadow.

Carry the same model over Serial or over BLE. The three directions sit above the transport. That is the reason one application can switch channels: the cooperation does not mention the pipe. The transport adapter does.

## Checklist

| Question | You should be able to answer |
|---|---|
| How is telemetry different from an event? | Telemetry is a series of samples. An event is one occurrence. |
| Poll or subscribe? | Subscribe. The application receives. It does not interview the device on a timer. |
| Why not stream telemetry as fast as possible? | Every byte spends the constrained side's budget. Match the rate to how fast the quantity changes. |
| Where does heavy logic live? | On the application or in the cloud. The device does the real-time work. |
| Does the device keep running if the page dies? | Yes. It owns its state. The application holds a shadow of that state. |
| What should a reconnect do first? | Refresh state from the device. The old shadow may be stale. |
