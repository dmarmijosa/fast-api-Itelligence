import json
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import requests

app = FastAPI()

OLLAMA_API_URL = "http://localhost:11434/api/generate"

def wait_for_ollama():
    for _ in range(10):  # Intentar por 10 intentos (aprox. 10s)
        try:
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                print("✅ Ollama está disponible")
                return True
        except requests.ConnectionError:
            print("⏳ Esperando a Ollama...")
            time.sleep(1)
    return False

if not wait_for_ollama():
    raise Exception("❌ Ollama no se pudo conectar después de múltiples intentos.")
class QueryModel(BaseModel):
    query: str

# ✅ Ajustamos la función de streaming para mejor compatibilidad
def stream_ollama_response(query: str):
    payload = {
        "model": "deepseek-r1:8b",
        "prompt": query,
        "stream": True
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=payload, stream=True)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error al conectar con Ollama: {e}")
        raise HTTPException(status_code=500, detail=f"Error conectando a Ollama: {e}")

    buffer = ""  # Acumulador de texto

    def event_generator():
        nonlocal buffer
        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode("utf-8"))
                chunk = data.get("response", "")

                buffer += chunk  # 🔹 Acumular los fragmentos en lugar de enviarlos incompletos

                if "." in chunk or "\n" in chunk:  # 🔹 Enviar solo cuando hay punto o salto de línea
                    yield buffer + "\n"
                    buffer = ""  # 🔹 Reiniciar el buffer

    return event_generator()

@app.post("/ask_stream/")
async def ask_stream(payload: QueryModel, request: Request):
    print(f"📡 Recibida pregunta: {payload.query}")

    return StreamingResponse(
        stream_ollama_response(payload.query), 
        media_type="text/event-stream",  # ✅ Cambiado a text/event-stream para mejor compatibilidad
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Transfer-Encoding": "chunked"
        }
    )