import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

class MyPelletApi:
    def __init__(self, host, port=23):
        self.host = host
        self.port = port
        self.lock = asyncio.Lock()

    async def send_cmd(self, command):
        """Verstuur commando en ontvang antwoord."""
        async with self.lock:
            reader, writer = None, None
            try:
                _LOGGER.debug("Verbinden met %s op poort %s", self.host, self.port)
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port), timeout=5
                )
                
                _LOGGER.debug("Versturen commando: %s", command.encode())
                writer.write(command.encode())
                await writer.drain()
                
                data = await asyncio.wait_for(reader.read(64), timeout=3)
                _LOGGER.debug("Antwoord ontvangen: %s", data.decode())
                
                return data.decode().strip()
            except asyncio.TimeoutError:
                _LOGGER.error("Timeout tijdens verbinding met kachel")
                raise Exception("Kachel reageert niet (Timeout)")
            except Exception as e:
                _LOGGER.error("Fout in MyPelletApi: %s", e)
                raise Exception(f"Socket fout: {str(e)}")
            finally:
                if writer:
                    writer.close()
                    try:
                        await writer.wait_closed()
                    except:
                        pass