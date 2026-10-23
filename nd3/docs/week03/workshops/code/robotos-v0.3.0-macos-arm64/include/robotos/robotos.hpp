// robotos C++20 SDK — RAII wrapper over the C ABI (plan §7.3,
// ADR 0006). Protobuf types are duck-typed: any generated message with
// SerializeToString / ParseFromArray / GetDescriptor works; this header
// does not include protobuf headers itself.
#pragma once

#include <robotos/robotos.h>

#include <chrono>
#include <concepts>
#include <cstdint>
#include <cstring>
#include <functional>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace robotos {

/// Mirror of robotos_status_t.
enum class Status : uint32_t {
    Ok = ROBOTOS_OK,
    InvalidArgument = ROBOTOS_INVALID_ARGUMENT,
    TransportError = ROBOTOS_TRANSPORT_ERROR,
    NotInitialized = ROBOTOS_NOT_INITIALIZED,
    Shutdown = ROBOTOS_SHUTDOWN,
    ChannelClosed = ROBOTOS_CHANNEL_CLOSED,
    PayloadTooLarge = ROBOTOS_PAYLOAD_TOO_LARGE,
    ProtocolError = ROBOTOS_PROTOCOL_ERROR,
    Timeout = ROBOTOS_TIMEOUT,
    InvalidState = ROBOTOS_INVALID_STATE,
    Unavailable = ROBOTOS_UNAVAILABLE,
    AmbiguousResponder = ROBOTOS_AMBIGUOUS_RESPONDER,
    Cancelled = ROBOTOS_CANCELLED,
    DeadlineExceeded = ROBOTOS_DEADLINE_EXCEEDED,
    ResourceExhausted = ROBOTOS_RESOURCE_EXHAUSTED,
    NotFound = ROBOTOS_NOT_FOUND,
    Error = ROBOTOS_ERROR,
};

const char* status_name(Status status) noexcept;

/// Thrown by constructors/factories. Per-call APIs (publish, recv)
/// return `Status` instead of throwing.
class Error : public std::runtime_error {
public:
    Error(Status status, const std::string& detail);
    Status status() const noexcept { return status_; }

private:
    Status status_;
};

/// True for generated protobuf message types.
template <typename M>
concept ProtobufMessage =
    std::default_initializable<M> && requires(M m, std::string* s) {
        { m.SerializeToString(s) } -> std::convertible_to<bool>;
        { m.ParseFromArray(nullptr, 0) } -> std::convertible_to<bool>;
        {
            M::default_instance().GetDescriptor()->full_name()
        } -> std::convertible_to<std::string_view>;
    };

/// Metadata carried by the wire envelope (ADR 0003).
struct MessageMeta {
    std::string publisher_uuid;
    uint64_t sequence = 0;
    uint64_t timestamp_ns = 0;
};

/// Parameter descriptor — declaration-time metadata (ADR 0011).
struct ParamDescriptor {
    std::string description;
    bool read_only = false;
    /// Numeric range applied to int64/double params when set.
    std::optional<std::pair<double, double>> range;
};

/// Supported C++ parameter types (scalars — arrays are Rust-side
/// only for now).
template <typename T>
concept ParamScalar =
    std::same_as<T, bool> || std::same_as<T, int64_t> ||
    std::same_as<T, double> || std::same_as<T, std::string>;

/// Node lifecycle state (ADR 0012) — mirror of robotos_lifecycle_state_t.
enum class LifecycleState : uint32_t {
    Unspecified = ROBOTOS_LIFECYCLE_UNSPECIFIED,
    Created = ROBOTOS_LIFECYCLE_CREATED,
    Inactive = ROBOTOS_LIFECYCLE_INACTIVE,
    Active = ROBOTOS_LIFECYCLE_ACTIVE,
    Finalized = ROBOTOS_LIFECYCLE_FINALIZED,
    Error = ROBOTOS_LIFECYCLE_ERROR,
    Configuring = ROBOTOS_LIFECYCLE_CONFIGURING,
    Activating = ROBOTOS_LIFECYCLE_ACTIVATING,
    Deactivating = ROBOTOS_LIFECYCLE_DEACTIVATING,
    CleaningUp = ROBOTOS_LIFECYCLE_CLEANING_UP,
    ShuttingDown = ROBOTOS_LIFECYCLE_SHUTTING_DOWN,
};

/// QoS preset names (ADR 0010) — mirror of robotos_qos_preset_t.
/// Presets map to concrete depth/overflow/priority values in the
/// Rust runtime; unhonored knobs fail at create time.
enum class QosPreset : uint32_t {
    Default = ROBOTOS_QOS_DEFAULT,
    SensorData = ROBOTOS_QOS_SENSOR_DATA,
    Control = ROBOTOS_QOS_CONTROL,
    State = ROBOTOS_QOS_STATE,
    Config = ROBOTOS_QOS_CONFIG,
    Logging = ROBOTOS_QOS_LOGGING,
};

/// Explicit transport configuration; empty vectors + multicast=true
/// give the default localhost-first Zenoh peer mode.
struct NodeOptions {
    std::vector<std::string> listen_endpoints;
    std::vector<std::string> connect_endpoints;
    uint16_t domain = 0;
    bool multicast = true;
};

/// Sentinel: wait forever in `Subscriber::recv`.
inline constexpr std::chrono::milliseconds kInfiniteTimeout{
    std::chrono::milliseconds::max()};

class Node;

namespace detail {

[[noreturn]] void throw_status(uint32_t code, std::string_view operation);
inline void check(uint32_t code, std::string_view operation) {
    if (code != ROBOTOS_OK) {
        throw_status(code, operation);
    }
}
std::string join_csv(const std::vector<std::string>& endpoints);
MessageMeta convert_meta(const robotos_msg_meta_t& meta);
uint32_t to_timeout_ms(std::chrono::milliseconds timeout);

// Scalar parameter type → FFI function selection.
template <typename T>
uint32_t param_declare(robotos_node_t* node, const char* name,
                       const T& initial,
                       const robotos_param_descriptor_t* d);
template <>
inline uint32_t param_declare<bool>(robotos_node_t* n, const char* name,
                                    const bool& v,
                                    const robotos_param_descriptor_t* d) {
    return robotos_param_declare_bool(n, name, v ? 1 : 0, d);
}
template <>
inline uint32_t param_declare<int64_t>(robotos_node_t* n, const char* name,
                                       const int64_t& v,
                                       const robotos_param_descriptor_t* d) {
    return robotos_param_declare_i64(n, name, v, d);
}
template <>
inline uint32_t param_declare<double>(robotos_node_t* n, const char* name,
                                      const double& v,
                                      const robotos_param_descriptor_t* d) {
    return robotos_param_declare_f64(n, name, v, d);
}
template <>
inline uint32_t param_declare<std::string>(
    robotos_node_t* n, const char* name, const std::string& v,
    const robotos_param_descriptor_t* d) {
    return robotos_param_declare_string(n, name, v.c_str(), d);
}

template <typename T>
uint32_t param_get(robotos_node_t* node, const char* name, T* out);
template <>
inline uint32_t param_get<bool>(robotos_node_t* n, const char* name, bool* out) {
    int v = 0;
    const auto st = robotos_param_get_bool(n, name, &v);
    *out = v != 0;
    return st;
}
template <>
inline uint32_t param_get<int64_t>(robotos_node_t* n, const char* name,
                                   int64_t* out) {
    return robotos_param_get_i64(n, name, out);
}
template <>
inline uint32_t param_get<double>(robotos_node_t* n, const char* name,
                                  double* out) {
    return robotos_param_get_f64(n, name, out);
}

template <typename T>
uint32_t param_set(robotos_node_t* node, const char* name, const T& v);
template <>
inline uint32_t param_set<bool>(robotos_node_t* n, const char* name,
                                const bool& v) {
    return robotos_param_set_bool(n, name, v ? 1 : 0);
}
template <>
inline uint32_t param_set<int64_t>(robotos_node_t* n, const char* name,
                                   const int64_t& v) {
    return robotos_param_set_i64(n, name, v);
}
template <>
inline uint32_t param_set<double>(robotos_node_t* n, const char* name,
                                  const double& v) {
    return robotos_param_set_f64(n, name, v);
}

} // namespace detail

/// Typed publisher — OK from publish() means *accepted for local
/// transport*, never end-to-end receipt (plan §5.1).
template <ProtobufMessage M>
class Publisher {
public:
    ~Publisher() { robotos_publisher_destroy(handle_); }
    Publisher(const Publisher&) = delete;
    Publisher& operator=(const Publisher&) = delete;
    Publisher(Publisher&& other) noexcept
        : handle_(std::exchange(other.handle_, nullptr)) {}
    Publisher& operator=(Publisher&& other) noexcept {
        if (this != &other) {
            robotos_publisher_destroy(handle_);
            handle_ = std::exchange(other.handle_, nullptr);
        }
        return *this;
    }

    Status publish(const M& msg) noexcept {
        std::string bytes;
        if (!msg.SerializeToString(&bytes)) {
            return Status::ProtocolError;
        }
        return static_cast<Status>(robotos_publish(
            handle_, reinterpret_cast<const uint8_t*>(bytes.data()),
            bytes.size()));
    }

private:
    friend class Node;
    explicit Publisher(robotos_publisher_t* handle) : handle_(handle) {}
    robotos_publisher_t* handle_ = nullptr;
};

/// Typed subscriber — poll via recv() or arm a callback with
/// on_message() (mutually exclusive per ADR 0006).
template <ProtobufMessage M>
class Subscriber {
public:
    using Callback = std::function<void(M, const MessageMeta&)>;

    ~Subscriber() {
        robotos_subscriber_clear_callback(handle_);
        robotos_subscriber_destroy(handle_);
    }
    Subscriber(const Subscriber&) = delete;
    Subscriber& operator=(const Subscriber&) = delete;
    Subscriber(Subscriber&& other) noexcept
        : handle_(std::exchange(other.handle_, nullptr)),
          callback_(std::move(other.callback_)) {}
    Subscriber& operator=(Subscriber&& other) noexcept {
        if (this != &other) {
            robotos_subscriber_clear_callback(handle_);
            robotos_subscriber_destroy(handle_);
            handle_ = std::exchange(other.handle_, nullptr);
            callback_ = std::move(other.callback_);
        }
        return *this;
    }

    /// Blocking poll. `timeout` of kInfiniteTimeout waits forever;
    /// {0} is a non-blocking poll.
    Status recv(M& out,
                MessageMeta* meta = nullptr,
                std::chrono::milliseconds timeout = kInfiniteTimeout) {
        robotos_message_t msg{};
        const auto st = robotos_subscriber_recv_owned(
            handle_, &msg, detail::to_timeout_ms(timeout));
        if (st != ROBOTOS_OK) {
            return static_cast<Status>(st);
        }
        struct FreeMsg {
            robotos_message_t* m;
            ~FreeMsg() { robotos_message_free(m); }
        } guard{&msg};
        if (!out.ParseFromArray(msg.data, static_cast<int>(msg.len))) {
            return Status::ProtocolError;
        }
        if (meta) {
            *meta = detail::convert_meta(msg.meta);
        }
        return Status::Ok;
    }

    /// Arm callback delivery; invoked on a robotos worker thread.
    /// Callback must not block and must not call robotos APIs.
    Status on_message(Callback cb) {
        // Allocate the new callback BEFORE set_callback disarms the
        // old one — assigning callback_ first would free the old
        // user_data while the still-armed task can still touch it.
        auto next = std::make_shared<Callback>(std::move(cb));
        const auto st = robotos_subscriber_set_callback(
            handle_, &Subscriber::trampoline, next.get());
        if (st != ROBOTOS_OK) {
            return static_cast<Status>(st);
        }
        callback_ = std::move(next);
        return Status::Ok;
    }

    void clear_callback() {
        robotos_subscriber_clear_callback(handle_);
        callback_.reset();
    }

private:
    friend class Node;
    explicit Subscriber(robotos_subscriber_t* handle) : handle_(handle) {}

    static void trampoline(const uint8_t* data, size_t len,
                           const robotos_msg_meta_t* meta, void* user) {
        try {
            auto& fn = *static_cast<Callback*>(user);
            M msg;
            if (!msg.ParseFromArray(data, static_cast<int>(len))) {
                return; // undecodable payload — drop, don't crash the callback
            }
            MessageMeta m = detail::convert_meta(*meta);
            fn(std::move(msg), m);
        } catch (...) {
            // Exceptions must never unwind across the FFI boundary.
        }
    }

    robotos_subscriber_t* handle_ = nullptr;
    // The Callback object address is the FFI user_data — shared_ptr
    // keeps it stable across Subscriber moves. Clear/destroy waits for
    // the callback task to exit, so it cannot dangle.
    std::shared_ptr<Callback> callback_;
};

/// Typed unary service server (ADR 0009). The handler runs on a
/// robotos worker thread; it must return promptly and must not call
/// robotos APIs reentrantly. Returning any non-Ok Status surfaces to
/// the caller; never blocks the graph.
template <ProtobufMessage Req, ProtobufMessage Rep>
class Service {
public:
    /// Handler: request in, fill `rep` out, return a Status
    /// (Ok = reply sent; others surface to the caller).
    using Handler = std::function<Status(const Req&, Rep&)>;

    ~Service() { robotos_service_destroy(handle_); }
    Service(const Service&) = delete;
    Service& operator=(const Service&) = delete;
    Service(Service&& other) noexcept
        : handle_(std::exchange(other.handle_, nullptr)),
          handler_(std::move(other.handler_)) {}
    Service& operator=(Service&& other) noexcept {
        if (this != &other) {
            robotos_service_destroy(handle_);
            handle_ = std::exchange(other.handle_, nullptr);
            handler_ = std::move(other.handler_);
        }
        return *this;
    }

private:
    friend class Node;
    explicit Service(robotos_service_t* handle) : handle_(handle) {}

    static robotos_status_t trampoline(const uint8_t* req, size_t req_len,
                                       uint8_t* resp, size_t resp_cap,
                                       size_t* resp_len, void* user) {
        try {
            auto& fn = *static_cast<Handler*>(user);
            Req request;
            if (!request.ParseFromArray(req, static_cast<int>(req_len))) {
                return ROBOTOS_INVALID_ARGUMENT;
            }
            Rep reply;
            const auto st = static_cast<uint32_t>(fn(request, reply));
            if (st != ROBOTOS_OK) {
                return static_cast<robotos_status_t>(st);
            }
            std::string bytes;
            if (!reply.SerializeToString(&bytes)) {
                return ROBOTOS_PROTOCOL_ERROR;
            }
            if (bytes.size() > resp_cap) {
                return ROBOTOS_RESOURCE_EXHAUSTED;
            }
            std::memcpy(resp, bytes.data(), bytes.size());
            *resp_len = bytes.size();
            return ROBOTOS_OK;
        } catch (...) {
            // Exceptions must never unwind across the FFI boundary.
            return ROBOTOS_ERROR;
        }
    }

    robotos_service_t* handle_ = nullptr;
    // The Handler object address is the FFI user_data — shared_ptr
    // keeps it stable across moves; destroy() joins in-flight calls.
    std::shared_ptr<Handler> handler_;
};

/// Typed unary service client (ADR 0008): each call returns exactly
/// one reply — zero responders is Unavailable, several is
/// AmbiguousResponder; never a silent pick.
/// Cancellation token for `Client::call` (RPC-06) — `cancel()` from
/// any thread; the pending call returns Status::Cancelled and the
/// server is asked (advisory, best-effort) to abort the handler.
class CallCancelToken {
public:
    CallCancelToken() {
        detail::check(robotos_call_token_create(&h_), "call_token_create");
    }
    ~CallCancelToken() { robotos_call_token_destroy(h_); }
    CallCancelToken(const CallCancelToken&) = delete;
    CallCancelToken& operator=(const CallCancelToken&) = delete;
    CallCancelToken(CallCancelToken&& o) noexcept : h_(std::exchange(o.h_, nullptr)) {}
    CallCancelToken& operator=(CallCancelToken&& o) noexcept {
        if (this != &o) {
            robotos_call_token_destroy(h_);
            h_ = std::exchange(o.h_, nullptr);
        }
        return *this;
    }

    void cancel() { robotos_call_token_cancel(h_); }
    robotos_call_token_t* raw() const { return h_; }

private:
    robotos_call_token_t* h_ = nullptr;
};

template <ProtobufMessage Req, ProtobufMessage Rep>
class Client {
public:
    /// Blocking call. `timeout` bounds the whole exchange.
    Status call(const Req& req, Rep& out,
                std::chrono::milliseconds timeout = kInfiniteTimeout) {
        return call(req, out, timeout, nullptr);
    }

    /// Blocking call that aborts when `tok` is cancelled (NULL =
    /// plain call). Cancellation returns Status::Cancelled and
    /// publishes a best-effort advisory on `{name}/_cancel`.
    Status call(const Req& req, Rep& out,
                std::chrono::milliseconds timeout,
                CallCancelToken* tok) {
        std::string bytes;
        if (!req.SerializeToString(&bytes)) {
            return Status::ProtocolError;
        }
        robotos_message_t reply{};
        const auto st = robotos_client_call_cancelable(
            node_handle_, name_.c_str(), req_schema_.c_str(),
            rep_schema_.c_str(),
            reinterpret_cast<const uint8_t*>(bytes.data()), bytes.size(),
            detail::to_timeout_ms(timeout), tok ? tok->raw() : nullptr, &reply);
        if (st != ROBOTOS_OK) {
            return static_cast<Status>(st);
        }
        struct FreeMsg {
            robotos_message_t* m;
            ~FreeMsg() { robotos_message_free(m); }
        } guard{&reply};
        if (!out.ParseFromArray(reply.data, static_cast<int>(reply.len))) {
            return Status::ProtocolError;
        }
        return Status::Ok;
    }

private:
    friend class Node;
    Client(robotos_node_t* node, std::string name)
        : node_handle_(node),
          name_(std::move(name)),
          req_schema_{Req::default_instance().GetDescriptor()->full_name()},
          rep_schema_{Rep::default_instance().GetDescriptor()->full_name()} {}
    robotos_node_t* node_handle_ = nullptr;
    std::string name_, req_schema_, rep_schema_;
};

// ---------- actions (ACT-01) ----------

/// Goal lifecycle — wire-identical to robotos.action.v1.GoalStatus.
enum class GoalStatus : int32_t {
    Unspecified = ROBOTOS_GOAL_UNSPECIFIED,
    Pending     = ROBOTOS_GOAL_PENDING,
    Accepted    = ROBOTOS_GOAL_ACCEPTED,
    Executing   = ROBOTOS_GOAL_EXECUTING,
    Canceling   = ROBOTOS_GOAL_CANCELING,
    Succeeded   = ROBOTOS_GOAL_SUCCEEDED,
    Canceled    = ROBOTOS_GOAL_CANCELED,
    Aborted     = ROBOTOS_GOAL_ABORTED,
    Rejected    = ROBOTOS_GOAL_REJECTED,
};

inline bool goal_is_terminal(GoalStatus s) noexcept {
    return s == GoalStatus::Succeeded || s == GoalStatus::Canceled ||
           s == GoalStatus::Aborted || s == GoalStatus::Rejected;
}

/// Per-goal context — valid only inside an `ActionServer` handler.
class GoalContext {
public:
    /// True once a cancel has been requested — wind down promptly.
    bool cancel_requested() const {
        return robotos_goal_cancel_requested(ctx_) != 0;
    }
    /// Publish progress on `{name}/_feedback` (best-effort).
    template <ProtobufMessage M>
    Status send_feedback(const M& fb) const {
        std::string b;
        if (!fb.SerializeToString(&b)) return Status::ProtocolError;
        return Status{robotos_goal_send_feedback(
            ctx_, reinterpret_cast<const uint8_t*>(b.data()), b.size())};
    }

private:
    template <ProtobufMessage, ProtobufMessage, ProtobufMessage>
    friend class ActionServer;
    explicit GoalContext(robotos_goal_ctx_t* ctx) : ctx_(ctx) {}
    robotos_goal_ctx_t* ctx_;
};

/// Typed action server (ADR actions): handler runs per goal,
/// `Ok` → SUCCEEDED (result serialized), other Status → ABORTED —
/// or CANCELED if a cancel landed mid-run. Blocking work is expected;
/// the handler runs off the async runtime.
template <ProtobufMessage G, ProtobufMessage F, ProtobufMessage R>
class ActionServer {
public:
    /// Handler: goal in, fill `result` out, return a Status.
    using Handler = std::function<Status(const G&, const GoalContext&, R&)>;

    ~ActionServer() { robotos_action_server_destroy(handle_); }
    ActionServer(const ActionServer&) = delete;
    ActionServer& operator=(const ActionServer&) = delete;
    ActionServer(ActionServer&& o) noexcept
        : handle_(std::exchange(o.handle_, nullptr)),
          handler_(std::move(o.handler_)) {}
    ActionServer& operator=(ActionServer&& o) noexcept {
        if (this != &o) {
            robotos_action_server_destroy(handle_);
            handle_ = std::exchange(o.handle_, nullptr);
            handler_ = std::move(o.handler_);
        }
        return *this;
    }

private:
    friend class Node;
    explicit ActionServer(robotos_action_server_t* handle) : handle_(handle) {}

    static robotos_status_t trampoline(
        const uint8_t* goal, size_t goal_len, robotos_goal_ctx_t* ctx,
        uint8_t* res, size_t res_cap, size_t* res_len, void* user) {
        auto& fn = *static_cast<Handler*>(user);
        G g;
        if (!g.ParseFromArray(goal, static_cast<int>(goal_len))) {
            return ROBOTOS_INVALID_ARGUMENT;
        }
        GoalContext c(ctx);
        R r;
        const auto st = static_cast<uint32_t>(fn(g, c, r));
        if (st != ROBOTOS_OK) {
            return static_cast<robotos_status_t>(st);
        }
        std::string bytes;
        if (!r.SerializeToString(&bytes)) {
            return ROBOTOS_PROTOCOL_ERROR;
        }
        if (bytes.size() > res_cap) {
            return ROBOTOS_RESOURCE_EXHAUSTED;
        }
        std::memcpy(res, bytes.data(), bytes.size());
        *res_len = bytes.size();
        return ROBOTOS_OK;
    }

    robotos_action_server_t* handle_ = nullptr;
    // The Handler object address is the FFI user_data — shared_ptr
    // keeps it stable across moves.
    std::shared_ptr<Handler> handler_;
};

/// Typed action client: `send_goal` → `next_feedback`/`result`/`cancel`.
/// One client tracks many goals by goal_id.
template <ProtobufMessage G, ProtobufMessage F, ProtobufMessage R>
class ActionClient {
public:
    ~ActionClient() { robotos_action_client_destroy(handle_); }
    ActionClient(const ActionClient&) = delete;
    ActionClient& operator=(const ActionClient&) = delete;
    ActionClient(ActionClient&& o) noexcept
        : handle_(std::exchange(o.handle_, nullptr)) {}
    ActionClient& operator=(ActionClient&& o) noexcept {
        if (this != &o) {
            robotos_action_client_destroy(handle_);
            handle_ = std::exchange(o.handle_, nullptr);
        }
        return *this;
    }

    /// Send a goal — fills `out_goal_id` with the goal UUID.
    /// Status::InvalidArgument = rejected by the server.
    Status send_goal(const G& goal, std::string& out_goal_id,
                     std::chrono::milliseconds timeout = kInfiniteTimeout) {
        std::string bytes;
        if (!goal.SerializeToString(&bytes)) return Status::ProtocolError;
        char buf[64];
        size_t n = 0;
        const auto st = robotos_action_send_goal(
            handle_, reinterpret_cast<const uint8_t*>(bytes.data()),
            bytes.size(), detail::to_timeout_ms(timeout),
            buf, sizeof(buf), &n);
        if (st != ROBOTOS_OK) return Status{st};
        out_goal_id.assign(buf, n);
        return Status::Ok;
    }

    /// Next feedback for `goal_id` (others are filtered out).
    /// Status::Timeout when none arrives in time.
    Status next_feedback(const std::string& goal_id, F& out,
                         std::chrono::milliseconds timeout = kInfiniteTimeout) {
        robotos_message_t msg{};
        const auto st = robotos_action_feedback_recv(
            handle_, goal_id.c_str(), detail::to_timeout_ms(timeout), &msg);
        if (st != ROBOTOS_OK) return Status{st};
        struct FreeMsg {
            robotos_message_t* m;
            ~FreeMsg() { robotos_message_free(m); }
        } guard{&msg};
        if (!out.ParseFromArray(msg.data, static_cast<int>(msg.len))) {
            return Status::ProtocolError;
        }
        return Status::Ok;
    }

    /// Block until the goal is terminal or `timeout`. `out_state` gets
    /// the final status; on Succeeded `out` gets the result.
    Status result(const std::string& goal_id, GoalStatus& out_state, R& out,
                  std::chrono::milliseconds timeout = kInfiniteTimeout) {
        robotos_goal_status_t gs = ROBOTOS_GOAL_UNSPECIFIED;
        robotos_message_t msg{};
        const auto st = robotos_action_result(
            handle_, goal_id.c_str(), detail::to_timeout_ms(timeout),
            &gs, &msg);
        if (st != ROBOTOS_OK) return Status{st};
        out_state = static_cast<GoalStatus>(gs);
        struct FreeMsg {
            robotos_message_t* m;
            ~FreeMsg() { robotos_message_free(m); }
        } guard{&msg};
        if (gs == ROBOTOS_GOAL_SUCCEEDED && msg.len > 0 &&
            !out.ParseFromArray(msg.data, static_cast<int>(msg.len))) {
            return Status::ProtocolError;
        }
        return Status::Ok;
    }

    /// Request cancellation (advisory); `out_state` = server-reported
    /// status (e.g. Canceling, or a terminal state if already done).
    Status cancel(const std::string& goal_id, GoalStatus& out_state,
                  std::chrono::milliseconds timeout = kInfiniteTimeout) {
        robotos_goal_status_t gs = ROBOTOS_GOAL_UNSPECIFIED;
        const auto st = robotos_action_cancel(
            handle_, goal_id.c_str(), detail::to_timeout_ms(timeout), &gs);
        if (st == ROBOTOS_OK) out_state = static_cast<GoalStatus>(gs);
        return Status{st};
    }

private:
    friend class Node;
    explicit ActionClient(robotos_action_client_t* handle) : handle_(handle) {}
    robotos_action_client_t* handle_ = nullptr;
};

/// A robotos node — owns the Tokio runtime and transport session.
struct ReplayOpts {
    double rate = 1.0;                 ///< pacing multiplier
    bool allow_command_topics = false; ///< lift the cmd guard
    std::vector<std::string> topics{}; ///< empty = all
    std::string prefix{};              ///< remap prefix
};

struct ReplayReport {
    uint64_t published = 0;
    uint64_t skipped_command = 0;
    uint64_t skipped_filter = 0;
    uint64_t failed = 0;
};

/// RAII recorder — finalizes the `.rbag` on stop()/destruction.
class Recorder {
public:
    ~Recorder();
    Recorder(const Recorder&) = delete;
    Recorder& operator=(const Recorder&) = delete;
    Recorder(Recorder&& o) noexcept : h_(o.h_) { o.h_ = nullptr; }
    Recorder& operator=(Recorder&& o) noexcept {
        if (this != &o) { if (h_) close(); h_ = o.h_; o.h_ = nullptr; }
        return *this;
    }

    /// Records written so far.
    uint64_t count() const {
        return h_ ? robotos_recorder_count(h_) : 0;
    }
    /// Finalize the bag — idempotent.
    void stop() {
        if (h_) {
            robotos_recorder_stop(h_);
            close();
        }
    }

private:
    explicit Recorder(robotos_recorder_t* h) : h_(h) {}
    void close() {
        if (h_) { robotos_recorder_destroy(h_); h_ = nullptr; }
    }
    robotos_recorder_t* h_;
    friend class Node;
};

/// Bag metadata (format version, record count, topics).
std::string bag_info(std::string_view path);

// ---------- presence (zenoh liveliness) ----------

enum class PresenceState : uint32_t {
    Down = ROBOTOS_PRESENCE_DOWN,
    Up = ROBOTOS_PRESENCE_UP,
};

/// RAII liveliness token — destroying it withdraws the declaration;
/// transport session drop withdraws it regardless (it can't go
/// stale). Move-only.
class PresenceToken {
public:
    ~PresenceToken() { close(); }
    PresenceToken(const PresenceToken&) = delete;
    PresenceToken& operator=(const PresenceToken&) = delete;
    PresenceToken(PresenceToken&& o) noexcept : h_(o.h_) { o.h_ = nullptr; }
    PresenceToken& operator=(PresenceToken&& o) noexcept {
        if (this != &o) { close(); h_ = o.h_; o.h_ = nullptr; }
        return *this;
    }

private:
    explicit PresenceToken(robotos_presence_token_t* h) : h_(h) {}
    void close() {
        if (h_) { robotos_presence_token_destroy(h_); h_ = nullptr; }
    }
    robotos_presence_token_t* h_ = nullptr;
    friend class Node;
};

/// RAII presence watch — callback fires on a robotos worker thread
/// (same contract as Subscriber::on_message: do not call robotos
/// APIs reentrantly). Destruction cancels + joins the task.
class PresenceWatcher {
public:
    using Callback = std::function<void(const std::string& keyexpr,
                                        PresenceState state)>;

    ~PresenceWatcher() { close(); }
    PresenceWatcher(const PresenceWatcher&) = delete;
    PresenceWatcher& operator=(const PresenceWatcher&) = delete;
    PresenceWatcher(PresenceWatcher&& o) noexcept
        : h_(o.h_), callback_(std::move(o.callback_)) { o.h_ = nullptr; }
    PresenceWatcher& operator=(PresenceWatcher&& o) noexcept {
        if (this != &o) {
            close();
            h_ = o.h_; o.h_ = nullptr;
            callback_ = std::move(o.callback_);
        }
        return *this;
    }

private:
    PresenceWatcher(robotos_presence_watch_t* h,
                    std::shared_ptr<Callback> cb)
        : h_(h), callback_(std::move(cb)) {}
    void close() {
        if (h_) { robotos_presence_watch_destroy(h_); h_ = nullptr; }
        callback_.reset();
    }
    static void trampoline(const char* keyexpr,
                           robotos_presence_state_t state, void* user) {
        try {
            auto& fn = *static_cast<Callback*>(user);
            fn(keyexpr ? std::string(keyexpr) : std::string{},
               static_cast<PresenceState>(state));
        } catch (...) {
        }
    }
    robotos_presence_watch_t* h_ = nullptr;
    // shared_ptr keeps the Callback address stable across moves —
    // it is the FFI user_data; destroy joins the task before return.
    std::shared_ptr<Callback> callback_;
    friend class Node;
};

class Node {
public:
    /// Default config (Zenoh peer mode, ROBOTOS_* env overrides).
    /// Throws robotos::Error on failure.
    explicit Node(std::string_view name);
    /// Explicit transport configuration.
    Node(std::string_view name, const NodeOptions& options);
    ~Node();
    Node(const Node&) = delete;
    Node& operator=(const Node&) = delete;
    Node(Node&& other) noexcept;
    Node& operator=(Node&& other) noexcept;

    /// Orderly shutdown: pending recv calls return, children start
    /// failing with Status::Shutdown. Idempotent; implied by ~Node.
    void shutdown() noexcept;
    bool running() const noexcept { return handle_ != nullptr && !shutdown_; }

    template <ProtobufMessage M>
    Publisher<M> create_publisher(std::string_view topic) {
        return create_publisher<M>(topic, QosPreset::Default);
    }

    template <ProtobufMessage M>
    Publisher<M> create_publisher(std::string_view topic, QosPreset qos) {
        robotos_publisher_t* h = nullptr;
        const std::string schema{
            M::default_instance().GetDescriptor()->full_name()};
        // Default = the transport's own defaults — same as the Rust
        // SDK's plain `publisher()`, not preset(0).
        const auto st = qos == QosPreset::Default
            ? robotos_publisher_create(
                  handle_, std::string(topic).c_str(), schema.c_str(), &h)
            : robotos_publisher_create_qos(
                  handle_, std::string(topic).c_str(), schema.c_str(),
                  static_cast<robotos_qos_preset_t>(qos), &h);
        detail::check(st, "create_publisher(qos)");
        return Publisher<M>(h);
    }

    template <ProtobufMessage M>
    Subscriber<M> create_subscriber(std::string_view topic) {
        return create_subscriber<M>(topic, QosPreset::Default);
    }

    template <ProtobufMessage M>
    Subscriber<M> create_subscriber(std::string_view topic, QosPreset qos) {
        robotos_subscriber_t* h = nullptr;
        const std::string schema{
            M::default_instance().GetDescriptor()->full_name()};
        const auto st = qos == QosPreset::Default
            ? robotos_subscriber_create(
                  handle_, std::string(topic).c_str(), schema.c_str(), &h)
            : robotos_subscriber_create_qos(
                  handle_, std::string(topic).c_str(), schema.c_str(),
                  static_cast<robotos_qos_preset_t>(qos), &h);
        detail::check(st, "create_subscriber(qos)");
        return Subscriber<M>(h);
    }

    /// Declare a typed unary service. Throws robotos::Error on
    /// failure. `handler` runs per request on a robotos thread.
    template <ProtobufMessage Req, ProtobufMessage Rep>
    Service<Req, Rep> create_service(
        std::string_view name,
        typename Service<Req, Rep>::Handler handler) {
        robotos_service_t* h = nullptr;
        auto service = Service<Req, Rep>(nullptr);
        service.handler_ =
            std::make_shared<typename Service<Req, Rep>::Handler>(
                std::move(handler));
        const std::string req_schema{
            Req::default_instance().GetDescriptor()->full_name()};
        const std::string rep_schema{
            Rep::default_instance().GetDescriptor()->full_name()};
        detail::check(
            robotos_service_create(
                handle_, std::string(name).c_str(), req_schema.c_str(),
                rep_schema.c_str(), &Service<Req, Rep>::trampoline,
                service.handler_.get(), &h),
            "create_service");
        service.handle_ = h;
        return service;
    }

    /// Create a typed client. Cheap — each `call` is independent.
    template <ProtobufMessage Req, ProtobufMessage Rep>
    Client<Req, Rep> create_client(std::string_view name) {
        return Client<Req, Rep>(handle_, std::string(name));
    }

    /// Declare a typed action server on `name`. Throws on failure.
    template <ProtobufMessage G, ProtobufMessage F, ProtobufMessage R>
    ActionServer<G, F, R> create_action_server(
        std::string_view name,
        typename ActionServer<G, F, R>::Handler handler) {
        robotos_action_server_t* h = nullptr;
        auto srv = ActionServer<G, F, R>(nullptr);
        srv.handler_ =
            std::make_shared<typename ActionServer<G, F, R>::Handler>(
                std::move(handler));
        detail::check(
            robotos_action_server_create(
                handle_, std::string(name).c_str(),
                &ActionServer<G, F, R>::trampoline, srv.handler_.get(), &h),
            "create_action_server");
        srv.handle_ = h;
        return srv;
    }

    /// Connect a typed action client to `name`. Throws on failure.
    template <ProtobufMessage G, ProtobufMessage F, ProtobufMessage R>
    ActionClient<G, F, R> create_action_client(std::string_view name) {
        robotos_action_client_t* h = nullptr;
        detail::check(
            robotos_action_client_create(handle_, std::string(name).c_str(), &h),
            "create_action_client");
        return ActionClient<G, F, R>(h);
    }

    // ---------- parameters (ADR 0011) ----------

    /// Opt in/out of remote `set` requests — off by default.
    void allow_remote_params(bool allow) {
        robotos_param_allow_remote(handle_, allow ? 1 : 0);
    }

    /// Pre-commit veto hook (ADR 0011) — runs synchronously inside
    /// `set` after descriptor checks, before the write lands.
    /// `fn(name, value_type, new_value, old_value)` returns true to
    /// accept; false/throw rejects the set (caller sees the error).
    /// Values arrive as display strings; `value_type` is the proto
    /// ParamType ordinal. Must not call back into the params API —
    /// the table lock is held.
    using ParamSetHook = std::function<bool(
        std::string_view, uint32_t, std::string_view, std::string_view)>;
    void on_param_set(ParamSetHook fn) {
        auto box = std::make_shared<ParamSetHook>(std::move(fn));
        detail::check(
            robotos_param_on_set(
                handle_, &Node::param_set_trampoline, box.get()),
            "on_param_set");
        hook_refs_.push_back(std::move(box));
    }

    // ---------- lifecycle (ADR 0012) ----------

    /// Current lifecycle state.
    [[nodiscard]] LifecycleState lifecycle_state() const {
        return static_cast<LifecycleState>(robotos_lifecycle_get(handle_));
    }

    /// Transitions — `Status::InvalidState` for illegal transitions
    /// or unmanaged nodes.
    [[nodiscard]] Status configure() {
        return Status{robotos_lifecycle_configure(handle_)};
    }
    [[nodiscard]] Status activate() {
        return Status{robotos_lifecycle_activate(handle_)};
    }
    [[nodiscard]] Status deactivate() {
        return Status{robotos_lifecycle_deactivate(handle_)};
    }
    [[nodiscard]] Status cleanup() {
        return Status{robotos_lifecycle_cleanup(handle_)};
    }

    /// Opt in/out of remote lifecycle `set` — off by default.
    void allow_remote_lifecycle(bool allow) {
        robotos_lifecycle_allow_remote(handle_, allow ? 1 : 0);
    }

    /// Transition hook (ADR 0012) — `fn` runs inside the transition;
    /// returning false (or throwing) fails it and the node enters
    /// `Error` — recover via `cleanup()`. Hooks must be registered
    /// before the transition runs.
    enum class LifecycleHook : int {
        Configure  = ROBOTOS_LC_ON_CONFIGURE,
        Activate   = ROBOTOS_LC_ON_ACTIVATE,
        Deactivate = ROBOTOS_LC_ON_DEACTIVATE,
        Cleanup    = ROBOTOS_LC_ON_CLEANUP,
    };
    void on_lifecycle(LifecycleHook which, std::function<bool()> fn) {
        auto box = std::make_shared<std::function<bool()>>(std::move(fn));
        detail::check(
            robotos_lifecycle_on(handle_, static_cast<int>(which),
                                 &Node::lifecycle_trampoline, box.get()),
            "on_lifecycle");
        hook_refs_.push_back(std::move(box));
    }

    // ---------- tracing (TRACE-001) ----------

    /// Enable/disable /{uuid}/_trace event publishing.
    void set_tracing(bool on) {
        detail::check(
            robotos_node_set_tracing(handle_, on ? 1 : 0),
            "set_tracing");
    }

    // ---------- .rbag record/replay (BAG-01) ----------

    /// Start recording `topics` to `path`; returns an RAII
    /// `Recorder` — call `stop()` (or let the destructor finalize).
    Recorder record(std::vector<std::string> topics,
                    std::string_view path,
                    std::string_view label = "");

    /// Replay a bag file. Returns counts published/skipped.
    ReplayReport replay(std::string_view path, const ReplayOpts& opts = {});

    // ---------- presence (zenoh liveliness) ----------

    /// Presence graph as JSON — same shape the CLI/UI consume:
    /// `{"nodes":[{uuid,name,lifecycle,endpoints:[{topic,kind,schema,qos}]}]}`.
    /// `settle_ms` waits for announcements before snapshotting.
    std::string graph_json(uint32_t settle_ms = 1600) const {
        size_t need = 0;
        robotos_node_graph_json(handle_, settle_ms, nullptr, 0, &need);
        std::string buf(need + 1, '\0');
        detail::check(
            robotos_node_graph_json(
                handle_, settle_ms, buf.data(), buf.size(), &need),
            "graph_json");
        buf.resize(need);
        return buf;
    }

    /// One-shot query — keyexprs currently alive under `keyexpr`
    /// (e.g. "robotos/0/presence/*").
    std::vector<std::string> presence_get(std::string_view keyexpr) const {
        std::vector<std::string> out;
        detail::check(
            robotos_presence_get(
                handle_, std::string(keyexpr).c_str(),
                [](const char* ke, robotos_presence_state_t, void* user) {
                    static_cast<std::vector<std::string>*>(user)
                        ->emplace_back(ke ? ke : "");
                },
                &out, nullptr),
            "presence_get");
        return out;
    }

    /// Watch UP/DOWN events under `keyexpr` — replays tokens alive
    /// at subscribe time. Throws robotos::Error on failure.
    PresenceWatcher presence_watch(std::string_view keyexpr,
                                   PresenceWatcher::Callback cb) {
        auto callback = std::make_shared<PresenceWatcher::Callback>(
            std::move(cb));
        robotos_presence_watch_t* h = nullptr;
        detail::check(
            robotos_presence_watch(
                handle_, std::string(keyexpr).c_str(),
                &PresenceWatcher::trampoline, callback.get(), &h),
            "presence_watch");
        return PresenceWatcher(h, std::move(callback));
    }

    /// Declare this node present under `keyexpr` — session-backed,
    /// withdrawn automatically when the transport drops. Hold the
    /// token while the node should be discoverable.
    PresenceToken presence_declare(std::string_view keyexpr) {
        robotos_presence_token_t* h = nullptr;
        detail::check(
            robotos_presence_declare(
                handle_, std::string(keyexpr).c_str(), &h),
            "presence_declare");
        return PresenceToken(h);
    }

    /// Declare a parameter. Throws robotos::Error on failure
    /// (duplicate name, invalid name).
    template <ParamScalar T>
    void declare_parameter(std::string_view name, const T& initial,
                           const ParamDescriptor& desc = {}) {
        robotos_param_descriptor_t d{
            .struct_size = sizeof(robotos_param_descriptor_t),
            .description = desc.description.empty() ? nullptr
                                                    : desc.description.c_str(),
            .read_only = static_cast<uint8_t>(desc.read_only ? 1 : 0),
            .has_range = static_cast<uint8_t>(desc.range ? 1 : 0),
            .range_min = desc.range ? desc.range->first : 0.0,
            .range_max = desc.range ? desc.range->second : 0.0,
        };
        const std::string n{name};
        detail::check(detail::param_declare<T>(handle_, n.c_str(), initial, &d),
                      "declare_parameter");
    }

    /// Current value. Throws on undeclared name or type mismatch.
    template <ParamScalar T>
    T get_parameter(std::string_view name) const {
        const std::string n{name};
        T out{};
        if constexpr (std::same_as<T, std::string>) {
            char buf[4096];
            size_t len = 0;
            detail::check(
                robotos_param_get_string(handle_, n.c_str(), buf, sizeof buf, &len),
                "get_parameter");
            out.assign(buf, len);
        } else {
            detail::check(detail::param_get<T>(handle_, n.c_str(), &out),
                          "get_parameter");
        }
        return out;
    }

    /// Set a declared parameter. Throws on rejection (type, range,
    /// read-only, undeclared).
    template <ParamScalar T>
    void set_parameter(std::string_view name, const T& value) {
        const std::string n{name};
        if constexpr (std::same_as<T, std::string>) {
            detail::check(robotos_param_set_string(handle_, n.c_str(), value.c_str()),
                          "set_parameter");
        } else {
            detail::check(detail::param_set<T>(handle_, n.c_str(), value),
                          "set_parameter");
        }
    }

private:
    static int param_set_trampoline(const char* name, int type,
                                    const char* nv, const char* ov,
                                    void* ud) {
        const auto& f = *static_cast<ParamSetHook*>(ud);
        try {
            return f(name ? std::string_view{name} : "",
                     static_cast<uint32_t>(type),
                     nv ? std::string_view{nv} : "",
                     ov ? std::string_view{ov} : "")
                     ? 0
                     : 1;
        } catch (...) {
            return 1;
        }
    }
    static int lifecycle_trampoline(void* ud) {
        const auto& f = *static_cast<std::function<bool()>*>(ud);
        try {
            return f() ? 0 : 1;
        } catch (...) {
            return 1;
        }
    }

    robotos_node_t* handle_ = nullptr;
    bool shutdown_ = false;
    std::vector<std::shared_ptr<const void>> hook_refs_;
};

} // namespace robotos
