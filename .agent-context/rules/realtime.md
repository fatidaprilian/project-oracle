# Real-time & WebSockets Architecture

> WebSockets are stateful tcp connections in a stateless HTTP world. Treat them with extreme caution.

## 1. Connection Management & Scaling
WebSockets hold a persistent connection, consuming file descriptors and memory on the server.
- **Rule:** NEVER scale WebSockets using a standard load balancer without sticky sessions (unless utilizing an external Pub/Sub service).
- **Architecture:** Use a dedicated external Pub/Sub layer to broadcast messages across multiple WebSocket server instances.
  - **Standard:** Redis Pub/Sub (Socket.io-redis, any standard Redis adapter).
  - **Enterprise:** NATS, Apache Kafka, or managed services like AWS API Gateway WebSockets / Pusher / Socket.io / Soketi.
- **Goal:** Any user can connect to Server A, and receive a message published by a background job running on Server B.

## 2. Authentication Context
WebSockets cannot rely on traditional HTTP Authorization headers during the handshake in browser environments (as the WebSocket API does not allow setting custom headers).
- **Rule:** Authenticate connections explicitly.
  - **Method A (Cookies):** If the application uses HTTPOnly cookies, authentication happens naturally during the initial HTTP upgrade request.
  - **Method B (Tickets/Tokens):** Pass the JWT or an ephemeral ticket in the connection URL query string (`?token=xyz`) or immediately after connecting via a dedicated `auth` JSON payload.
- **BANNED:** Never trust a client simply because they know the WebSocket URL.

## 3. The "No Business Logic in Sockets" Rule
A WebSocket controller should be treated exactly like an HTTP controller.
- **Rule:** The WebSocket handler's **only** responsibility is parsing the incoming message, validating the payload schema, and routing it to a Service/Application layer orchestrator.
- **BANNED:** Directly writing to databases, executing complex business logic, or calling external APIs directly inside the WebSocket event callback.

## 4. Heartbeats & Dead Connections
TCP connections drop silently (e.g., when a user drives through a tunnel).
- **Rule:** Implement Ping/Pong heartbeats. The server MUST periodically ping the client. If the client fails to respond within the expected window (e.g., 30s), the server MUST forcefully sever the connection to free resources (`ws.terminate()`, not `ws.close()`).

## 5. Event Design & Typing
Treat WebSocket events like a strongly typed REST API.
- **Rule:** Every WebSocket message MUST have a mandatory `type` or `event` field, and a strongly typed `payload` field defined by a schema (e.g., Zod, JSON Schema).
- **BANNED:** Emitting arbitrary strings or untyped JSON objects like `{ user_id: 1, message: "hi" }`.
- **REQUIRED:**
  ```json
  {
    "event": "message.created",
    "payload": {
      "id": "msg_123",
      "text": "Hello World",
      "timestamp": "2026-03-01T12:00:00Z"
    }
  }
  ```

## 6. Rate Limiting & Abuse Prevention
WebSockets are heavily susceptible to DoS attacks because an open connection bypasses traditional WAF rate limiters.
- **Rule:** You MUST implement message rate limiting at the application logic layer (e.g., maximum 5 messages per second per connection/user). Violators should be instantly disconnected and IP-banned temporarily.
