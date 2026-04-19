# PostgreSQL Database Specification for Subway Routing Engine

## Rationale & Algorithmic Needs
The A* routing engine requires several key pieces of information dynamically constructed into an in-memory graph to perform extremely fast computations. Instead of querying PostgreSQL per step (which introduces high latency), data is bulk-loaded from these tables on startup or invoked by an Admin. 

The essential data points:
- **Heuristics ($h(n)$)** requires spatial coordinates `(lat, lon)` to calculate remaining direct distance (Haversine formula).
- **Cost calculation ($g(n)$)** requires explicit `distance_km` which also determines standard routing and fare costs.
- **Transfer penalties** require `line_id` on each station and `is_transfer` flag on edges to assess if the passenger is changing subway lines (used for `priority=fewest_transfers`).
- **Dynamic Filtering** requires `station_id` and `edge_id` to temporarily invalidate/disable routing edges due to maintenance or closures.

---

## 1. Table: `stations`

Stores the metadata for each individual subway station. Each station belongs to one subway line.

| Column Name    | Data Type        | Constraints                               | Description |
| -------------- | ---------------- | ----------------------------------------- | ----------- |
| `station_id`   | VARCHAR(20)      | PRIMARY KEY                               | Unique identifier (e.g., "A01", "G05"). |
| `station_name` | VARCHAR(100)     | NOT NULL                                  | Human-readable station name. |
| `line_id`      | VARCHAR(10)      | FOREIGN KEY REFERENCES line(line_id)      | The subway line this station belongs to. |
| `lat`          | DOUBLE PRECISION |                                           | Latitude for Heuristic (Haversine). |
| `lon`          | DOUBLE PRECISION |                                           | Longitude for Heuristic (Haversine). |
| `geom`         | geometry(Point,4326) |                                       | PostGIS geometry column (not used by routing engine). |

---

## 2. Table: `line`

Stores the global line definitions.

| Column Name | Data Type    | Constraints | Description |
| ----------- | ------------ | ----------- | ----------- |
| `line_id`   | VARCHAR(10)  | PRIMARY KEY | Unique identifier for the Subway Line (e.g., "A", "G", "M"). |
| `line_name` | VARCHAR(100) | NOT NULL    | Display name of the line (e.g., "Asakusa Line", "Ginza Line"). |
| `color`     | VARCHAR      |             | Color code for front-end rendering. |

---

## 3. Table: `edges`

Stores directional edges between stations. Bidirectional tunnels are represented as two separate rows. Transfer edges (connecting stations of different lines at the same physical location) have `is_transfer = true` and `distance_km = 0`.

| Column Name   | Data Type        | Constraints                                    | Description |
| ------------- | ---------------- | ---------------------------------------------- | ----------- |
| `edge_id`     | INTEGER          | PRIMARY KEY, AUTO INCREMENT                    | Unique edge identifier for dynamic closure filtering. |
| `source_id`   | VARCHAR(20)      | FOREIGN KEY REFERENCES stations(station_id)    | Start node of the edge. |
| `target_id`   | VARCHAR(20)      | FOREIGN KEY REFERENCES stations(station_id)    | End node of the edge. |
| `distance_km` | DOUBLE PRECISION |                                                | Physical distance of this edge. Controls cost calculations for `shortest_distance` and `lowest_fare`. |
| `time_min`    | DOUBLE PRECISION |                                                | Legacy time field (not used by routing engine, which uses `AVERAGE_VELOCITY`). |
| `fare_yen`    | INTEGER          |                                                | Legacy per-edge fare (not used; fare is calculated from total distance via fare table). |
| `is_transfer` | BOOLEAN          | DEFAULT false                                  | Whether this edge represents a transfer between different subway lines. |
| `is_active`   | BOOLEAN          | DEFAULT true                                   | Whether this edge is currently active. Inactive edges are skipped by the routing engine. |

## Future Considerations
If real-life traffic delays or temporary speed restriction configurations are needed, `AVERAGE_VELOCITY` calculations could be moved from a global environment configuration to a line-specific override table dynamically mapping average train speeds.
