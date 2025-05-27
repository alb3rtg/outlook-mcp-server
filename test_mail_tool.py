import asyncio
from mail.list import handle_list_emails

async def main():
    print(await handle_list_emails(folder="inbox", count=10))

if __name__ == "__main__":
    asyncio.run(main())
