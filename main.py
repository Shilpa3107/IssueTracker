from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import your routers
from routes import issues, comments, reports, users

# Create FastAPI app
app = FastAPI(
    title="Issue Tracker API",
    description="API for managing issues, comments, labels, bulk updates, and CSV imports",
    version="1.0.0"
)

# Optional: CORS for frontend testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(issues.router)
app.include_router(comments.router)
app.include_router(reports.router)
app.include_router(users.router)

# Root endpoint for testing
@app.get("/")
def root():
    return {"message": "Issue Tracker API is running!"}

# Run app using uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
