# Subway Routing Engine

## Giới thiệu (Overview)
Subway Routing Engine là một RESTful API hiệu suất cao được xây dựng bằng **FastAPI**, làm nhiệm vụ tính toán các tuyến đường tàu điện ngầm tối ưu dựa trên bài toán khoảng cách, thời gian di chuyển, và số lần chuyển tuyến ít nhất. Hệ thống sử dụng thuật toán **A* (A-star)** để tìm đường đi ngắn nhất một cách linh hoạt, đồng thời xét đến chi phí chuyển tuyến, khoảng cách kết nối, và bộ lọc trạng thái mạng lưới tĩnh tại thời gian thực (ví dụ như ga hoặc tuyến đang đóng cửa bảo trì).

## Công nghệ cốt lõi (Core Technologies)
- **Python 3**
- **FastAPI** & **Uvicorn**: Xây dựng API async nhanh và mạnh mẽ.
- **PostgreSQL** & **SQLAlchemy**: Lưu trữ dữ liệu cấu trúc bản đồ tàu ngầm, các điểm ga (vertices) và các mối nối (edges).
- **GraphManager (In-Memory)**: Mẫu thiết kế Singleton có chức năng tải trước (preload) dữ liệu từ PostgreSQL lên bộ nhớ RAM để đảm bảo thuật toán A* tính toán định tuyến ở độ trễ siêu thấp.
- **Thuật toán A\***: Logic cốt lõi định tuyến kết hợp với tọa độ không gian thực (Vĩ độ / Kinh độ - Lat/Lon) và công thức **Haversine** (Heuristics).

## Các tính năng nổi bật (Features)
- **Coordinate-to-Station Mapping**: Ánh xạ tọa độ Vĩ độ/Kinh độ từ người dùng sang điểm ga tàu điện ngầm gần nhất.
- **Định tuyến đa tiêu chí**: Tối ưu hóa theo `shortest_distance` (khoảng cách ngắn nhất), `lowest_fare` (giá rẻ nhất), hoặc `fewest_transfers` (ít phải chuyển tàu nhất).
- **Lọc đồ thị thời gian thực (Real-time Graph Filtering)**: Quản lý việc `avoid_stations` (tránh ga nào đó), `avoid_connections` (tránh tuyến đường kết nối), cho phép Admin mô phỏng hoặc xử lý đóng cửa ga/tuyến đường đột xuất.
- **Chế độ Admin và User**: Phân tách logic sử dụng cho việc truy vấn chuyến đi dành cho User và can thiệp số liệu cấu hình dành cho Admin (cung cấp sẵn thông qua công cụ `test_interactive.py`).

## Cấu trúc dự án (Project Structure)
- `main.py`: Điểm đầu vào (entry point) của ứng dụng FastAPI. Nơi thiết lập vòng đời ứng dụng (tự động nạp trước dữ liệu Data vào bộ nhớ khi khởi động ứng dụng Server).
- `app/api/`: Các định tuyến API (`router.py`) liên kết các phương thức HTTP REST với Business logic.
- `app/core/`: Bộ não của ứng dụng.
  - `graph_manager.py`: Lớp Singleton lưu trữ và xử lý cấu trúc đồ thị từ Data dưới PostgreSQL để tránh việc truy vấn tới Database trong mọi bước Path-finding.
  - `database.py`, `models.py`: Khởi tạo và thiết lập các Model cơ sở dữ liệu SQLAlchemy.
  - `config.py`: File ánh xạ cấu hình từ biến môi trường.
- `app/services/`: Logic nghiệp vụ (Business logic).
  - `astar_service.py`: Chứa logic thuật toán pathfinding (A*).
- `app/schemas/`: Định nghĩa các cấu trúc Pydantic validation dùng cho Input/Output của API.
- `test_interactive.py`: Phiên bản command-line dùng để tương tác giả lập giữa Admin và User, hỗ trợ cho việc kiểm thử logic thuần túy không cần giao diện web.
- `DB_SPECIFICATION.md`: Đặc tả cấu trúc Database, các logic không gian liên quan và chi tiết cách thuật toán tương tác với các Table.

## Hướng dẫn cài đặt và sử dụng (Getting Started)

### 1. Biến môi trường
Tạo một file `.env` ở thư mục gốc của dự án với ít nhất nội dung về chuỗi kết nối PostgreSQL gốc:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/subway_db
## Ví dụ có thêm các biến tốc độ trung bình
AVERAGE_VELOCITY=30
```

### 2. Cài đặt các thư viện (Requirements)
Sử dụng môi trường ảo hóa (virtual environment) để cài đặt sạch:
```bash
python -m venv venv
venv\Scripts\activate  # Nếu dùng Windows
pip install -r requirements.txt
```

### 3. Chạy Server API trực tiếp
Sử dụng Uvicorn để bắt đầu tiến trình API. Từ Terminal chạy lệnh:
```bash
uvicorn main:app --reload
```
Khi Server khởi động, hệ thống sẽ trigger sự kiện `startup`, ánh xạ các Models, nạp dữ liệu vào Single instance `GraphManager`.
*Note: Swagger UI cho việc Test APIs được tích hợp tự động tại: [http://localhost:8000/docs](http://localhost:8000/docs)*

### 4. Chạy mô phỏng định tuyến tương tác
Sử dụng công cụ Python Console có sẵn để tương tác và xác minh các thuật toán cho User và Admin mà chưa cần gọi HTTP API:
```bash
python test_interactive.py
```

### 5. Chạy giao diện Web (Frontend)
Dự án đi kèm một giao diện tương tác trực quan được xây dựng bằng Streamlit. Để chạy giao diện:

1. Đảm bảo API Backend (Uvicorn) **đang chạy** ở một cửa sổ Terminal (như hướng dẫn ở bước 3).
2. Mở một cửa sổ Terminal khác.
3. Chạy lệnh:
```bash
python -m streamlit run frontend.py
```
*(Hoặc `streamlit run frontend.py`)*

Ngay sau đó trình duyệt web của bạn sẽ tự động mở trang web (mặc định tại `http://localhost:8501`). Tại đây bạn có thể thao tác tìm đường trên bản đồ và đăng nhập quyền Admin để đóng/mở nhà ga trực tiếp.

---

## Tham chiếu biến (Variables Reference)

### 🔧 Biến môi trường (`.env` / `config.py`)

| Tên biến | Mặc định | Tác dụng |
|---|---|---|
| `DATABASE_URL` | *(bắt buộc)* | Chuỗi kết nối PostgreSQL. VD: `postgresql://user:pass@localhost:5432/subway_db` |
| `AVERAGE_VELOCITY` | `100.0` km/h | Tốc độ tàu trung bình, dùng để tính thời gian di chuyển ước tính |
| `ADMIN_USERNAME` | `"admin"` | Tên đăng nhập Admin để gọi các endpoint quản trị |
| `ADMIN_PASSWORD` | `"admin123"` | Mật khẩu Admin |

---

### 📥 Đầu vào API — `RouteRequest` (`POST /v1/route`)

| Tên biến | Kiểu | Tác dụng |
|---|---|---|
| `start_coords.lat` | `float` | Vĩ độ điểm xuất phát |
| `start_coords.lon` | `float` | Kinh độ điểm xuất phát |
| `end_coords.lat` | `float` | Vĩ độ điểm đến |
| `end_coords.lon` | `float` | Kinh độ điểm đến |
| `priority` | `enum` | Tiêu chí tối ưu: `shortest_distance` / `lowest_fare` / `fewest_transfers` |
| `passenger_type` | `enum` | Loại hành khách: `adult` (người lớn) / `child` (trẻ em) — ảnh hưởng giá vé |

---

### 📤 Đầu ra API — `RouteResponse`

| Tên biến | Kiểu | Tác dụng |
|---|---|---|
| `path` | `List[str]` | Danh sách ID các ga theo thứ tự trên tuyến đường tìm được |
| `total_subway_distance` | `float` | Tổng khoảng cách (km) |
| `total_fare` | `int` | Tổng giá vé (VNĐ) |
| `estimated_time_minutes` | `float` | Thời gian di chuyển ước tính (phút) |

---

### 🚫 Quản trị bít mạng lưới — `ClosureRequest` (`POST /v1/admin/closures`)

| Tên biến | Kiểu | Tác dụng |
|---|---|---|
| `closed_stations` | `List[str]` | Danh sách ID các **ga** bị đóng — thuật toán sẽ bỏ qua |
| `closed_edges` | `List[int]` | Danh sách ID các **kết nối** (edge) bị đóng |
| `closed_lines` | `List[str]` | Danh sách ID các **tuyến tàu** bị đóng |

---

### ⚙️ Biến nội bộ thuật toán A\* (`astar_service.py`)

| Tên biến | Tác dụng |
|---|---|
| `open_set` | Hàng đợi ưu tiên (min-heap) chứa các trạng thái cần xét |
| `best_g_scores` | Dict lưu chi phí tốt nhất đã biết cho mỗi `(station_id, line_id)` |
| `g_dist` | Tổng khoảng cách thực tế đã đi từ điểm xuất phát |
| `h_cost` | Chi phí heuristic — khoảng cách Haversine tới đích |
| `f_score` | `g_cost + h_cost` — tổng chi phí ước tính |
| `transfers` | Số lần chuyển tuyến tích lũy |
| `is_transfer` | `true` nếu bước di chuyển hiện tại là chuyển sang tuyến khác |
| `step_dist` | Khoảng cách của cạnh (edge) đang xét (km) |
