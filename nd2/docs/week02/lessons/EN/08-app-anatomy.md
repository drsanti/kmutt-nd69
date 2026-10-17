# Anatomy of a Monitor and Control Application

![Four layers: transport, connection, bindings, and the user interface](../images/08-app-anatomy.png)

You have the channels (serial, BLE, Wi-Fi through a service) and the conversation (telemetry, command, event). This lesson describes what the application looks like inside, as layers rather than as a code listing. The same anatomy fits a page, a desktop tool, or a mobile client. The week builds it as a web page.

## Four parts every device application has

```
┌─────────────────────────────────────────┐
│            UI and application state     │  what the user sees and operates
├─────────────────────────────────────────┤
│   telemetry binding    command dispatch │  turn bytes into meaning, and back
├─────────────────────────────────────────┤
│           connection manager            │  connect, drop, reconnect
├─────────────────────────────────────────┤
│      transport (Serial / BLE / Wi-Fi)   │  the actual channel
└─────────────────────────────────────────┘
```

Read from the bottom. Each layer may know about the one beneath it. None of them should reach past it.

### 1. Transport — the raw channel

The transport is the only layer that knows whether the pipe is serial, BLE, or a network socket to a service.

- It connects, it exposes an inbound stream, and it accepts outbound bytes or messages.
- Replacing serial with BLE, or BLE with a network service, replaces this layer. The layers above keep their jobs.
- It does not decide what a battery reading means, and it does not decide whether the user may press the button again. Meaning and policy live higher up.

If a React component, or a DOM handler, calls `navigator.serial` directly, this layer has leaked. The leak is what makes a second transport a rewrite instead of an adapter.

### 2. Connection manager — the session

This is the layer beginners skip, and it is the one users feel first.

- It owns the lifecycle: disconnected → connecting → connected → disconnected again, at any moment → reconnecting.
- It answers "where are we?" for the rest of the application. The status in the header, the enablement of the controls, and the reconnect policy all read this state. They do not each keep a private boolean named `isConnected`.
- It treats fragility as ordinary. A port already claimed, a BLE link that drops at the edge of the room, a network service that resets: each one is a transition, not an uncaught exception that takes the page down with it.
- **On every return to connected, it refreshes device state before the UI trusts the shadow.** The picture from the previous session is evidence of the past, not a reading.

A connection manager with an explicit state machine is boring to write and easy to test. A page that sprinkles `connected = true` through click handlers is neither.

### 3. Telemetry binding — from a stream to state

- Inbound telemetry and events update the application state the UI is rendering.
- The work is: subscribe to the right signals, decode them into meaning (this number is a battery percent, not an anonymous byte), retain history when a chart needs it, and notify the UI on change.
- This is where an endless stream becomes "latest value, plus a timeline." A gauge reads the latest value. A chart reads the timeline. A log reads events. They are three views of one binding, not three parsers.

Decoding belongs here, or inside the library that sits just under here. A component that shifts bits out of an `ArrayBuffer` is a component that will be copied, incorrectly, the next time someone adds a gauge.

### 4. Command dispatcher — the outbound path with manners

A button press does not write to the pipe. It goes through the dispatcher.

- Queue or coalesce commands so a slider cannot flood the device.
- Wait for an acknowledgement when the protocol has one.
- Time out when the acknowledgement does not arrive, and tell the user the command was not confirmed.
- This is where "respect the constrained side" becomes code. The dispatcher is allowed to drop a redundant write. The transport is not the place to discover that you sent two hundred color updates during one drag.

Keep commands and telemetry on separate paths even though they share a connection. When the LED does not change, you inspect the dispatcher. When the meter does not move, you inspect the binding. A single function that both sends and parses makes that split impossible.

## Application state is the seam

Two kinds of state live in the page, and mixing them is a bug:

- **Local state** belongs to the application alone. Which panel is open, a UI preference, a filter on the chart. The device has no opinion.
- **Device shadow** is the picture of the device. LED color, microphone enabled, last battery sample. **It changes when telemetry, an event, or a confirmed command says so. The UI does not invent it.**

The interface should report the status of that picture:

- `connected`, `disconnected`, and `reconnecting` are visible at all times. A control that commands the device is disabled unless the session is connected.
- A displayed value is either live or last-seen. After a disconnect, a frozen number without a timestamp is a false instrument. Stamp it, or replace it with unknown.

Optimistic updates are allowed and must be marked. If the user sets a color and you paint the swatch red before the acknowledgement, that swatch is a prediction. If the ack fails, the prediction comes back off the screen.

## Transport abstraction — one application, more than one channel

The payoff of the layers is that the top of the stack does not name the pipe:

```
UI ──► telemetry binding / dispatcher ──► connection manager
                                              │
                    ┌─────────────────────────┼─────────────────┐
                    ▼                         ▼                 ▼
              Serial transport          BLE transport     network transport
              (Web Serial)              (Web Bluetooth)   (through a service)
```

- Telemetry, command, and event mean the same thing on every channel, so the upper layers have nothing to branch on.
- One interface is enough: `connect()`, an inbound telemetry stream, `send(command)`, and a disconnect signal. Each transport implements that interface. The serial adapter frames bytes. The BLE adapter maps characteristics. The network adapter speaks the service's protocol. The connection manager cannot tell which one it is holding, and should not try.
- A demo that switches between serial and BLE in one page is then a choice of adapter at connect time. It is not a second application, and it is not a branch inside the color picker.

The shape above is a design vocabulary, not a library you import. When a real SDK arrives, expect it to look like this if it was built for more than one channel. If it was not, this is still the shape to wrap around it.

## Tooling for this week — TypeScript and Vite

The page is ordinary web software, with types:

- **TypeScript** earns its place because the directions are types. A telemetry sample is one type. A command is another. An event handler has a known payload. The compiler will not notice a stale shadow, but it will notice a command passed where a sample was expected. That class of mistake is common once more than one signal exists.
- **Vite** is the development server and the production build. It serves the page on `localhost`, and localhost is a secure context, so Web Serial and Web Bluetooth work during development without a certificate. You are not configuring a bundler by hand to get that.
- The anatomy does not require a UI framework. The same four layers sit under vanilla TypeScript or under any framework. Pick a framework for the UI. Do not pick it as the place to hide the connection manager.

## Patterns worth keeping

- **Keep the layers separate.** Transport, connection, binding, state. Do not put "open the serial port" and "draw the gauge" in one function.
- **Get the connection right before you add features.** An application that drops the link and keeps showing live data is worse than an application with fewer gauges.
- **Device state comes from the device.** The application tracks. It does not guess, except for an optimistic update it is prepared to retract.
- **The channel is a detail.** Product logic does not mention the cable or the radio.
- **The user sees the truth of the session.** Connection status, and the age of the data, are part of the instrument.

## Checklist

| Question | You should be able to answer |
|---|---|
| What are the main parts? | Transport, connection manager, telemetry binding, command dispatcher, plus UI and state. |
| What is the transport abstraction? | One interface above serial, BLE, and the network path. Upper layers do not know which pipe they have. |
| What is shadow state? | The application's picture of the device. It is updated from telemetry and events. It is not invented by the UI. |
| What must a reconnect do? | Refresh state from the device. The previous shadow cannot be trusted. |
| Why have a dispatcher? | To queue, coalesce, acknowledge, time out, and stop a user gesture from flooding the pipe. |
| Why is Vite on localhost convenient? | Localhost is a secure context. Web Serial and Web Bluetooth run in development without HTTPS. |
