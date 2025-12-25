from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from app.core.database import Base


class AppSettings(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    # Admin authentication
    admin_username = Column(String, nullable=True)
    admin_password_hash = Column(String, nullable=True)
    is_setup_complete = Column(Boolean, default=False)
    # OpenAlgo settings
    openalgo_api_key = Column(String, nullable=True)
    openalgo_host = Column(String, default="http://127.0.0.1:5000")
    openalgo_ws_url = Column(String, default="ws://127.0.0.1:8765")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
