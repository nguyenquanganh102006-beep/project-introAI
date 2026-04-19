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
