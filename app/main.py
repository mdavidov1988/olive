from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app import db
    try:
        await db.init_pool()
        print("Database connected and schema initialized.")
    except Exception as e:
        print(f"Warning: Database not connected: {e}")
        print("App will run but data operations will fail.")
    yield
    from app import db as db_mod
    await db_mod.close_pool()


app = FastAPI(title="Olive", lifespan=lifespan)

# Include routers
from app.auth import router as auth_router
from app.routes.babies import router as babies_router
from app.routes.feedings import router as feedings_router
from app.routes.poops import router as poops_router
from app.routes.sleep import router as sleep_router
from app.routes.weight import router as weight_router
from app.routes.summary import router as summary_router

app.include_router(auth_router)
app.include_router(babies_router)
app.include_router(feedings_router)
app.include_router(poops_router)
app.include_router(sleep_router)
app.include_router(weight_router)
app.include_router(summary_router)

# Static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    index_path = os.path.join(static_dir, "index.html")
    with open(index_path, "r") as f:
        html = f.read()
    return HTMLResponse(
        content=html,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
