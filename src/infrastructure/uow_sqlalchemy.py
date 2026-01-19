from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from src.application.uow import UnitOfWork
# from src.domain.repositories import UsersRepo
# from src.infrastructure.persistence.repositories import UsersRepoSQL


class SQLAlchemyUoW(UnitOfWork):

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._sf = session_factory
        self.session: AsyncSession | None = None
#         self.users: UsersRepo | None = None

#     async def __aenter__(self):
#         self.session = self._sf()
#         self.users = UsersRepoSQL(self.session)
#         return self

#     async def __aexit__(self, exc_type, exc, tb):
#         try:
#             if exc_type is None:
#                 await self.session.commit()
#             else:
#                 await self.session.rollback()
#         finally:
#             await self.session.close()

#     async def commit(self):
#         await self.session.commit()

#     async def rollback(self):
#         await self.session.rollback()
