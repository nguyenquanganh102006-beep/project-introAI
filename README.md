
# Tokyo Subway Pathfinder API

Dự án này là backend cho dịch vụ tìm đường tàu điện ngầm Tokyo, xây dựng bằng FastAPI và PostgreSQL. Hệ thống cung cấp xác thực người dùng, quản lý ga/tuyến/đoạn đường, và tìm đường tối ưu dựa trên thuật toán Dijkstra.

## Tổng quan

- `app/main.py`: Khởi tạo ứng dụng FastAPI.
- `app/api/`: Định nghĩa các endpoint REST cho xác thực, tìm đường, dữ liệu ga và chức năng quản trị.
- `app/core/`: Cấu hình, kết nối cơ sở dữ liệu và các tiện ích bảo mật.
- `app/models/`: Các model SQLAlchemy cho người dùng, ga, tuyến, đoạn đường.
- `app/schemas/`: Các schema Pydantic cho request/response.
- `app/service/pathfinding_service.py`: Xử lý logic tìm đường, tìm ga gần nhất và xây dựng đồ thị trọng số.

## Tính năng

- Đăng ký, đăng nhập người dùng với JWT.
- Tìm ga gần nhất theo toạ độ lat/lon.
- Tìm đường giữa hai điểm trên bản đồ với các ưu tiên:
  - `time` (thời gian)
  - `cost` (chi phí)
  - `distance` (khoảng cách)
  - Trả về các bước đi và tổng hợp kết quả.

## Các endpoint API

### Xác thực (Auth)

- `POST /api/auth/register`
  - Body: `username`, `password`
  - Đăng ký tài khoản mới.

- `POST /api/auth/login`
  - Dữ liệu form OAuth2: `username`, `password`
  - Trả về `access_token`, `token_type`, `role`

### Tìm đường (Pathfinding)

- `POST /api/path/find`
  - Yêu cầu phải có bearer token.
  - Body:
    - `origin_lat`
    - `origin_lon`
    - `dest_lat`
    - `dest_lon`
    - `priority` (`time`, `cost`, `distance`, `transfers`)
  - Phản hồi: chi tiết đường đi gồm `origin_station`, `dest_station`, các bước đi, tổng hợp và ưu tiên đã chọn.

### Ga, tuyến, đoạn đường (Stations)

- `GET /api/stations/`
  - Lấy danh sách tất cả các ga đang hoạt động.
- `GET /api/stations/lines`
  - Lấy danh sách tất cả các tuyến.
- `GET /api/stations/edges`
  - Lấy danh sách các đoạn đường đang hoạt động.
- `GET /api/stations/nearest?lat=<lat>&lon=<lon>`
  - Tìm ga gần nhất với toạ độ truyền vào.

### Quản trị (Admin)

- `POST /api/admin/station/ban`
- `POST /api/admin/station/unban`
- `POST /api/admin/line/ban`
- `POST /api/admin/line/unban`
- `POST /api/admin/edge/ban`
- `POST /api/admin/edge/unban`
- `GET /api/admin/banned/stations`
- `GET /api/admin/banned/lines`
- `GET /api/admin/banned/edges`

> Tất cả các endpoint quản trị yêu cầu tài khoản admin đã xác thực (bearer token).

## Lưu ý

- Tìm đường sẽ bỏ qua các ga và đoạn đường bị khoá.
- Khi khoá tuyến, các ga thuộc tuyến đó cũng sẽ bị khoá.
- Mật khẩu được băm bằng `bcrypt`, token sử dụng `HS256`.
- Thuật toán tìm đường hiện tại là Dijkstra trên đồ thị vô hướng.

## Danh sách file mã nguồn chính

- `app/main.py`
- `app/api/auth.py`
- `app/api/pathfinding.py`
- `app/api/admin.py`
- `app/api/stations.py`
- `app/core/config.py`
- `app/core/database.py`
- `app/core/security.py`
- `app/models/user.py`
- `app/models/subway.py`
- `app/schemas/auth.py`
- `app/schemas/pathfinding.py`
- `app/schemas/admin.py`
- `app/service/pathfinding_service.py`

### Models

- `app/models/user.py`: Model `User` với `username`, `password`, `role`, `is_active`.
- `app/models/subway.py`: Model `Line`, `Station`, `Edge`.

### Schemas

- `app/schemas/auth.py`: `RegisterRequest`, `LoginResponse`, `UserOut`
- `app/schemas/pathfinding.py`: `Priority`, `PathRequest`, `StepOut`, `PathResponse`
- `app/schemas/admin.py`: `BanStationRequest`, `BanLineRequest`, `BanEdgeRequest`, `StatusResponse`

### Service

- `app/service/pathfinding_service.py`
  - Tìm ga hoạt động gần nhất bằng công thức Haversine.
  - Xây đồ thị từ các đoạn đường và ga còn hoạt động.
  - Chạy Dijkstra để tìm đường tối ưu theo ưu tiên.
  - Trả về các bước đi và tổng hợp kết quả.

## API Endpoints

### Auth

- `POST /api/auth/register`
  - Request body: `username`, `password`
  - Creates a new user.

- `POST /api/auth/login`
  - OAuth2 form data: `username`, `password`
  - Returns `access_token`, `token_type`, `role`

### Pathfinding

- `POST /api/path/find`
  - Requires bearer token.
  - Request body:
    - `origin_lat`
    - `origin_lon`
    - `dest_lat`
    - `dest_lon`
    - `priority` (`time`, `cost`, `distance`, `transfers`)
  - Response: route details including `origin_station`, `dest_station`, `steps`, totals, and selected priority.

### Stations

- `GET /api/stations/`
  - Returns all active stations.
- `GET /api/stations/lines`
  - Returns all lines.
- `GET /api/stations/edges`
  - Returns all active edges.
- `GET /api/stations/nearest?lat=<lat>&lon=<lon>`
  - Returns the nearest active station for given coordinates.

### Admin

- `POST /api/admin/station/ban`
- `POST /api/admin/station/unban`
- `POST /api/admin/line/ban`
- `POST /api/admin/line/unban`
- `POST /api/admin/edge/ban`
- `POST /api/admin/edge/unban`
- `GET /api/admin/banned/stations`
- `GET /api/admin/banned/lines`
- `GET /api/admin/banned/edges`

> All admin endpoints require an authenticated admin user and bearer token.

## Notes

- The route search ignores inactive stations and edges.
- Line bans also mark contained stations as inactive.
- Passwords are hashed with `bcrypt` and tokens use `HS256`.
- The service currently uses Dijkstra on an undirected graph.

## Source Directory

- `app/main.py`
- `app/api/auth.py`
- `app/api/pathfinding.py`
- `app/api/admin.py`
- `app/api/stations.py`
- `app/core/config.py`
- `app/core/database.py`
- `app/core/security.py`
- `app/models/user.py`
- `app/models/subway.py`
- `app/schemas/auth.py`
- `app/schemas/pathfinding.py`
- `app/schemas/admin.py`
- `app/service/pathfinding_service.py`
