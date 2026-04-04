import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# --- CẤU HÌNH HỆ THỐNG ---
API_BASE = "http://127.0.0.1:8000/api"
st.set_page_config(page_title="Tokyo Subway Pathfinder", layout="wide", page_icon="🚇")

# Khởi tạo Session State để lưu dữ liệu khi reload trang
if "token" not in st.session_state: st.session_state.token = None
if "role" not in st.session_state: st.session_state.role = "user"
if "origin" not in st.session_state: st.session_state.origin = [35.6812, 139.7671]
if "dest" not in st.session_state: st.session_state.dest = [35.6586, 139.7454]
if "path_data" not in st.session_state: st.session_state.path_data = None

def get_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}

# --- GIAO DIỆN ĐĂNG NHẬP ---
if not st.session_state.token:
    st.sidebar.title("🔐 Đăng nhập hệ thống")
    u = st.sidebar.text_input("Username")
    p = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Đăng nhập", use_container_width=True):
        res = requests.post(f"{API_BASE}/auth/login", data={"username": u, "password": p})
        if res.status_code == 200:
            data = res.json()
            st.session_state.token = data["access_token"]
            st.session_state.role = data.get("role", "user")
            st.rerun()
        else:
            st.sidebar.error("Sai tài khoản hoặc mật khẩu!")
    st.info("💡 Hãy đăng nhập từ thanh bên trái để bắt đầu tìm đường.")
    
# --- GIAO DIỆN CHÍNH SAU KHI ĐĂNG NHẬP ---
else:
    st.sidebar.success(f"Chào, {st.session_state.role.upper()}")
    if st.sidebar.button("Đăng xuất"):
        st.session_state.token = None
        st.session_state.path_data = None
        st.rerun()

    tab1, tab2 = st.tabs(["🔍 Tìm đường & Bản đồ", "🛠️ Quản trị (Admin)"])

    # --- TAB 1: TÌM ĐƯỜNG ---
    with tab1:
        c1, c2 = st.columns([2.5, 1])
        
        with c1:
            # 1. Khởi tạo bản đồ trung tâm Tokyo
            m = folium.Map(location=[35.6895, 139.6917], zoom_start=12)
            
            # 2. VẼ ĐƯỜNG ĐI (POLYLINES)
            if st.session_state.path_data:
                steps = st.session_state.path_data.get('steps', [])
                for stp in steps:
                    # Kiểm tra xem Backend có trả về tọa độ không
                    if all(k in stp for k in ('from_lat', 'from_lon', 'to_lat', 'to_lon')):
                        p1 = [stp['from_lat'], stp['from_lon']]
                        p2 = [stp['to_lat'], stp['to_lon']]
                        
                        # Vẽ đường kẻ xanh đậm nối các ga
                        folium.PolyLine(
                            locations=[p1, p2],
                            color="#2E86C1", 
                            weight=6,
                            opacity=0.8,
                            tooltip=stp.get('line_name', 'Tàu điện')
                        ).add_to(m)
                        
                        # Vẽ chấm tròn tại ga trung gian
                        folium.CircleMarker(p1, radius=4, color="white", fill=True, fill_color="#2E86C1").add_to(m)
                        folium.CircleMarker(p2, radius=4, color="white", fill=True, fill_color="#2E86C1").add_to(m)

            # 3. Vẽ 2 cái ghim Điểm đi (Xanh) / Điểm đến (Đỏ)
            folium.Marker(st.session_state.origin, icon=folium.Icon(color='green', icon='play'), tooltip="Điểm đi").add_to(m)
            folium.Marker(st.session_state.dest, icon=folium.Icon(color='red', icon='stop'), tooltip="Điểm đến").add_to(m)

            # Điều khiển chọn vị trí bằng cách click
            mode = st.radio("📍 Đang chọn vị trí cho:", ["Điểm đi", "Điểm đến"], horizontal=True)
            
            # Hiển thị Map
            out = st_folium(m, width=800, height=550, key="tokyo_map_final", returned_objects=["last_clicked"])

            # Xử lý click chọn điểm
            if out and out.get("last_clicked"):
                new_pos = [out["last_clicked"]["lat"], out["last_clicked"]["lng"]]
                if mode == "Điểm đi" and new_pos != st.session_state.origin:
                    st.session_state.origin = new_pos
                    st.rerun()
                elif mode == "Điểm đến" and new_pos != st.session_state.dest:
                    st.session_state.dest = new_pos
                    st.rerun()

        with c2:
            st.write("### ⚙️ Thông số lộ trình")
            st.write(f"🟢 **Từ:** `{st.session_state.origin[0]:.4f}, {st.session_state.origin[1]:.4f}`")
            st.write(f"🔴 **Đến:** `{st.session_state.dest[0]:.4f}, {st.session_state.dest[1]:.4f}`")
            
            prio = st.selectbox("Ưu tiên theo", ["time", "cost", "distance"])
            if st.button("🚀 TÌM ĐƯỜNG", type="primary", use_container_width=True):
                payload = {
                    "origin_lat": st.session_state.origin[0], "origin_lon": st.session_state.origin[1],
                    "dest_lat": st.session_state.dest[0], "dest_lon": st.session_state.dest[1],
                    "priority": prio
                }
                res = requests.post(f"{API_BASE}/path/find", json=payload, headers=get_headers())
                if res.status_code == 200:
                    st.session_state.path_data = res.json()
                    st.rerun()
                else:
                    st.error("❌ Không tìm thấy đường đi!")

            # Hiển thị kết quả chi tiết
            if st.session_state.path_data:
                res = st.session_state.path_data
                st.markdown(f"### ✅ Kết quả")
                st.success(f"⏱️ **{res['total_time_min']} phút** | 💰 **{res['total_cost_yen']} ¥**")
                
                with st.expander("📄 Chi tiết các chặng"):
                    for s in res['steps']:
                        st.write(f"🚩 **{s['from_station']}** → **{s['to_station']}**")
                        st.caption(f"Tuyến: {s.get('line_name')} | {s.get('time_min')} phút")

    # --- TAB 2: ADMIN ---
    with tab2:
        if st.session_state.role != "admin":
            st.warning("⛔ Bạn cần quyền ADMIN để truy cập tính năng này.")
        else:
            st.subheader("🛠️ Quản lý mạng lưới tàu điện")
            
            # Lấy danh sách ga từ Backend
            try:
                stations_res = requests.get(f"{API_BASE}/stations/", headers=get_headers())
                stations_list = stations_res.json() if stations_res.status_code == 200 else []
            except:
                stations_list = []

            if stations_list:
                # Chặn/Mở Ga
                st.write("#### 🚉 Quản lý Ga")
                s_map = {f"{s.get('station_name')} (ID: {s.get('station_id')})": s.get('station_id') for s in stations_list}
                sel_s = st.selectbox("Chọn ga cần thao tác", options=list(s_map.keys()))
                
                col_btn1, col_btn2 = st.columns(2)
                if col_btn1.button("🚫 Chặn ga này", use_container_width=True):
                    requests.post(f"{API_BASE}/admin/station/ban", json={"station_id": s_map[sel_s]}, headers=get_headers())
                    st.toast(f"Đã chặn ga {sel_s}")
                if col_btn2.button("✅ Mở ga này", use_container_width=True):
                    requests.post(f"{API_BASE}/admin/station/unban", json={"station_id": s_map[sel_s]}, headers=get_headers())
                    st.toast(f"Đã mở ga {sel_s}")
            else:
                st.error("Không thể tải danh sách ga từ Database.")

            st.divider()
            
            # Chặn Tuyến
            st.write("#### 🛤️ Quản lý Tuyến (Lines)")
            line_id_input = st.text_input("Nhập mã Tuyến (ví dụ: Ginza, Marunouchi)")
            if st.button("Xác nhận thay đổi Tuyến", use_container_width=True):
                # Giả định mày có endpoint chặn tuyến
                requests.post(f"{API_BASE}/admin/line/ban", json={"line_id": line_id_input}, headers=get_headers())
                st.success(f"Đã cập nhật trạng thái cho tuyến {line_id_input}")