"""Entry point per uvicorn."""

import uvicorn
from pman.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "pman.api:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
