import asyncio
import sys
from contextlib import asynccontextmanager
from pathlib import Path

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
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

workspace_path = Path(
    settings.playwright_workspace_path
).resolve()
reports_path = workspace_path / "reports"
test_results_path = workspace_path / "test-results"

reports_path.mkdir(parents=True, exist_ok=True)
test_results_path.mkdir(parents=True, exist_ok=True)

app.mount(
    "/artifacts/reports",
    StaticFiles(directory=str(reports_path)),
    name="playwright-reports",
)
app.mount(
    "/artifacts/test-results",
    StaticFiles(directory=str(test_results_path)),
    name="playwright-test-results",
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
