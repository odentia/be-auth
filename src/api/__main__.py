import uvicorn

from src.api.app import create_app
from src.core.config import load_settings


def main() -> None:
    settings = load_settings()
    app = create_app(settings)

    uvicorn.run(
        app,
        host=settings.http_host,
        port=settings.http_port,
        reload=settings.reload,  # safe for local/dev only
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
