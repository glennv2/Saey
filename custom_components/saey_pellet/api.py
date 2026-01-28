import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

class MyPelletApi:
    def __init__(self, host, port=23):
        self.host = host
        self.port = port
        self.lock = asyncio.Lock()

    async def send_cmd(self, command):
        async with self.lock:
            reader, writer = None, None
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port), timeout=5
                )
                
                writer.write(command.encode())
                await writer.drain()
                
                data = await asyncio.wait_for(reader.read(64), timeout=3)
                
                return data.decode().strip()
            except asyncio.TimeoutError:
                raise Exception("Kachel reageert niet (Timeout)")
            except ConnectionRefusedError:
                raise Exception("Verbinding geweigerd (is poort 23 open?)")
            except Exception as e:
                raise Exception(f"Netwerkfout: {str(e)}")
            finally:
                if writer:
                    writer.close()
                    try:
                        await writer.wait_closed()
                    except:
                        pass