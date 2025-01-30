import asyncio
import aiohttp
import random

async def send_request(session, url, data):
    """
    Envía una solicitud POST al servidor y maneja la respuesta.
    """
    try:
        async with session.post(url, json=data) as response:
            result = await response.json()
            print(f"Response from {url}: {result}")
    except Exception as e:
        print(f"Error sending request to {url}: {e}")

async def main():
    # URLs para probar con IPv4 e IPv6
    ipv4_url = "http://127.0.0.1:8080/calculator"
    ipv6_url = "http://[::1]:8080/calculator"  # Suponiendo que el servidor está configurado para IPv6

    # Datos para las solicitudes
    test_data = [
        {
            "function": f"x**4",
            "a": 0,
            "b": 1,
            "n": 10,
            "aprox": 10
        }
        for i in range(1, 11)
    ]

    # Crear un cliente aiohttp
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        # Alternar entre IPv4 e IPv6 para las solicitudes
        for i, data in enumerate(test_data):
            url = ipv4_url if i % 2 == 0 else ipv6_url
            tasks.append(send_request(session, url, data))
        
        # Ejecutar todas las solicitudes concurrentemente
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
