from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="Nexus Manager")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
