
# 🚇 Tokyo Subway Pathfinder

Ứng dụng tìm đường tàu điện ngầm Tokyo với A* pathfinding, hệ thống giá vé dựa theo khoảng cách, và hỗ trợ hai ngôn ngữ Nhật-Anh.

## 📋 Tổng quan

**Tokyo Subway Pathfinder** gồm 2 thành phần:
- **Backend**: FastAPI REST API
- **Frontend**: Streamlit Web UI

```
┌─────────────────────────────────────────────────────────────┐
│           Tokyo Subway Pathfinder (Web Browser)             │
├─────────────────────────────────────────────────────────────┤
│ Frontend (Streamlit - frontend.py)                          │
│  • Giao diện người dùng tương tác                           │
│  • Bản đồ folium 🗺️ (tiếng Nhật/Anh)                      │
│  • Đăng nhập/Quản trị                                       │
│  • Hiển thị kết quả tìm đường                               │
├─────────────────────────────────────────────────────────────┤
│                    HTTP Requests                            │
├─────────────────────────────────────────────────────────────┤
│ Backend (FastAPI - app/main.py)                             │
│  • REST API endpoints                                       │
│  • Xác thực (JWT)                                          │
│  • A* pathfinding algorithm                                 │
│  • Quản lý ga/tuyến/đoạn đường                            │
│  • Tính giá vé (distance-based)                             │
├─────────────────────────────────────────────────────────────┤
│                 PostgreSQL Database                         │
│  • tables: stations, lines, edges, users                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Cách chạy ứng dụng

### Prerequisites

```bash
pip install -r requirements.txt
```

### 1️⃣ Khởi động Backend (FastAPI)

```bash
cd tìm đường tàu_backend_2
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

✅ Backend sẽ chạy tại: `http://127.0.0.1:8000`

**API Documentation (Swagger UI)**: `http://127.0.0.1:8000/docs`

### 2️⃣ Khởi động Frontend (Streamlit)

Mở **terminal mới** và chạy:

```bash
cd tìm đường tàu_backend_2
streamlit run frontend.py
```

✅ Frontend sẽ mở tự động tại: `http://localhost:8501`

---

## 🏗️ Kiến trúc

### Backend (FastAPI)

**Trách nhiệm:**
- Xử lý logic pathfinding (A* algorithm)
- Quản lý dữ liệu (ga, tuyến, người dùng)
- Tính giá vé dựa theo khoảng cách
- Xác thực JWT
- Admin controls (chặn/mở ga, tuyến)

**Cấu trúc:**
```
app/
├── main.py                 # FastAPI app initialization
├── api/
│   ├── auth.py            # 🔐 Đăng ký/đăng nhập
│   ├── pathfinding.py     # 🗺️ Tìm đường
│   ├── stations.py        # 🚉 Danh sách ga
│   └── admin.py           # 🛠️ Quản lý
├── core/
│   ├── config.py          # ⚙️ Config & DB URL
│   ├── database.py        # 🔌 SQLAlchemy setup
│   └── security.py        # 🔐 JWT & bcrypt
├── models/
│   ├── user.py            # 👤 User model
│   └── subway.py          # 🚄 Line, Station, Edge models
├── schemas/
│   ├── auth.py            # Request/Response schemas
│   ├── pathfinding.py     # PathRequest, PathResponse
│   └── admin.py           # Admin request schemas
└── service/
    └── pathfinding_service.py  # 🧠 A* + fare calc
```

### Frontend (Streamlit)

**Trách nhiệm:**
- Hiển thị giao diện web
- Quản lý đăng nhập người dùng
- Vẽ bản đồ tương tác (folium)
- Gọi API backend để tìm đường
- Quản trị admin (chặn/mở ga)

**Tính năng:**
```
frontend.py
├── 🔐 Đăng nhập (Sidebar)
├── 🔍 Tab 1: Tìm đường & Bản đồ
│   ├── 🔄 Nút chuyển ngôn ngữ (Nhật ↔ Anh)
│   ├── 🗺️ Bản đồ folium (CartoDB/OpenStreetMap)
│   ├── 📍 Chọn điểm đi/đến bằng click
│   ├── ⚙️ Ưu tiên (distance/transfers)
│   ├── 👤 Loại hành khách (adult/child)
│   ├── 💰 Hiển thị giá vé & khoảng cách
│   └── 📄 Chi tiết các chặng
└── 🛠️ Tab 2: Quản trị (Admin only)
    ├── 🚫 Chặn/Mở ga
    └── 🚫 Chặn/Mở tuyến
```

---

## 📡 API Endpoints (Input/Output Chi tiết)

### 🔐 Xác thực (Auth)

#### `POST /api/auth/register`
**INPUT (Request Body - JSON):**
```json
{
  "username": "string (2-50 chars)",
  "password": "string (6+ chars)"
}
```

**OUTPUT (Response - 200 OK):**
```json
{
  "username": "string",
  "role": "string (user|admin)"
}
```

**Errors:**
- `400`: Username hoặc password không hợp lệ
- `409`: Username đã tồn tại

---

#### `POST /api/auth/login`
**INPUT (Form Data):**
```
Content-Type: application/x-www-form-urlencoded

username=string
password=string
```

**OUTPUT (Response - 200 OK):**
```json
{
  "access_token": "string (JWT token)",
  "token_type": "string (bearer)",
  "role": "string (user|admin)"
}
```

**Errors:**
- `401`: Sai username hoặc password

---

### 🗺️ Tìm đường (Pathfinding)

#### `POST /api/path/find`
**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**INPUT (Request Body - JSON):**
```json
{
  "origin_lat": "float (latitude -90 to 90)",
  "origin_lon": "float (longitude -180 to 180)",
  "dest_lat": "float (latitude -90 to 90)",
  "dest_lon": "float (longitude -180 to 180)",
  "priority": "enum (distance|transfers)",
  "user_type": "enum (adult|child)"
}
```

**Field Details:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| origin_lat | float | ✅ | Vĩ độ điểm đi |
| origin_lon | float | ✅ | Kinh độ điểm đi |
| dest_lat | float | ✅ | Vĩ độ điểm đến |
| dest_lon | float | ✅ | Kinh độ điểm đến |
| priority | enum | ✅ | `"distance"` hoặc `"transfers"` |
| user_type | enum | ✅ | `"adult"` hoặc `"child"` (child = 50% giá) |

**OUTPUT (Response - 200 OK):**
```json
{
  "origin_station": "string (tên ga điểm đi)",
  "dest_station": "string (tên ga điểm đến)",
  "total_distance_km": "float (km)",
  "total_cost_yen": "integer (yen)",
  "total_transfers": "integer (số lần đổi tàu)",
  "steps": [
    {
      "from_station": "string",
      "to_station": "string",
      "line_name": "string (tên tuyến)",
      "line_color": "string (hex color #RRGGBB)",
      "distance_km": "float",
      "fare_yen": "integer",
      "from_lat": "float",
      "from_lon": "float",
      "to_lat": "float",
      "to_lon": "float",
      "is_transfer": "boolean"
    }
  ]
}
```

**Field Details (Response):**
| Field | Type | Description |
|-------|------|-------------|
| origin_station | string | Tên ga gần nhất với điểm đi |
| dest_station | string | Tên ga gần nhất với điểm đến |
| total_distance_km | float | Tổng khoảng cách toàn bộ route |
| total_cost_yen | integer | Tổng giá vé (tính theo fare tier) |
| total_transfers | integer | Số lần phải đổi tàu |
| steps | array | Chi tiết từng chặng |

**Step Details:**
| Field | Type | Description |
|-------|------|-------------|
| from_station | string | Tên ga khởi hành |
| to_station | string | Tên ga đích chặng này |
| line_name | string | Tên tuyến (ví dụ: "Ginza Line") |
| line_color | string | Màu tuyến (#RRGGBB) |
| distance_km | float | Khoảng cách chặng này |
| fare_yen | integer | Giá vé chặng này |
| from_lat/lon | float | Tọa độ ga đi |
| to_lat/lon | float | Tọa độ ga đến |
| is_transfer | boolean | True nếu là chuyển tuyến |

**Example Response:**
```json
{
  "origin_station": "Shibuya",
  "dest_station": "Shinjuku",
  "total_distance_km": 2.5,
  "total_cost_yen": 180,
  "total_transfers": 1,
  "steps": [
    {
      "from_station": "Shibuya",
      "to_station": "Meiji-Jingu Mae",
      "line_name": "Omotesando Line",
      "line_color": "#0066CC",
      "distance_km": 1.2,
      "fare_yen": 90,
      "from_lat": 35.6595,
      "from_lon": 139.7004,
      "to_lat": 35.6631,
      "to_lon": 139.6999,
      "is_transfer": false
    },
    {
      "from_station": "Meiji-Jingu Mae",
      "to_station": "Shinjuku",
      "line_name": "Marunouchi Line",
      "line_color": "#DC241F",
      "distance_km": 1.3,
      "fare_yen": 90,
      "from_lat": 35.6631,
      "from_lon": 139.6999,
      "to_lat": 35.6896,
      "to_lon": 139.7007,
      "is_transfer": true
    }
  ]
}
```

**Errors:**
- `401`: Không có JWT token hoặc token không hợp lệ
- `400`: Tọa độ không hợp lệ
- `404`: Không tìm thấy đường đi

---

### 🚉 Ga (Stations)

#### `GET /api/stations/`
**Headers:**
```
Authorization: Bearer <access_token> (optional)
```

**INPUT:** Không có

**OUTPUT (Response - 200 OK):**
```json
[
  {
    "station_id": "integer",
    "station_name": "string",
    "latitude": "float",
    "longitude": "float",
    "is_active": "boolean"
  }
]
```

**Field Details:**
| Field | Type | Description |
|-------|------|-------------|
| station_id | integer | ID duy nhất ga |
| station_name | string | Tên ga (tiếng Nhật) |
| latitude | float | Vĩ độ |
| longitude | float | Kinh độ |
| is_active | boolean | Ga có đang hoạt động không |

---

#### `GET /api/stations/lines`
**Headers:**
```
Authorization: Bearer <access_token> (optional)
```

**INPUT:** Không có

**OUTPUT (Response - 200 OK):**
```json
[
  {
    "line_id": "string",
    "line_name": "string",
    "color": "string (#RRGGBB)",
    "is_active": "boolean"
  }
]
```

**Field Details:**
| Field | Type | Description |
|-------|------|-------------|
| line_id | string | Mã tuyến (ví dụ: "G", "M") |
| line_name | string | Tên tuyến đầy đủ |
| color | string | Màu đại diện (#RRGGBB) |
| is_active | boolean | Tuyến có hoạt động không |

---

#### `GET /api/stations/edges`
**Headers:**
```
Authorization: Bearer <access_token> (optional)
```

**INPUT:** Không có

**OUTPUT (Response - 200 OK):**
```json
[
  {
    "edge_id": "integer",
    "source_id": "integer",
    "target_id": "integer",
    "distance_km": "float",
    "fare_yen": "integer",
    "is_transfer": "boolean",
    "is_active": "boolean"
  }
]
```

**Field Details:**
| Field | Type | Description |
|-------|------|-------------|
| edge_id | integer | ID duy nhất đoạn đường |
| source_id | integer | ID ga khởi hành |
| target_id | integer | ID ga đích |
| distance_km | float | Khoảng cách (km) |
| fare_yen | integer | Giá vé (yen) |
| is_transfer | boolean | Là điểm đổi tuyến không |
| is_active | boolean | Đoạn đường hoạt động không |

---

#### `GET /api/stations/nearest?lat={lat}&lon={lon}`
**Headers:**
```
Authorization: Bearer <access_token> (optional)
```

**INPUT (Query Parameters):**
```
lat: float (vĩ độ)
lon: float (kinh độ)
```

**OUTPUT (Response - 200 OK):**
```json
{
  "station_id": "integer",
  "station_name": "string",
  "latitude": "float",
  "longitude": "float",
  "distance_m": "float (khoảng cách tính bằng meter)"
}
```

---

### 🛠️ Quản trị (Admin)

#### `POST /api/admin/station/ban`
**Headers:**
```
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**INPUT (Request Body - JSON):**
```json
{
  "station_id": "integer"
}
```

**OUTPUT (Response - 200 OK):**
```json
{
  "message": "string",
  "status": "success"
}
```

---

#### `POST /api/admin/station/unban`
**Headers:**
```
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**INPUT (Request Body - JSON):**
```json
{
  "station_id": "integer"
}
```

**OUTPUT (Response - 200 OK):**
```json
{
  "message": "string",
  "status": "success"
}
```

---

#### `POST /api/admin/line/ban`
**Headers:**
```
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**INPUT (Request Body - JSON):**
```json
{
  "line_id": "string"
}
```

**OUTPUT (Response - 200 OK):**
```json
{
  "message": "string",
  "status": "success"
}
```

---

#### `POST /api/admin/line/unban`
**Headers:**
```
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**INPUT (Request Body - JSON):**
```json
{
  "line_id": "string"
}
```

**OUTPUT (Response - 200 OK):**
```json
{
  "message": "string",
  "status": "success"
}
```

---

#### `GET /api/admin/banned/stations`
**Headers:**
```
Authorization: Bearer <admin_token>
```

**INPUT:** Không có

**OUTPUT (Response - 200 OK):**
```json
[
  {
    "station_id": "integer",
    "station_name": "string"
  }
]
```

---

#### `GET /api/admin/banned/lines`
**Headers:**
```
Authorization: Bearer <admin_token>
```

**INPUT:** Không có

**OUTPUT (Response - 200 OK):**
```json
[
  {
    "line_id": "string",
    "line_name": "string"
  }
]
```

---

#### `GET /api/admin/banned/edges`
**Headers:**
```
Authorization: Bearer <admin_token>
```

**INPUT:** Không có

**OUTPUT (Response - 200 OK):**
```json
[
  {
    "edge_id": "integer",
    "source_id": "integer",
    "target_id": "integer"
  }
]
```

---

## 💾 Database

PostgreSQL - `tokyo_subway`

**Tables:**
```sql
-- Users
users (user_id, username, password_hash, role, is_active)

-- Stations
stations (station_id, station_name, latitude, longitude, is_active)

-- Lines
lines (line_id, line_name, color, is_active)

-- Edges (connections between stations)
edges (edge_id, source_id, target_id, distance_km, fare_yen, is_transfer, is_active)
```

---

## 🧮 Fare Calculation

**Distance-based pricing:**
```
Distance Range    | Adult Price | Child Price (50%)
1-6 km           | 180 ¥       | 90 ¥
7-11 km          | 210 ¥       | 105 ¥
12-19 km         | 260 ¥       | 130 ¥
20-27 km         | 300 ¥       | 150 ¥
28-40 km         | 330 ¥       | 165 ¥
```

**Child fare = Adult fare × 0.5** (rounded)

---

## 🤖 Pathfinding Algorithm

**A* Search with Haversine Heuristic**

```python
# Heuristic: Straight-line distance to destination
heuristic = haversine_distance(current, destination)

# Cost: Total distance traveled so far
g_cost = total_distance_from_start

# F-score: g + h (prioritizes closer nodes)
f_score = g_cost + heuristic

# Algorithm: Expand nodes with lowest f_score first
```

**Đặc điểm:**
- ✅ Tối ưu và đầy đủ
- ✅ Nhanh hơn Dijkstra
- ✅ Sử dụng Haversine distance (km)
- ✅ Hỗ trợ prioritize: distance hoặc transfers

---

## 🎨 Frontend Features

### 🗺️ Map Controls
- **Click để chọn điểm**: Chọn "Điểm đi" hoặc "Điểm đến" rồi click trên bản đồ
- **Phóng to/ra**: Scroll chuột để zoom
- **Chuyển ngôn ngữ**: Nút 🔄 để đổi giữa tiếng Nhật ↔ Tiếng Anh

### 🚇 Stations Display
- Tất cả ga được hiển thị dưới dạng icon
- Hover để xem tên ga
- Click để xem chi tiết

### 📊 Route Details
```
✅ Kết quả
📍 2.5 km | 💰 180 ¥ | 🔄 1 lần đổi tàu

📄 Chi tiết các chặng (expandable)
  1. 🚩 Shibuya → Meiji-Jingu Mae
     🚇 Omotesando Line | 📏 1.2 km | 💵 90 ¥
  2. 🚩 Meiji-Jingu Mae → Shinjuku
     🚇 Marunouchi Line | 📏 1.3 km | 💵 90 ¥
```

---

## 🔑 Credentials

**Default Test Account:**
```
Username: admin
Password: admin123
Role: admin
```

**Create new users:**
```bash
# POST /api/auth/register
curl -X POST "http://127.0.0.1:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'
```

---

## 📝 Dependencies

```
fastapi==0.111.0
sqlalchemy==2.0.0
psycopg2-binary==2.9.0
python-jose==3.3.0
passlib==1.7.4
bcrypt==4.1.2
streamlit==1.32.0
folium==0.14.0
streamlit-folium==0.20.0
requests==2.32.0
```

---

## 🛠️ Troubleshooting

**❌ Backend không kết nối được:**
```bash
# Kiểm tra DATABASE_URL trong app/core/config.py
# Mặc định: postgresql://postgres:1234@localhost:5432/tokyo_subway

# Kiểm tra PostgreSQL đang chạy
psql -U postgres
```

**❌ Frontend không kết nối được Backend:**
```bash
# Kiểm tra API_BASE trong frontend.py
API_BASE = "http://127.0.0.1:8000/api"

# Verify backend đang chạy tại port 8000
curl http://127.0.0.1:8000/docs
```

**❌ Map không hiển thị:**
- Kiểm tra folium & streamlit-folium đã install
- Clear Streamlit cache: `streamlit cache clear`

---

## 📚 Nguồn tham khảo

- [FastAPI](https://fastapi.tiangolo.com/)
- [Streamlit](https://streamlit.io/)
- [Folium](https://python-visualization.github.io/folium/)
- [A* Algorithm](https://en.wikipedia.org/wiki/A*_search_algorithm)
- [Haversine Formula](https://en.wikipedia.org/wiki/Haversine_formula)

---

**Tác giả**: Tokyo Subway Pathfinder Team  
**Version**: 2.0 (A* + Fare System + Dual Language)  
**Last Updated**: 2026-04-19
