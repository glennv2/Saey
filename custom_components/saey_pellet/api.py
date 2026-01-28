import asyncio
import socket

class MyPelletApi:
    def __init__(self, host, port=23):
        self.host = host
        self.port = port
        self.lock = asyncio.Lock() 

    async def send_cmd(self, command):
        """Verstuur commando en ontvang antwoord."""
        async with self.lock:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port), timeout=5
                )
                
                writer.write(command.encode())
                await writer.drain()
                
                data = await asyncio.wait_for(reader.read(10), timeout=3)
                
                writer.close()
                await writer.wait_closed()
                
                return data.decode()
            except Exception as e:
                raise Exception(f"Socket fout: {e}")