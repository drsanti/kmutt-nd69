/* robotos C ABI v0 — see docs/adr/0006-c-abi-v0.md
 *
 * Opaque handles over the Rust runtime. Raw payload bytes + schema IDs
 * cross the boundary; envelope framing and schema checks stay in Rust.
 *
 * Threading: all functions are thread-safe. Never call robotos
 * functions from inside a robotos_message_callback_t — the runtime
 * cannot be re-entered and the call will fail/abort safely.
 */
#ifndef ROBOTOS_H
#define ROBOTOS_H

#include <stddef.h>
#include <stdint.h>

#ifdef _WIN32
  #ifdef ROBOTOS_BUILDING
    #define ROBOTOS_API __declspec(dllexport)
  #else
    #define ROBOTOS_API __declspec(dllimport)
  #endif
#else
  #define ROBOTOS_API __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef struct robotos_node robotos_node_t;
typedef struct robotos_publisher robotos_publisher_t;
typedef struct robotos_subscriber robotos_subscriber_t;
typedef struct robotos_service robotos_service_t;

typedef enum robotos_status {
    ROBOTOS_OK = 0,
    ROBOTOS_INVALID_ARGUMENT = 1,
    ROBOTOS_TRANSPORT_ERROR = 2,
    ROBOTOS_NOT_INITIALIZED = 3,
    ROBOTOS_SHUTDOWN = 4,
    ROBOTOS_CHANNEL_CLOSED = 5,
    ROBOTOS_PAYLOAD_TOO_LARGE = 6,
    ROBOTOS_PROTOCOL_ERROR = 7,
    ROBOTOS_TIMEOUT = 8,
    ROBOTOS_INVALID_STATE = 9,
    /* Service/RPC statuses (ADR 0009) — surfaced verbatim so C
     * callers can distinguish failure kinds. */
    ROBOTOS_UNAVAILABLE = 10,
    ROBOTOS_AMBIGUOUS_RESPONDER = 11,
    ROBOTOS_CANCELLED = 12,
    ROBOTOS_DEADLINE_EXCEEDED = 13,
    ROBOTOS_RESOURCE_EXHAUSTED = 14,
    ROBOTOS_NOT_FOUND = 15,
    ROBOTOS_ERROR = 255
} robotos_status_t;

/* Envelope metadata for one received message. publisher_uuid is a
 * NUL-terminated UUID string (36 chars + NUL). `struct_size` is
 * populated with sizeof(robotos_msg_meta_t) — future versions may
 * append fields; compare sizes before reading unknown fields. */
typedef struct robotos_msg_meta {
    uint32_t struct_size;
    char publisher_uuid[37];
    uint64_t sequence;
    uint64_t timestamp_ns;
} robotos_msg_meta_t;

/* Invoked on a robotos-managed worker thread. `data`/`meta` are valid
 * only for the duration of the call — copy if you keep them. Must not
 * block; must not call robotos functions reentrantly. */
typedef void (*robotos_message_callback_t)(
    const uint8_t *data,
    size_t len,
    const robotos_msg_meta_t *meta,
    void *user_data);

/* Owned receive buffer — allocated by robotos, released by
 * robotos_message_free. Never free() it yourself. `struct_size` is
 * populated with sizeof(robotos_message_t) for future-proofing. */
typedef struct robotos_message {
    uint32_t struct_size;
    uint8_t *data;
    size_t len;
    robotos_msg_meta_t meta;
} robotos_message_t;

/* timeout_ms value meaning "wait forever" for robotos_subscriber_recv. */
#define ROBOTOS_TIMEOUT_INFINITE UINT32_C(0xFFFFFFFF)

/* ABI major version — currently 0 (pre-stable; bumps on breaking
 * change). Always check against ROBOTOS_ABI_VERSION at build time. */
#define ROBOTOS_ABI_VERSION UINT32_C(0)

ROBOTOS_API uint32_t robotos_abi_version(void);

/* Library version string, e.g. "0.1.0". Borrowed, never NULL,
 * never freed. */
ROBOTOS_API const char *robotos_get_version(void);

/* Detail string for the last failing call on this thread. Borrowed —
 * valid until the next robotos call on the same thread. Never NULL. */
ROBOTOS_API const char *robotos_last_error(void);

/* Create a node. Starts a Tokio runtime and opens the default
 * transport (Zenoh peer mode; ROBOTOS_* env vars apply). */
ROBOTOS_API robotos_status_t robotos_node_create(
    const char *name,
    robotos_node_t **out_node);

/* Create a node with explicit transport config. Endpoint strings are
 * comma-separated transport endpoints, e.g. "tcp/0.0.0.0:7447" (NULL
 * or "" = none). multicast: 0 = disabled, 1 = enabled.
 * robotos_node_create(name, out) is equivalent to
 * robotos_node_create_with_transport(name, NULL, NULL, 0, 1, out)
 * with ROBOTOS_* env overrides applied. */
ROBOTOS_API robotos_status_t robotos_node_create_with_transport(
    const char *name,
    const char *listen_endpoints_csv,
    const char *connect_endpoints_csv,
    uint16_t domain,
    int multicast,
    robotos_node_t **out_node);

/* Shut the node down: pending recv calls return, children created
 * from it start failing with ROBOTOS_SHUTDOWN. Idempotent.
 * robotos_node_destroy implies shutdown. */
ROBOTOS_API robotos_status_t robotos_node_shutdown(robotos_node_t *node);

/* Free the node handle (implies shutdown). Children must not be used
 * after this returns. */
ROBOTOS_API void robotos_node_destroy(robotos_node_t *node);

/* Snapshot the announced presence graph as JSON into `buf`
 * (NUL-terminated when it fits). `settle_ms` waits for announcements
 * first. `out_len` always receives the full JSON length — call with a
 * NULL/0 buffer to size it, then again with a real buffer. Returns
 * ROBOTOS_RESOURCE_EXHAUSTED when truncated.
 * Shape: {"nodes":[{"uuid","name","lifecycle","endpoints":
 *   [{"topic","kind":"pub|sub|svc","schema"}]}]} */
ROBOTOS_API robotos_status_t robotos_node_graph_json(
    robotos_node_t *node,
    uint32_t settle_ms,
    char *buf,
    size_t buf_cap,
    size_t *out_len);

/* Publishers. `schema_id` is the canonical protobuf message name,
 * e.g. "robotos.sensor.v1.Imu" — it must match the subscriber's. */
ROBOTOS_API robotos_status_t robotos_publisher_create(
    robotos_node_t *node,
    const char *topic,
    const char *schema_id,
    robotos_publisher_t **out_publisher);

/* OK means accepted for local transport — never end-to-end receipt. */
ROBOTOS_API robotos_status_t robotos_publish(
    robotos_publisher_t *publisher,
    const uint8_t *data,
    size_t len);

ROBOTOS_API void robotos_publisher_destroy(robotos_publisher_t *publisher);

/* Subscribers. Bounded queue, drop-oldest (default depth 32). */
ROBOTOS_API robotos_status_t robotos_subscriber_create(
    robotos_node_t *node,
    const char *topic,
    const char *schema_id,
    robotos_subscriber_t **out_subscriber);

/* QoS presets (ADR 0010). Passed as the `qos_preset` argument of
 * robotos_subscriber_create_qos / robotos_publisher_create_qos.
 * ROBOTOS_QOS_DEFAULT = the transport's own defaults. */
typedef enum robotos_qos_preset {
    ROBOTOS_QOS_DEFAULT = 0,
    ROBOTOS_QOS_SENSOR_DATA = 1, /* depth 8, drop-oldest */
    ROBOTOS_QOS_CONTROL = 2,     /* depth 1, drop-newest, high priority */
    ROBOTOS_QOS_STATE = 3,       /* depth 32, reliable-if-supported */
    ROBOTOS_QOS_CONFIG = 4,      /* depth 32, reserved for services */
    ROBOTOS_QOS_LOGGING = 5,     /* depth 256, drop-oldest */
} robotos_qos_preset_t;

/* Like robotos_subscriber_create with a QoS preset. Presets map to
 * concrete queue/overflow/priority values; knobs the transport cannot
 * honor fail at create time (ROBOTOS_TRANSPORT_ERROR with detail in
 * robotos_last_error) — never silently degrade. */
ROBOTOS_API robotos_status_t robotos_subscriber_create_qos(
    robotos_node_t *node,
    const char *topic,
    const char *schema_id,
    robotos_qos_preset_t qos_preset,
    robotos_subscriber_t **out_subscriber);

/* Like robotos_publisher_create with a QoS preset — only the
 * priority component affects publishers today. */
ROBOTOS_API robotos_status_t robotos_publisher_create_qos(
    robotos_node_t *node,
    const char *topic,
    const char *schema_id,
    robotos_qos_preset_t qos_preset,
    robotos_publisher_t **out_publisher);

/* Blocking poll. On ROBOTOS_OK, *out_len is the payload length and
 * meta_out_opt (if non-NULL) is filled. ROBOTOS_PAYLOAD_TOO_LARGE sets
 * *out_len to the required size (message is consumed). timeout_ms of
 * ROBOTOS_TIMEOUT_INFINITE waits forever; 0 is a non-blocking poll.
 * Returns ROBOTOS_INVALID_STATE while a callback is armed. */
ROBOTOS_API robotos_status_t robotos_subscriber_recv(
    robotos_subscriber_t *subscriber,
    uint8_t *buf,
    size_t capacity,
    size_t *out_len,
    robotos_msg_meta_t *meta_out_opt,
    uint32_t timeout_ms);

/* Like robotos_subscriber_recv but returns a heap-allocated message —
 * preferred when payload size is unknown. Free with
 * robotos_message_free. */
ROBOTOS_API robotos_status_t robotos_subscriber_recv_owned(
    robotos_subscriber_t *subscriber,
    robotos_message_t *out_message,
    uint32_t timeout_ms);

ROBOTOS_API void robotos_message_free(robotos_message_t *message);

/* Arm callback delivery (replaces any existing callback, waiting for
 * the old task to exit first). While armed, robotos_subscriber_recv
 * returns ROBOTOS_INVALID_STATE. */
ROBOTOS_API robotos_status_t robotos_subscriber_set_callback(
    robotos_subscriber_t *subscriber,
    robotos_message_callback_t callback,
    void *user_data);

/* Disarm the callback. Blocks until the callback task has exited —
 * after this returns, `user_data` is never touched again. */
ROBOTOS_API robotos_status_t robotos_subscriber_clear_callback(
    robotos_subscriber_t *subscriber);

ROBOTOS_API void robotos_subscriber_destroy(robotos_subscriber_t *subscriber);

/* ---------------- Services (v0.2, ADR 0009) -----------------------*/

/* Invoked on a robotos worker thread for each request. `req_data`
 * is valid for the call duration; write the response into `resp_buf`
 * (capacity `resp_cap`, up to ROBOTOS_MAX_RPC_PAYLOAD) and set
 * *resp_len_out. Return ROBOTOS_OK on success; any other status is
 * surfaced to the caller (detail via robotos_last_error may be set by
 * the handler itself is NOT required — the code is sufficient).
 * Must return promptly; must not call robotos functions reentrantly. */
#define ROBOTOS_MAX_RPC_PAYLOAD (4u * 1024u * 1024u)

typedef robotos_status_t (*robotos_service_handler_t)(
    const uint8_t *req_data,
    size_t req_len,
    uint8_t *resp_buf,
    size_t resp_cap,
    size_t *resp_len_out,
    void *user_data);

/* Declare a unary service. `request_schema_id`/`reply_schema_id` are
 * canonical protobuf names — a request carrying a different request
 * schema is rejected SCHEMA_MISMATCH before the handler runs.
 * `handler` may be NULL to create an empty responder (all calls
 * fail UNAVAILABLE at the transport level — reserved). `user_data` is
 * opaque to robotos and must outlive the service handle. */
ROBOTOS_API robotos_status_t robotos_service_create(
    robotos_node_t *node,
    const char *name,
    const char *request_schema_id,
    const char *reply_schema_id,
    robotos_service_handler_t handler,
    void *user_data,
    robotos_service_t **out_service);

/* Stop serving and wait for in-flight requests to finish — after
 * this returns, `handler`/`user_data` are never touched again. */
ROBOTOS_API void robotos_service_destroy(robotos_service_t *service);

/* Unary client call — at most once, responder selection per
 * ADR 0008 (ambiguous responders fail, never a silent pick).
 * On ROBOTOS_OK, `out_reply` holds the reply payload — free with
 * robotos_message_free. `timeout_ms` bounds the whole exchange;
 * ROBOTOS_TIMEOUT_INFINITE waits forever. Service failures come back
 * as their robotos_status_t (e.g. ROBOTOS_UNAVAILABLE when no
 * responder exists); detail via robotos_last_error. */
ROBOTOS_API robotos_status_t robotos_client_call(
    robotos_node_t *node,
    const char *name,
    const char *request_schema_id,
    const char *reply_schema_id,
    const uint8_t *req_data,
    size_t req_len,
    uint32_t timeout_ms,
    robotos_message_t *out_reply);

/* Cancellation token for robotos_client_call_cancelable (RPC-06).
 * Cancel from any thread; a NULL token is a plain call. */
typedef struct robotos_call_token robotos_call_token_t;
ROBOTOS_API robotos_status_t
robotos_call_token_create(robotos_call_token_t **out_token);
ROBOTOS_API void robotos_call_token_cancel(robotos_call_token_t *token);
ROBOTOS_API void robotos_call_token_destroy(robotos_call_token_t *token);

/* As robotos_client_call but the pending call aborts when `token` is
 * cancelled: returns ROBOTOS_CANCELLED and publishes a best-effort
 * CancelRequest on {name}/_cancel so responders can abort the
 * in-flight handler (advisory — a finished handler keeps its result). */
ROBOTOS_API robotos_status_t robotos_client_call_cancelable(
    robotos_node_t *node,
    const char *name,
    const char *request_schema_id,
    const char *reply_schema_id,
    const uint8_t *req_data,
    size_t req_len,
    uint32_t timeout_ms,
    robotos_call_token_t *token,
    robotos_message_t *out_reply);

/* ---------------- Parameters (v0.2, ADR 0011) --------------------*/

/* The C ABI exposes scalar parameters (bool/i64/f64/string) —
 * arrays are Rust-only for now. All functions return ROBOTOS_OK or a
 * status; undeclared names → ROBOTOS_NOT_FOUND; type mismatch,
 * read-only or range violations → ROBOTOS_INVALID_ARGUMENT;
 * duplicate declarations → ROBOTOS_INVALID_STATE. */

typedef struct robotos_param_descriptor {
    /* sizeof(robotos_param_descriptor_t) — forward ABI compat. */
    uint32_t struct_size;
    const char *description; /* borrowed for the call duration */
    uint8_t read_only;
    uint8_t has_range;
    double range_min; /* applies to numeric params when has_range */
    double range_max;
} robotos_param_descriptor_t;

/* Remote set opt-in — off by default. Affects the auto-served
 * /{uuid}/param/set service live. */
ROBOTOS_API void robotos_param_allow_remote(robotos_node_t *node, int allow);

#define ROBOTOS_PARAM_API(T)                                                  \
    ROBOTOS_API robotos_status_t robotos_param_declare_##T(                   \
        robotos_node_t *node, const char *name,                              \
        robotos_param_##T##_t initial,                                       \
        const robotos_param_descriptor_t *descriptor_opt);                   \
    ROBOTOS_API robotos_status_t robotos_param_get_##T(                      \
        robotos_node_t *node, const char *name,                              \
        robotos_param_##T##_t *out_value);                                   \
    ROBOTOS_API robotos_status_t robotos_param_set_##T(                      \
        robotos_node_t *node, const char *name,                              \
        robotos_param_##T##_t value)

typedef int64_t robotos_param_i64_t;
typedef double robotos_param_f64_t;
typedef int robotos_param_bool_t;
typedef const char *robotos_param_string_t;

ROBOTOS_PARAM_API(i64);
ROBOTOS_PARAM_API(f64);
ROBOTOS_PARAM_API(bool);
/* For get_string, `value` is the caller's buffer instead:
 * signature is special — declared manually below. */
ROBOTOS_API robotos_status_t robotos_param_declare_string(
    robotos_node_t *node, const char *name,
    const char *initial,
    const robotos_param_descriptor_t *descriptor_opt);
/* Copies the string into `buf` (NUL-terminated); sets *out_len to
 * the string length — on ROBOTOS_PAYLOAD_TOO_LARGE the required size
 * is in *out_len. */
ROBOTOS_API robotos_status_t robotos_param_get_string(
    robotos_node_t *node, const char *name,
    char *buf, size_t capacity, size_t *out_len);
ROBOTOS_API robotos_status_t robotos_param_set_string(
    robotos_node_t *node, const char *name, const char *value);

/* Param-set veto hook (ADR 0011). Runs synchronously inside set()
 * after descriptor checks, before the write lands — return nonzero
 * to reject (the set fails; no event is emitted). `type` is the
 * robotos.parameters.v1.ParamType ordinal; `new_value`/`old_value`
 * are display strings. Must not call back into the params API —
 * the hook runs under the table lock (reentrant set → deadlock). */
typedef int (*robotos_param_set_cb_t)(
    const char *name,
    int value_type,
    const char *new_value,
    const char *old_value,
    void *user_data);
ROBOTOS_API robotos_status_t robotos_param_on_set(
    robotos_node_t *node,
    robotos_param_set_cb_t cb,
    void *user_data);

/* ---------------- Lifecycle (v0.2, ADR 0012) --------------------*/

/* Stable + transient states; wire-identical to
 * robotos.lifecycle.v1.LifecycleState. */
typedef enum robotos_lifecycle_state {
    ROBOTOS_LIFECYCLE_UNSPECIFIED  = 0,
    ROBOTOS_LIFECYCLE_CREATED      = 1,
    ROBOTOS_LIFECYCLE_INACTIVE     = 2,
    ROBOTOS_LIFECYCLE_ACTIVE       = 3,
    ROBOTOS_LIFECYCLE_FINALIZED    = 4,
    ROBOTOS_LIFECYCLE_ERROR        = 5,
    ROBOTOS_LIFECYCLE_CONFIGURING  = 10,
    ROBOTOS_LIFECYCLE_ACTIVATING   = 11,
    ROBOTOS_LIFECYCLE_DEACTIVATING = 12,
    ROBOTOS_LIFECYCLE_CLEANING_UP  = 13,
    ROBOTOS_LIFECYCLE_SHUTTING_DOWN= 14
} robotos_lifecycle_state_t;

/* Current state. Returns ROBOTOS_LIFECYCLE_FINALIZED for NULL or
 * destroyed nodes. */
ROBOTOS_API robotos_lifecycle_state_t
robotos_lifecycle_get(robotos_node_t *node);

/* Local transitions. ROBOTOS_OK on success;
 * ROBOTOS_INVALID_STATE for illegal transitions or unmanaged
 * (auto-active) nodes. */
ROBOTOS_API robotos_status_t robotos_lifecycle_configure(robotos_node_t *node);
ROBOTOS_API robotos_status_t robotos_lifecycle_activate(robotos_node_t *node);
ROBOTOS_API robotos_status_t robotos_lifecycle_deactivate(robotos_node_t *node);
ROBOTOS_API robotos_status_t robotos_lifecycle_cleanup(robotos_node_t *node);

/* Opt in/out of remote lifecycle `set` — off by default. */
ROBOTOS_API void robotos_lifecycle_allow_remote(robotos_node_t *node, int allow);

/* Transition hooks (ADR 0012). Registered before the transition runs;
 * the hook executes inside it — nonzero return fails the transition
 * and the node enters Error (recover via robotos_lifecycle_cleanup).
 * Must not block or re-enter the lifecycle API. */
#define ROBOTOS_LC_ON_CONFIGURE  0
#define ROBOTOS_LC_ON_ACTIVATE   1
#define ROBOTOS_LC_ON_DEACTIVATE 2
#define ROBOTOS_LC_ON_CLEANUP    3
typedef int (*robotos_lifecycle_cb_t)(void *user_data);
ROBOTOS_API robotos_status_t robotos_lifecycle_on(
    robotos_node_t *node,
    int which,
    robotos_lifecycle_cb_t cb,
    void *user_data);

/* ---------- tracing (TRACE-001) ---------- */

/* Enable/disable /{uuid}/_trace event publishing on this node. */
ROBOTOS_API robotos_status_t
robotos_node_set_tracing(robotos_node_t *node, int on);

/* ---------- .rbag record/replay (BAG-01) ---------- */

typedef struct robotos_recorder robotos_recorder_t;

/* Start recording comma-separated `topics` to `path`.
 * Returns a recorder handle; the bag is finalized by
 * robotos_recorder_stop() (or destroy as a fallback). */
ROBOTOS_API robotos_status_t robotos_recorder_create(
    robotos_node_t *node,
    const char *topics_csv,
    const char *path,
    const char *label,
    robotos_recorder_t **out_recorder);

ROBOTOS_API uint64_t robotos_recorder_count(robotos_recorder_t *recorder);
ROBOTOS_API robotos_status_t robotos_recorder_stop(robotos_recorder_t *recorder);
ROBOTOS_API void robotos_recorder_destroy(robotos_recorder_t *recorder);

typedef struct {
    uint64_t published;
    uint64_t skipped_command;
    uint64_t skipped_filter;
    uint64_t failed;
} robotos_replay_report_t;

/* Replay a bag file. `rate` scales pacing (0 or 1.0 = real-time);
 * `topics_csv`/`prefix` may be NULL. Command-shaped topics are
 * skipped unless `allow_command_topics` is set. */
ROBOTOS_API robotos_status_t robotos_replay(
    robotos_node_t *node,
    const char *path,
    double rate,
    int allow_command_topics,
    const char *topics_csv,
    const char *prefix,
    robotos_replay_report_t *out_report);

/* Bag metadata as a JSON string into the caller buffer. */
ROBOTOS_API robotos_status_t robotos_bag_info(
    const char *path, char *buf, size_t capacity, size_t *out_len);

/* ---------------- Actions (ACT-01) ---------------------------*/

/* Goal lifecycle states — wire-identical to
 * robotos.action.v1.GoalStatus. */
typedef enum robotos_goal_status {
    ROBOTOS_GOAL_UNSPECIFIED = 0,
    ROBOTOS_GOAL_PENDING   = 1,
    ROBOTOS_GOAL_ACCEPTED  = 2,
    ROBOTOS_GOAL_EXECUTING = 3,
    ROBOTOS_GOAL_CANCELING = 4,
    ROBOTOS_GOAL_SUCCEEDED = 5,
    ROBOTOS_GOAL_CANCELED  = 6,
    ROBOTOS_GOAL_ABORTED   = 7,
    ROBOTOS_GOAL_REJECTED  = 8
} robotos_goal_status_t;

typedef struct robotos_action_server robotos_action_server_t;
typedef struct robotos_action_client robotos_action_client_t;

/* Opaque per-goal context — valid only inside the handler call. */
typedef struct robotos_goal_ctx robotos_goal_ctx_t;

/* Goal handler — same contract as robotos_service_handler_t but for
 * long-running goals: runs on a robotos worker thread off the async
 * runtime, so blocking work is expected. `goal_ctx` supports
 * robotos_goal_cancel_requested / robotos_goal_send_feedback.
 * Write the result into result_buf (cap ROBOTOS_MAX_RPC_PAYLOAD) and
 * set *result_len_out. ROBOTOS_OK → SUCCEEDED; other → ABORTED (or
 * CANCELED if a cancel was requested mid-run). `goal_data`,
 * `goal_ctx`, and buffers are valid only for the call. */
typedef robotos_status_t (*robotos_action_handler_t)(
    const uint8_t *goal_data,
    size_t goal_len,
    robotos_goal_ctx_t *goal_ctx,
    uint8_t *result_buf,
    size_t result_cap,
    size_t *result_len_out,
    void *user_data);

/* Inside a goal handler: 1 once a cancel has been requested —
 * the handler should wind down promptly. */
ROBOTOS_API int robotos_goal_cancel_requested(const robotos_goal_ctx_t *ctx);

/* Inside a goal handler: publish progress bytes on {name}/_feedback
 * (best-effort, like a topic publish). */
ROBOTOS_API robotos_status_t robotos_goal_send_feedback(
    robotos_goal_ctx_t *ctx, const uint8_t *data, size_t len);

/* Declare an action on `name` (e.g. "/act/move"). The same name
 * serves {name}/send_goal|cancel_goal|get_result plus the
 * _feedback/_status topics. */
ROBOTOS_API robotos_status_t robotos_action_server_create(
    robotos_node_t *node,
    const char *name,
    robotos_action_handler_t handler,
    void *user_data,
    robotos_action_server_t **out_server);

/* Stop serving goals and wait for in-flight goals to finish —
 * `handler`/`user_data` are never touched after return. */
ROBOTOS_API void robotos_action_server_destroy(robotos_action_server_t *server);

/* Connect to an action; subscribes to {name}/_feedback eagerly so
 * early feedback isn't missed. */
ROBOTOS_API robotos_status_t robotos_action_client_create(
    robotos_node_t *node,
    const char *name,
    robotos_action_client_t **out_client);

ROBOTOS_API void robotos_action_client_destroy(robotos_action_client_t *client);

/* Send a goal. On ROBOTOS_OK the goal UUID is NUL-terminated into
 * goal_id_buf; *out_len = string length (ROBOTOS_PAYLOAD_TOO_LARGE →
 * required size in *out_len). ROBOTOS_INVALID_ARGUMENT = rejected. */
ROBOTOS_API robotos_status_t robotos_action_send_goal(
    robotos_action_client_t *client,
    const uint8_t *goal_data,
    size_t goal_len,
    uint32_t timeout_ms,
    char *goal_id_buf,
    size_t goal_id_cap,
    size_t *out_len);

/* Request cancellation (advisory — a terminal goal keeps its state).
 * *out_state = server-reported status (e.g. ROBOTOS_GOAL_CANCELING). */
ROBOTOS_API robotos_status_t robotos_action_cancel(
    robotos_action_client_t *client,
    const char *goal_id,
    uint32_t timeout_ms,
    robotos_goal_status_t *out_state);

/* Block until the goal reaches a terminal state or timeout.
 * *out_state = final status; on ROBOTOS_GOAL_SUCCEEDED `out_result`
 * holds the result bytes — free with robotos_message_free. */
ROBOTOS_API robotos_status_t robotos_action_result(
    robotos_action_client_t *client,
    const char *goal_id,
    uint32_t timeout_ms,
    robotos_goal_status_t *out_state,
    robotos_message_t *out_result);

/* Receive the next feedback for `goal_id` (required — other goals'
 * feedback is filtered out). On timeout returns ROBOTOS_TIMEOUT
 * with an empty out_feedback. */
ROBOTOS_API robotos_status_t robotos_action_feedback_recv(
    robotos_action_client_t *client,
    const char *goal_id,
    uint32_t timeout_ms,
    robotos_message_t *out_feedback);

/* ---------- presence (zenoh liveliness) ---------- */

/* Watch boards (or any liveliness tokens) under a keyexpr like
 * "robotos/0/presence/*". Presence keys are raw zenoh key
 * expressions, NOT domain topics. Requires a zenoh transport —
 * other transports return CONFIG error.
 *
 * Events fire on a robotos-managed worker thread — same contract
 * as robotos_message_callback_t: do not call robotos functions
 * reentrantly from the callback. */

typedef enum robotos_presence_state {
    ROBOTOS_PRESENCE_DOWN = 0,
    ROBOTOS_PRESENCE_UP = 1,
} robotos_presence_state_t;

typedef void (*robotos_presence_callback_t)(
    const char *keyexpr,
    robotos_presence_state_t state,
    void *user_data);

typedef struct robotos_presence_watch robotos_presence_watch_t;

/* One-shot query: invokes `cb` once per alive token (UP) on the
 * caller's thread, then writes the count to `out_count` (may be
 * NULL). `cb` is required (it's the result channel). */
ROBOTOS_API robotos_status_t robotos_presence_get(
    robotos_node_t *node,
    const char *keyexpr,
    robotos_presence_callback_t cb,
    void *user_data,
    size_t *out_count);

/* Watch UP/DOWN events under `keyexpr`; replays tokens alive at
 * subscribe time before streaming changes. `cb` fires on a
 * robotos worker thread. */
ROBOTOS_API robotos_status_t robotos_presence_watch(
    robotos_node_t *node,
    const char *keyexpr,
    robotos_presence_callback_t cb,
    void *user_data,
    robotos_presence_watch_t **out_watch);

/* Cancels the watch and joins its task — after return, `user_data`
 * is no longer referenced and may be freed. NULL is a no-op. */
ROBOTOS_API void robotos_presence_watch_destroy(
    robotos_presence_watch_t *watch);

typedef struct robotos_presence_token robotos_presence_token_t;

/* Declare this node present under `keyexpr` — a session-backed
 * liveliness token, so the declaration dies WITH the transport (it
 * can never go stale). Hold the handle while the node should be
 * discoverable; destroy to withdraw early. */
ROBOTOS_API robotos_status_t robotos_presence_declare(
    robotos_node_t *node,
    const char *keyexpr,
    robotos_presence_token_t **out_token);

/* Withdraws the declaration. NULL is a no-op. */
ROBOTOS_API void robotos_presence_token_destroy(
    robotos_presence_token_t *token);

#ifdef __cplusplus
}
#endif
#endif /* ROBOTOS_H */
