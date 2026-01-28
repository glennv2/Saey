import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

class MyPelletApi:
    def __init__(self, host, port=23):
        self.host = host
        self.port = port
        self.lock = asyncio.Lock()

async def send_cmd(self, command):
        """Verstuur commando en log alles."""
        async with self.lock:
            _LOGGER.debug("Versturen naar kachel: %s", command.encode()) # Zie wat we sturen
            reader, writer = None, None
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port), timeout=5
                )
                
                writer.write(command.encode())
                await writer.drain()
                
                data = await asyncio.wait_for(reader.read(64), timeout=3)
                _LOGGER.debug("Ontvangen van kachel: %s", data) # Zie wat we terugkrijgen
                
                return data.decode().strip()
            except Exception as e:
                _LOGGER.error("FOUT bij communicatie: %s", e)
                raise Exception(f"Socket fout: {e}")
            finally:
                if writer:
                    writer.close()
                    await writer.wait_closed()