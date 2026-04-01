# PostgreSQL Database Specification for Subway Routing Engine

## Rationale & Algorithmic Needs
The A* routing engine requires several key pieces of information dynamically constructed into an in-memory graph to perform extremely fast computations. Instead of querying PostgreSQL per step (which introduces high latency), data is bulk-loaded from these tables on startup or invoked by an Admin. 

The essential data points:
- **Heuristics ($h(n)$)** requires spatial coordinates `(lat, lon)` to calculate remaining direct distance (Haversine formula).
- **Cost calculation ($g(n)$)** requires explicit `distance_km` or `travel_time_sec`.
- **Transfer penalties** require `line_id` metadata on the connection to assess if the passenger is changing subway lines.
- **Dynamic Filtering** requires `id` strings on both stations and connections to temporarily invalidate/disable routing edges due to maintenance or closures.

---

## 1. Table: `stations`

Stores the metadata for each individual subway station. Cannot have duplicate IDs.

| Column Name | Data Type        | Constraints                    | Description |
| ----------- | ---------------- | ------------------------------ | ----------- |
| `id`        | VARCHAR(50)      | PRIMARY KEY                    | Unique identifier (e.g., "S1"). |
| `name`      | VARCHAR(255)     | NOT NULL                       | Human-readable station name. |
| `lat`       | DOUBLE PRECISION | NOT NULL                       | Latitude for Heuristic (Haversine). |
| `lon`       | DOUBLE PRECISION | NOT NULL                       | Longitude for Heuristic (Haversine). |

---

## 2. Table: `lines`

Stores the global line definitions.

| Column Name | Data Type   | Constraints | Description |
| ----------- | ----------- | ----------- | ----------- |
| `id`        | VARCHAR(50) | PRIMARY KEY | Unique identifier for the Subway Line (e.g., "Red", "Blue"). |
| `name`      | VARCHAR(100)| NOT NULL    | Display name of the line. |
| `color_hex` | VARCHAR(7)  |             | UI tracking metric for front-end rendering. |

---

## 3. Table: `connections`

Stores directional edges. Since A* acts on directed graphs, bidirectional tunnels are typically saved as two separate rows in the database (or logically mirrored via a boolean flag in logic, but standard DB tables for graphs prefer explicit edges for varying travel times, e.g., uphill vs downhill).

| Column Name      | Data Type        | Constraints                               | Description |
| ---------------- | ---------------- | ----------------------------------------- | ----------- |
| `id`             | VARCHAR(100)     | PRIMARY KEY                               | Explicit ID for dynamic closure filtering. |
| `from_station_id`| VARCHAR(50)      | NOT NULL, FOREIGN KEY REFERENCES stations(id) | Start node of the edge. |
| `to_station_id`  | VARCHAR(50)      | NOT NULL, FOREIGN KEY REFERENCES stations(id) | End node of the edge. |
| `line_id`        | VARCHAR(50)      | NOT NULL, FOREIGN KEY REFERENCES lines(id)| The subway line facilitating this connection. Used to evaluate transfer penalties (+300s). |
| `distance_km`    | DOUBLE PRECISION | NOT NULL, CHECK (distance_km > 0)         | Exact edge distance. Used when `priority=distance`. |
| `travel_time_sec`| DOUBLE PRECISION | NOT NULL, CHECK (travel_time_sec > 0)     | Base time traversal. Used when `priority=time`. |

### **Indexes**
1. **`idx_connections_from_station`**: BTREE on `from_station_id`. Massively speeds up adjacency list generation queries (`SELECT * FROM connections WHERE from_station_id = ?`).
2. **`idx_connections_line`**: BTREE on `line_id`.

## Future Considerations
If real-life traffic delay or temporary speed restriction configurations are needed, `travel_time_sec` should be periodically updated from a `current_status` override table.
