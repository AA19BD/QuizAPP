"""
Put here any Python code that must be runned before application startup.
It is included in `init.sh` script.

By defualt `main` create a superuser if not exists
"""

import asyncio

from sqlalchemy import select

from app.core import config, security
from app.core.session import async_session
from app.models import User
from log import Log

log = Log()


async def main() -> None:
    log.info("Start initial data")
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.email == config.settings.FIRST_SUPERUSER_EMAIL)
        )
        user = result.scalars().first()

        if user is None:
            new_superuser = User(
                email=config.settings.FIRST_SUPERUSER_EMAIL,
                hashed_password=security.get_password_hash(
                    config.settings.FIRST_SUPERUSER_PASSWORD
                ),
            )
            session.add(new_superuser)
            await session.commit()
            log.info("Superuser was created")
        else:
            log.info("Superuser already exists in database")

        log.info("Initial data created")


if __name__ == "__main__":
    asyncio.run(main())
