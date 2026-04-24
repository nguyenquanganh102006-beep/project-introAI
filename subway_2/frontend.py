import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# --- CẤU HÌNH HỆ THỐNG ---
API_BASE = "http://127.0.0.1:8000/v1"
st.set_page_config(page_title="Tokyo Subway Pathfinder", layout="wide", page_icon="🚇")

# Khởi tạo Session State
if "admin_user" not in st.session_state: st.session_state.admin_user = None
if "admin_pass" not in st.session_state: st.session_state.admin_pass = None
if "is_admin" not in st.session_state: st.session_state.is_admin = False
if "origin" not in st.session_state: st.session_state.origin = [35.6812, 139.7671]
if "dest" not in st.session_state: st.session_state.dest = [35.6586, 139.7454]
if "path_data" not in st.session_state: st.session_state.path_data = None
if "map_lang" not in st.session_state: st.session_state.map_lang = "en"

def get_admin_auth():
    """Trả về tuple (user, pass) cho HTTP Basic Auth của admin."""
    if st.session_state.is_admin:
        return (st.session_state.admin_user, st.session_state.admin_pass)
    return None

def geocode_place(place_query):
    """Đổi tên địa điểm/địa chỉ sang toạ độ lat/lon bằng Nominatim."""
    if not place_query or not place_query.strip():
        return None
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": place_query.strip(), "format": "json", "limit": 1},
            headers={"User-Agent": "tokyo-subway-pathfinder/1.0"},
            timeout=10,
        )
        if response.status_code != 200:
            return None
        items = response.json()
        if not items:
            return None
        top = items[0]
        return {
            "lat": float(top["lat"]),
            "lon": float(top["lon"]),
            "display_name": top.get("display_name", place_query.strip()),
        }
    except (requests.RequestException, ValueError, TypeError, KeyError):
        return None

def draw_routes(m, lang):
    """Vẽ routes trên bản đồ dựa trên path (danh sách tên ga) từ backend."""
    path_data = st.session_state.path_data
    if path_data:
        path = path_data.get("path", [])
        network = st.session_state.get("network_data")

        # Nếu có dữ liệu mạng lưới, vẽ đường nối giữa các ga liên tiếp
        if network and len(path) >= 2:
            station_coords = {s["name"]: (s["lat"], s["lon"]) for s in network.get("stations", [])}
            for i in range(len(path) - 1):
                s_from = path[i]
                s_to = path[i + 1]
                if s_from in station_coords and s_to in station_coords:
                    p1 = list(station_coords[s_from])
                    p2 = list(station_coords[s_to])
                    folium.PolyLine(
                        locations=[p1, p2],
                        color="#2E86C1", weight=6, opacity=0.8,
                        tooltip=f"{s_from} → {s_to}"
                    ).add_to(m)
                    folium.CircleMarker(p1, radius=4, color="white", fill=True, fill_color="#2E86C1").add_to(m)
                    folium.CircleMarker(p2, radius=4, color="white", fill=True, fill_color="#2E86C1").add_to(m)

    folium.Marker(st.session_state.origin, icon=folium.Icon(color="green", icon="play"), tooltip="Điểm đi").add_to(m)
    folium.Marker(st.session_state.dest, icon=folium.Icon(color="red", icon="stop"), tooltip="Điểm đến").add_to(m)
    return m

def create_map(lang):
    """Tạo bản đồ (lang: 'ja' hoặc 'en')"""
    if lang == "en":
        m = folium.Map(location=[35.6895, 139.6917], zoom_start=12, tiles="CartoDB positron")
    else:
        m = folium.Map(location=[35.6895, 139.6917], zoom_start=12)
    return draw_routes(m, lang)

def load_network():
    """Tải dữ liệu mạng lưới từ GET /v1/network để hỗ trợ vẽ bản đồ."""
    try:
        res = requests.get(f"{API_BASE}/network", timeout=10)
        if res.status_code == 200:
            st.session_state.network_data = res.json()
    except requests.RequestException:
        st.session_state.network_data = None

# Tải dữ liệu mạng lưới nếu chưa có hoặc đang bị None (do lần trước lỗi kết nối)
if st.session_state.get("network_data") is None:
    load_network()

# --- LAYOUT CHÍNH ---
left_col, right_col = st.columns([1.0, 2.7], gap="large")

with left_col:
    st.write("### 🎛️ Điều khiển")

    # ---- PHẦN ADMIN LOGIN ----
    if not st.session_state.is_admin:
        with st.expander("🔒 Đăng nhập Admin"):
            admin_u = st.text_input("Username (Admin)", key="admin_login_user")
            admin_p = st.text_input("Password (Admin)", type="password", key="admin_login_pass")
            if st.button("Đăng nhập Admin", use_container_width=True, key="btn_admin_login"):
                if admin_u and admin_p:
                    # Kiểm tra thông tin bằng cách gọi thử endpoint admin
                    try:
                        test_res = requests.get(
                            f"{API_BASE}/admin/closures",
                            auth=(admin_u, admin_p),
                            timeout=5
                        )
                        if test_res.status_code == 200:
                            st.session_state.admin_user = admin_u
                            st.session_state.admin_pass = admin_p
                            st.session_state.is_admin = True
                            st.success("✅ Đăng nhập Admin thành công!")
                            st.rerun()
                        elif test_res.status_code == 401:
                            st.error("❌ Sai tên đăng nhập hoặc mật khẩu!")
                        else:
                            st.error(f"❌ Lỗi kết nối: HTTP {test_res.status_code}")
                    except requests.RequestException as e:
                        st.error(f"❌ Không thể kết nối tới server: {e}")
                else:
                    st.warning("⚠️ Vui lòng nhập tài khoản và mật khẩu!")
        st.info("💡 Chọn điểm đi/đến và nhấn TÌM để tìm lộ trình.")
    else:
        top_col1, top_col2 = st.columns([3, 1])
        with top_col1:
            st.success(f"Đang đăng nhập: ADMIN ({st.session_state.admin_user})")
        with top_col2:
            if st.button("Đăng xuất", use_container_width=True):
                st.session_state.is_admin = False
                st.session_state.admin_user = None
                st.session_state.admin_pass = None
                st.session_state.path_data = None
                st.rerun()

    # ---- CHUYỂN NGÔN NGỮ BẢN ĐỒ ----
    btn_col, info_col = st.columns([0.5, 3])
    with btn_col:
        if st.button("🔄", use_container_width=True, help="Chuyển ngôn ngữ bản đồ"):
            st.session_state.map_lang = "ja" if st.session_state.map_lang == "en" else "en"
            st.rerun()
    with info_col:
        lang_display = "🇬🇧 Tiếng Anh" if st.session_state.map_lang == "en" else "🇯🇵 Tiếng Nhật"
        st.write(f"#### ⚙️ Bản đồ ({lang_display})")

    # ---- NHẬP ĐIỂM ĐI / ĐIỂM ĐẾN ----
    st.write("#### ✍️ Nhập điểm đi / điểm đến")
    in_col1, in_col2 = st.columns(2)
    with in_col1:
        origin_place_input = st.text_input(
            "Điểm đi",
            placeholder="Ví dụ: Tokyo Station",
            key="origin_place_input",
        )
    with in_col2:
        dest_place_input = st.text_input(
            "Điểm đến",
            placeholder="Ví dụ: Shibuya Crossing",
            key="dest_place_input",
        )
    if st.button("📌 Áp dụng địa điểm", use_container_width=True):
        origin_geo = geocode_place(origin_place_input)
        dest_geo = geocode_place(dest_place_input)
        if not origin_geo or not dest_geo:
            st.error("❌ Không tìm thấy một trong hai địa điểm. Hãy nhập rõ hơn hoặc chọn trên bản đồ.")
        else:
            st.session_state.origin = [origin_geo["lat"], origin_geo["lon"]]
            st.session_state.dest = [dest_geo["lat"], dest_geo["lon"]]
            st.session_state.path_data = None
            st.rerun()

    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.caption(f"🟢 {st.session_state.origin[0]:.4f}, {st.session_state.origin[1]:.4f}")
    with col_info2:
        st.caption(f"🔴 {st.session_state.dest[0]:.4f}, {st.session_state.dest[1]:.4f}")

    # ---- THÔNG SỐ TÌM ĐƯỜNG ----
    # priority: "shortest_distance" | "fewest_transfers"  (theo RoutePriority enum)
    # passenger_type: "adult" | "child"  (theo PassengerType enum)
    sel_col1, sel_col2 = st.columns(2)
    with sel_col1:
        prio_label = st.selectbox(
            "Ưu tiên",
            ["Khoảng cách ngắn nhất", "Ít đổi tàu nhất"],
            key="priority_select"
        )
    with sel_col2:
        passenger_label = st.selectbox(
            "Loại hành khách",
            ["Người lớn", "Trẻ em"],
            key="passenger_select"
        )

    # Ánh xạ label sang giá trị enum backend
    prio_map = {"Khoảng cách ngắn nhất": "shortest_distance", "Ít đổi tàu nhất": "fewest_transfers"}
    passenger_map = {"Người lớn": "adult", "Trẻ em": "child"}
    prio = prio_map[prio_label]
    passenger_type = passenger_map[passenger_label]

    # ---- NÚT TÌM ĐƯỜNG ----
    # POST /v1/route
    # Body: { start_coords: {lat, lon}, end_coords: {lat, lon}, priority, passenger_type }
    if st.button("🚀 TÌM ĐƯỜNG", type="primary", use_container_width=True):
        payload = {
            "start_coords": {
                "lat": st.session_state.origin[0],
                "lon": st.session_state.origin[1]
            },
            "end_coords": {
                "lat": st.session_state.dest[0],
                "lon": st.session_state.dest[1]
            },
            "priority": prio,
            "passenger_type": passenger_type
        }
        try:
            res = requests.post(f"{API_BASE}/route", json=payload, timeout=15)
            if res.status_code == 200:
                st.session_state.path_data = res.json()
                st.rerun()
            elif res.status_code == 404:
                st.error("❌ Không tìm thấy đường đi giữa hai điểm đã chọn!")
            else:
                try:
                    error_msg = res.json().get("detail", "Lỗi không xác định")
                except ValueError:
                    error_msg = res.text.strip() or f"HTTP {res.status_code}"
                st.error(f"❌ {error_msg}")
        except requests.RequestException as e:
            st.error(f"❌ Không thể kết nối tới server: {e}")

    # ---- HIỂN THỊ KẾT QUẢ ----
    # Response fields: path (List[str]), total_subway_distance, total_fare, estimated_time_minutes, total_transfers
    if st.session_state.path_data:
        r = st.session_state.path_data
        st.success(
            f"📏 {r['total_subway_distance']:.2f} km | "
            f"💰 {r['total_fare']} ¥ | "
            f"⏱️ {r['estimated_time_minutes']:.1f} phút | "
            f"🔄 {r['total_transfers']} đổi tàu"
        )
        path_stations = r.get("path", [])
        if path_stations:
            network = st.session_state.get("network_data") or {}
            sts = network.get("stations", [])
            id_to_name = {s["id"]: s["name"] for s in sts}
            with st.expander(f"📄 Lộ trình ({len(path_stations)} ga)"):
                for i, station_id in enumerate(path_stations):
                    station_display = id_to_name.get(station_id, station_id)
                    if i == 0:
                        st.markdown(f"🟢 **{station_display}** *(Điểm xuất phát)*")
                    elif i == len(path_stations) - 1:
                        st.markdown(f"🔴 **{station_display}** *(Điểm đến)*")
                    else:
                        st.markdown(f"🔵 {station_display}")

    # ---- ADMIN PANEL ----
    # POST /v1/admin/closures  (HTTP Basic Auth)
    # Body: { closed_stations: List[str], closed_edges: List[int], closed_lines: List[str] }
    if st.session_state.is_admin:
        with st.expander("🛠️ Quản trị (Admin)"):
            st.write("**Cập nhật trạng thái đóng cửa mạng lưới**")
            st.caption("Nhập tên/ID cách nhau bởi dấu phẩy. Để trống nếu không thay đổi.")

            network = st.session_state.get("network_data") or {}
            sts = network.get("stations", [])
            s_map = {f"{s['name']} (ID: {s['id']})": s["id"] for s in sts}
            id_to_name_map = {s["id"]: s["name"] for s in sts}
            
            sel_closed_sts = st.multiselect(
                "Ga bị đóng (Chọn tên ga)",
                options=list(s_map.keys()),
                key="closed_stations_input"
            )
            closed_edges_input = st.text_input(
                "Cạnh kết nối bị đóng (edge IDs số nguyên, phân cách bởi dấu phẩy)",
                key="closed_edges_input",
                placeholder="Ví dụ: 101, 205"
            )
            closed_lines_input = st.text_input(
                "Tuyến bị đóng (line names, phân cách bởi dấu phẩy)",
                key="closed_lines_input",
                placeholder="Ví dụ: Ginza, Marunouchi"
            )

            if st.button("🚫 Áp dụng đóng cửa", use_container_width=True, key="btn_apply_closures"):
                # Parse inputs
                def parse_str_list(raw: str):
                    items = [x.strip() for x in raw.split(",") if x.strip()]
                    return items if items else None

                def parse_int_list(raw: str):
                    try:
                        items = [int(x.strip()) for x in raw.split(",") if x.strip()]
                        return items if items else None
                    except ValueError:
                        st.error("❌ Edge IDs phải là số nguyên!")
                        return False  # Lỗi parse

                closed_stations = [s_map[k] for k in sel_closed_sts] if sel_closed_sts else None
                closed_edges = parse_int_list(closed_edges_input)
                closed_lines = parse_str_list(closed_lines_input)

                if closed_edges is False:
                    pass  # Lỗi đã được hiển thị
                else:
                    closure_payload = {
                        "closed_stations": closed_stations,
                        "closed_edges": closed_edges,
                        "closed_lines": closed_lines,
                    }
                    try:
                        res = requests.post(
                            f"{API_BASE}/admin/closures",
                            json=closure_payload,
                            auth=get_admin_auth(),
                            timeout=10
                        )
                        if res.status_code == 200:
                            result = res.json()
                            st.success(f"✅ {result.get('message', 'Cập nhật thành công!')}")
                            current = result.get("current_state", {})
                            if current:
                                st.write("**Đang đóng:**")
                                st.write("- **Ga:** " + (", ".join([id_to_name_map.get(s, s) for s in current.get("closed_stations", [])]) or "Không có"))
                                st.write("- **Tuyến:** " + (", ".join(current.get("closed_lines", [])) or "Không có"))
                                st.write("- **Cạnh:** " + (", ".join(str(e) for e in current.get("closed_edges", [])) or "Không có"))
                        elif res.status_code == 401:
                            st.error("❌ Phiên admin hết hạn. Vui lòng đăng nhập lại.")
                            st.session_state.is_admin = False
                        else:
                            try:
                                error_msg = res.json().get("detail", "Lỗi không xác định")
                            except ValueError:
                                error_msg = f"HTTP {res.status_code}"
                            st.error(f"❌ {error_msg}")
                    except requests.RequestException as e:
                        st.error(f"❌ Không thể kết nối tới server: {e}")

            if st.button("🔁 Mở lại tất cả (Reset)", use_container_width=True, key="btn_reset_closures"):
                try:
                    res = requests.post(
                        f"{API_BASE}/admin/closures",
                        json={"closed_stations": None, "closed_edges": None, "closed_lines": None},
                        auth=get_admin_auth(),
                        timeout=10
                    )
                    if res.status_code == 200:
                        st.success("✅ Đã mở lại toàn bộ mạng lưới!")
                    else:
                        st.error(f"❌ HTTP {res.status_code}")
                except requests.RequestException as e:
                    st.error(f"❌ Lỗi kết nối: {e}")

            st.divider()
            if st.button("🔍 Xem trạng thái hiện tại", use_container_width=True, key="btn_get_closures"):
                try:
                    res = requests.get(
                        f"{API_BASE}/admin/closures",
                        auth=get_admin_auth(),
                        timeout=10
                    )
                    if res.status_code == 200:
                        data = res.json()
                        st.write("### Trạng thái hiện tại:")
                        st.write("- **Ga đang đóng:** " + (", ".join([id_to_name_map.get(s, s) for s in data.get("closed_stations", [])]) or "Không có"))
                        st.write("- **Tuyến đang đóng:** " + (", ".join(data.get("closed_lines", [])) or "Không có"))
                        st.write("- **Kết nối (Edge) đang đóng:** " + (", ".join(str(e) for e in data.get("closed_edges", [])) or "Không có"))
                    else:
                        st.error(f"❌ HTTP {res.status_code}")
                except requests.RequestException as e:
                    st.error(f"❌ Lỗi kết nối: {e}")

# ---- BẢN ĐỒ ----
with right_col:
    st.write("### 🗺️ Bản đồ")
    mode = st.radio("Chọn vị trí trên bản đồ:", ["Điểm đi", "Điểm đến"], horizontal=True, key="mode_select")
    m = create_map(st.session_state.map_lang)
    out = st_folium(m, width=None, height=820, key=f"map_{st.session_state.map_lang}", returned_objects=["last_clicked"])

    if out and out.get("last_clicked"):
        new_pos = [out["last_clicked"]["lat"], out["last_clicked"]["lng"]]
        if mode == "Điểm đi" and new_pos != st.session_state.origin:
            st.session_state.origin = new_pos
            st.rerun()
        elif mode == "Điểm đến" and new_pos != st.session_state.dest:
            st.session_state.dest = new_pos
            st.rerun()