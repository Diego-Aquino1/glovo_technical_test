import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.audit.logger import audit_logger
from app.config import settings
from app.erp_client import erp_client
from app.tools.article_info import get_article_info
from app.tools.purchase_orders import get_pending_replenishments
from app.tools.stock import get_stock_availability

logging.basicConfig(level=logging.DEBUG if settings.debug else logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncGenerator[None, None]:
    logger.info("[mcp-server] Inicializando ERP Client y Audit Logger...")
    await erp_client.initialize()
    await audit_logger.initialize()
    logger.info("[mcp-server] Listo para recibir conexiones.")
    try:
        yield
    finally:
        logger.info("[mcp-server] Cerrando conexiones...")
        await erp_client.close()
        await audit_logger.close()


mcp = FastMCP(
    name="ERP MCP Server",
    lifespan=lifespan,
)

mcp.add_tool(get_article_info)
mcp.add_tool(get_stock_availability)
mcp.add_tool(get_pending_replenishments)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "mcp-server"})


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=settings.port,
    )
