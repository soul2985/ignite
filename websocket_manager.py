from fastapi import WebSocket
from typing import List


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

        print("=" * 50)
        print("✅ NEW CLIENT CONNECTED")
        print("Total Connected:", len(self.active_connections))
        print("=" * 50)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        print("=" * 50)
        print("❌ CLIENT DISCONNECTED")
        print("Total Connected:", len(self.active_connections))
        print("=" * 50)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            print("📤 Sending personal message:", message)
            await websocket.send_json(message)
            print("✅ Personal message sent")
        except Exception as e:
            print("❌ Personal message failed:", e)

    async def broadcast_json(self, message: dict):
        print("=" * 50)
        print("📢 BROADCAST STARTED")
        print("Connected Clients:", len(self.active_connections))
        print("Message:", message)
        print("=" * 50)

        disconnected = []

        for connection in self.active_connections:
            try:
                print("➡️ Sending to client...")
                await connection.send_json(message)
                print("✅ Sent successfully")

            except Exception as e:
                print("❌ Broadcast Error:", e)
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)

        print("=" * 50)
        print("🏁 BROADCAST FINISHED")
        print("=" * 50)


manager = ConnectionManager()