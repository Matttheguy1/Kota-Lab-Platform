import asyncio
import json
import websockets

# Store for connected clients
connected_clients = set()

async def handle_connection(websocket, path):
    """Handle a WebSocket connection for coordinate sharing."""
    # Register client
    connected_clients.add(websocket)
    try:
        # Notify new connection
        print(f"New client connected. Total clients: {len(connected_clients)}")
        
        # Listen for messages
        async for message in websocket:
            try:
                # Parse the incoming JSON message
                data = json.loads(message)
                
                # Check if the message contains coordinates
                if 'x' in data and 'y' in data:
                    # Log the received coordinates
                    print(f"Received coordinates: x={data['x']}, y={data['y']}")
                    
                    # Optional: Add a z-coordinate if it exists
                    if 'z' in data:
                        print(f"z={data['z']}")
                    
                    # Broadcast coordinates to all connected clients
                    if connected_clients:
                        await asyncio.gather(
                            *[client.send(message) for client in connected_clients if client != websocket]
                        )
                else:
                    await websocket.send(json.dumps({"error": "Invalid format. Expected {x, y} coordinates"}))
                    
            except json.JSONDecodeError:
                await websocket.send(json.dumps({"error": "Invalid JSON format"}))
                
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed: {e}")
    finally:
        # Unregister client
        connected_clients.remove(websocket)
        print(f"Client disconnected. Remaining clients: {len(connected_clients)}")

# Set up and start the WebSocket server
async def main():
    server = await websockets.serve(handle_connection, "localhost", 8765)
    print("WebSocket server started on ws://localhost:8765")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())