import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

class MyPelletApi:
    def __init__(self, host, port=23):
        self.host = host
        self.port = port
        self.lock = asyncio.Lock()

    def _generate_command(self, command):
        """De exacte methode uit de werkende climate.py."""
        formatted_cmd = "R" + command
        checksum = sum(ord(char) for char in formatted_cmd) & 0xFF
        return "\x1b" + formatted_cmd + f"{checksum:02X}" + "&"

    async def send_cmd(self, command_code):
        """Verstuur commando (bijv 'D9000') en ontvang antwoord."""
        raw_command = self._generate_command(command_code)
        
        async with self.lock:
            reader, writer = None, None
            try:
                _LOGGER.debug("Verbinden met %s:%s", self.host, self.port)
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port), timeout=10
                )
                
                writer.write(raw_command.encode())
                await writer.drain()
                
                data = await asyncio.wait_for(reader.read(64), timeout=3)
                response = data.decode().strip()
                _LOGGER.debug("Antwoord ontvangen: %s", response)
                return response
            except Exception as e:
                _LOGGER.error("Fout in MyPelletApi bij %s: %s", command_code, e)
                raise
            finally:
                if writer:
                    writer.close()
                    await writer.wait_closed()