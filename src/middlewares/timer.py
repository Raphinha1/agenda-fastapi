from time import perf_counter

from fastapi import Request


async def response_time_middleware(request: Request, call_next):
    start = perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{perf_counter() - start:.4f} s"
    return response
