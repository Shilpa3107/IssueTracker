from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from routes import issues, comments, reports

app = FastAPI(
    title="Issue Tracker API",
    description="API for managing issues, comments, labels with transactions and concurrency control",
    version="1.0.0"
)

# Optional: enable CORS if you use a frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your routes
app.include_router(issues.router)
app.include_router(comments.router)
app.include_router(reports.router)

# Root endpoint for testing
@app.get("/")
def root():
    return {"message": "Issue Tracker API is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
