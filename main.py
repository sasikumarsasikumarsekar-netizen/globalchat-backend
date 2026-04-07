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

    try:
        while True:
            data = await websocket.receive_text()
            msg_data = json.loads(data)

            sender = msg_data["sender"]
            receiver = msg_data["receiver"]
            message = msg_data["message"]

            # 🔥 SEND TO RECEIVER (translated)
            if receiver in clients:
                try:
                    receiver_lang = clients[receiver]["lang"]

                    translated = GoogleTranslator(
                        source='auto',
                        target=receiver_lang
                    ).translate(message)

                    await clients[receiver]["ws"].send_text(
                        f"{sender}: {translated}"
                    )

                except Exception as e:
                    await clients[receiver]["ws"].send_text(
                        f"{sender}: {message}"
                    )

            # 🔥 SEND TO SENDER (original only)
            if sender in clients:
                await clients[sender]["ws"].send_text(
                    f"{sender}: {message}"
                )

    except WebSocketDisconnect:
        if name in clients:
            del clients[name]