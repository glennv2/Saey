import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

class MyPelletApi:
    def __init__(self, host, port=23):
        self.host = host
        self.port = port
        self.lock = asyncio.Lock()

    def _generate_command(self, command):
        formatted_cmd = "R" + command
        checksum = sum(ord(char) for char in formatted_cmd) & 0xFF
        return "\x1b" + formatted_cmd + f"{checksum:02X}" + "&"

    async def _transact(self, raw_command):
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
                _LOGGER.error("Fout in MyPelletApi bij %s: %s", raw_command, e)
                raise
            finally:
                if writer:
                    writer.close()
                    await writer.wait_closed()

    async def send_cmd(self, command_code):
        """Send a bare command code (e.g. "D9000"). Applies the ESC / "R" /
        checksum / "&" framing automatically. Use for reads."""
        return await self._transact(self._generate_command(command_code))

    async def send_raw_cmd(self, raw_command):
        """Send an already fully-formed, pre-checksummed command exactly as
        given — no additional framing or checksum. Use for the write/control
        commands whose exact bytes were already confirmed working; do NOT
        run these through send_cmd(), which would double-wrap them."""
        return await self._transact(raw_command)