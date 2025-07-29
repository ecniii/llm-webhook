from fastapi import FastAPI, Request
import httpx
import os
import time

app = FastAPI()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434/api/generate")
MODEL = os.getenv("OLLAMA_MODEL", "gemma:7b")

GRAFANA_URL = os.getenv("GRAFANA_URL", "http://grafana:3000")
GRAFANA_API_KEY = os.getenv("GRAFANA_API_KEY")
GRAFANA_DASHBOARD_ID = os.getenv("GRAFANA_DASHBOARD_ID", "1")

TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL")

@app.post("/alert")
async def handle_alert(request: Request):
    data = await request.json()
    title = data.get("title", "No Title")
    message = data.get("message", "No Message")
    alert_time = int(time.time() * 1000)

    prompt = f"Analyze this Grafana alert:\n\nTitle: {title}\n\nMessage: {message}"
    async with httpx.AsyncClient() as client:
        res = await client.post(OLLAMA_URL, json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        })
        llm_output = res.json().get("response", "").strip()

        # Grafana annotation
        if GRAFANA_API_KEY:
            await client.post(f"{GRAFANA_URL}/api/annotations", headers={
                "Authorization": GRAFANA_API_KEY
            }, json={
                "dashboardId": int(GRAFANA_DASHBOARD_ID),
                "time": alert_time,
                "tags": ["LLM", title],
                "text": f"🔍 LLM Insight:\n{llm_output}"
            })

        # Microsoft Teams
        if TEAMS_WEBHOOK_URL:
            await client.post(TEAMS_WEBHOOK_URL, json={
                "text": f"⚠️ Grafana Alert: {title}\n\n🧠 LLM Analysis:\n{llm_output}"
            })

    return {"status": "ok", "analysis": llm_output}
