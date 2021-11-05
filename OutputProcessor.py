import asyncio
from JobListener import get_server_job_stats, _print


async def main(m):
    await get_server_job_stats()
    await _print(m)
    await asyncio.sleep(5)


if __name__ == '__main__':
    i=0
    while True:
        i+=1
        asyncio.run(main(i))
        if i > 15:
            break

