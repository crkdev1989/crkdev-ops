from fastapi import FastAPI
import psutil

app = FastAPI(title="CRK Health Agent")


@app.get("/health")
def health():
    disk = psutil.disk_usage("/")
    return {
        "cpu": psutil.cpu_percent(interval=0.3),
        "ram": psutil.virtual_memory().percent,
        "disk": disk.percent,
        "status": "healthy",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("health_agent:app", host="0.0.0.0", port=9090, reload=False)
