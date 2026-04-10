from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from deep_translator import GoogleTranslator
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

clients = {}

@app.get("/")
def home():
    return {"message": "GlobalChat backend running 🚀"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    user_info = await websocket.receive_text()
    user_data = json.loads(user_info)

    name = user_data["name"]
    lang = user_data["lang"]

    clients[name] = {
        "ws": websocket,
        "lang": lang
    }

    await broadcast_users()

    try:
        while True:
            data = await websocket.receive_text()
            msg_data = json.loads(data)

            sender = msg_data["sender"]
            receiver = msg_data["receiver"]
            message = msg_data["message"]

            # ✅ Check receiver exists
            if receiver in clients:
                try:
                    translated = GoogleTranslator(
                        source='auto',
                        target=clients[receiver]["lang"]
                    ).translate(message)
                except:
                    translated = message  # fallback

                await clients[receiver]["ws"].send_text(json.dumps({
                    "type": "msg",
                    "data": f"{sender}: {translated}"
                }))

            # ✅ Send back to sender safely
            if sender in clients:
                await clients[sender]["ws"].send_text(json.dumps({
                    "type": "msg",
                    "data": f"{sender}: {message}"
                }))

    except WebSocketDisconnect:
        if name in clients:
            del clients[name]
        await broadcast_users()


async def broadcast_users():
    user_list = list(clients.keys())
    for user in clients:
        await clients[user]["ws"].send_text(json.dumps({
            "type": "users",
            "users": user_list
        }))
