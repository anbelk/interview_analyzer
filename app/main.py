from fastapi import FastAPI

app = FastAPI(title="Interview Analyzer")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
