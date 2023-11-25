from fastapi import FastAPI

import routers

# FastAPI Application
app = FastAPI(
    title="service-scraper",
    description="Author - SD",
    version="1.0.0",
)


# Include Routers
app.include_router(routers.router)


# Event: On Startup
@app.on_event("startup")
async def startup_event() -> None:
    print("Startup!")


# Event: On Shutdown
@app.on_event("shutdown")
async def shutdown_event():
    print("Shutdown!")
