import asyncio
import sys
from contextlib import asynccontextmanager

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import engine
from app.routers import projects, generation, execution, reports

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup
    yield
    # Teardown
    await engine.dispose()

app = FastAPI(
    title="AI-Powered Test Automation API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(generation.router, tags=["generation"])
app.include_router(execution.router, tags=["execution"])
app.include_router(reports.router, tags=["reports"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
