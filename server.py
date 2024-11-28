import argparse
import asyncio
import signal
import json
from aiohttp import web
from aioquic.asyncio import serve
from aioquic.quic.configuration import QuicConfiguration
from aioquic.asyncio.protocol import QuicConnectionProtocol

def cleanup(signum, frame):
    print("Finish the process")
    loop = asyncio.get_running_loop()
    loop.stop()
    exit()

class AsyncConnection(QuicConnectionProtocol):
    def __init__(self, host, port, a_host, a_port, config):
        self.host = host
        self.port = port
        self.a_host = a_host
        self.a_port = a_port
        self.config = config
        self.app = web.Application()
        self.app.router.add_post('/calculator', self.handle_post)

    async def start(self):
        server = await serve(
            self.host,
            self.port,
            configuration=self.config,
            create_protocol=self.create_protocol
        )
        print(f"QUIC HTTP/3 server started at https://{self.host}:{self.port}")
        #await server.wait_closed()

    def create_protocol(self):
        return self

    async def handle_post(self, request):
        data = await request.post()
        response_data = await self.send_json_to_server(data)
        return web.Response(text=response_data)

    async def send_json_to_server(self, data):
        server_host = self.a_host
        server_port = self.a_port

        reader, writer = await asyncio.open_connection(server_host, server_port)

        json_data = json.dumps(data)
        writer.write(json_data.encode())
        await writer.drain()

        response = await reader.read(1024)
        response_data = json.loads(response.decode())

        writer.close()
        await writer.wait_closed()

        return response_data

async def main():
    parser = argparse.ArgumentParser(description="Servidor HTTP/3 asíncrono para comunicación con el cliente")
    parser.add_argument("--host", type=str, default="::", help="Dirección IP del servidor")
    parser.add_argument("--port", type=int, default=8080, help="Puerto del servidor")
    parser.add_argument("--Ahost", type=str, default="localhost", help="Dirección IP del servidor de procesamiento de imágenes")
    parser.add_argument("--Aport", type=int, default=7373, help="Puerto del servidor de procesamiento de imágenes")
    parser.add_argument("--certificate", type=str, required=True, help="Ruta al certificado SSL")
    parser.add_argument("--private_key", type=str, required=True, help="Ruta a la clave privada del certificado SSL")
    args = parser.parse_args()

    config = QuicConfiguration(is_client=False)
    config.load_cert_chain(args.certificate, args.private_key)

    HOST, PORT = args.host, args.port
    Ahost, Aport = args.Ahost, args.Aport
    signal.signal(signal.SIGINT, cleanup)
    conn = AsyncConnection(HOST, PORT, Ahost, Aport, config)
    await conn.start()

if __name__ == "__main__":
    asyncio.run(main())
