import sys
import os

# Thêm đường dẫn để Python tìm thấy module app
sys.path.append(os.getcwd())

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User

# Tạo kết nối
db: Session = SessionLocal()

# NHẬP USERNAME MÀY MUỐN LÊN ADMIN VÀO ĐÂY
target_username = "quanganh" 

user = db.query(User).filter(User.username == target_username).first()

if user:
    user.role = "admin"
    db.commit()
    print(f"--- THÀNH CÔNG ---")
    print(f"User '{user.username}' đã được nâng cấp lên ADMIN.")
else:
    print(f"--- THẤT BẠI ---")
    print(f"Không tìm thấy tài khoản nào tên là '{target_username}' trong Database.")

db.close()