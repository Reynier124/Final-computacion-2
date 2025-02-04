import argparse
import asyncio
import signal
import json
from aiohttp import web
from calculator import calculate_simpson_method
from multiprocessing import Process, Queue

def logger_process(queue):
    while True:
        log_data = queue.get() 
        if log_data is None:  
            break
        with open("server_log.txt", "a") as log_file:
            log_file.write(json.dumps(log_data) + "\n")

class AsyncConnection:
    def __init__(self, host_ipv4, host_ipv6, port, log_queue):
        self.host_ipv4 = host_ipv4
        self.host_ipv6 = host_ipv6
        self.port = port
        self.log_queue = log_queue
        self.app = web.Application()
        self.app.router.add_post('/calculator', self.handle_post)

    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()

        self.site_ipv4 = web.TCPSite(runner, self.host_ipv4, self.port)
        await self.site_ipv4.start()
        print(f"HTTP server started at http://{self.host_ipv4}:{self.port} (IPv4)")

        self.site_ipv6 = web.TCPSite(runner, self.host_ipv6, self.port)
        await self.site_ipv6.start()
        print(f"HTTP server started at http://[{self.host_ipv6}]:{self.port} (IPv6)")

    async def stop(self):
        print("Stopping HTTP server...")
        await self.site_ipv4.stop()
        await self.site_ipv6.stop()

    async def handle_post(self, request):
        try:
            data = await request.json()

            function = data['function']
            a = data['a']
            b = data['b']
            n = data['n']
            aprox = data['aprox']

            task = calculate_simpson_method.delay(a, b, n, function, aprox)

            list_results = task.get(timeout=10)

            result = list_results[0]
            time_execution = list_results[1]
            date = list_results[2]

            log_data = {
                "function": function,
                "a": a,
                "b": b,
                "n": n,
                "aprox": aprox,
                "result": result,
                "time_execution": time_execution,
                "date": date,
            }

            self.log_queue.put(log_data)

            response_data = {
                "result": result,
                "time_execution": time_execution,
                "date": date,
            }

            return web.json_response(response_data)
        except Exception as e:
            return web.json_response(
                {"error": str(e)},
                status=500,
            )

async def main():
    parser = argparse.ArgumentParser(description="Servidor HTTP asíncrono para calcular el método de Simpson")
    parser.add_argument("--host_ipv4", type=str, default="0.0.0.0", help="Dirección IPv4 del servidor")
    parser.add_argument("--host_ipv6", type=str, default="::", help="Dirección IPv6 del servidor")
    parser.add_argument("--port", type=int, default=8080, help="Puerto del servidor")
    args = parser.parse_args()

    HOST_IPV4, HOST_IPV6, PORT = args.host_ipv4, args.host_ipv6, args.port

    log_queue = Queue()
    logger = Process(target=logger_process, args=(log_queue,))
    logger.start()

    conn = AsyncConnection(HOST_IPV4, HOST_IPV6, PORT, log_queue)

    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    try:
        await conn.start()
        print("Server is running. Press Ctrl+C to stop.")
        await stop_event.wait() 
    finally:
        await conn.stop()
        log_queue.put(None)  
        logger.join()

if __name__ == "__main__":
    asyncio.run(main())
