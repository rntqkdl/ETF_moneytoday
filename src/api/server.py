"""
src/api/server.py
FastAPI 애플리케이션 진입점
"""

from fastapi import FastAPI
import uvicorn
from config.settings import settings
from src.api.routes import router

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="머니투데이 제3회 ETF 투자왕 대회 (연금형) n8n 오케스트레이션 FastAPI 브릿지"
    )
    app.include_router(router)
    return app

app = create_app()

def start_server():
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)

if __name__ == "__main__":
    start_server()
