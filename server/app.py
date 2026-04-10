# # Copyright (c) Meta Platforms, Inc. and affiliates.
# # All rights reserved.
# #
# # This source code is licensed under the BSD-style license found in the
# # LICENSE file in the root directory of this source tree.

# """
# FastAPI application for the Openenv Proj Environment.

# This module creates an HTTP server that exposes the OpenenvProjEnvironment
# over HTTP and WebSocket endpoints, compatible with EnvClient.

# Endpoints:
#     - POST /reset: Reset the environment
#     - POST /step: Execute an action
#     - GET /state: Get current environment state
#     - GET /schema: Get action/observation schemas
#     - WS /ws: WebSocket endpoint for persistent sessions

# Usage:
#     # Development (with auto-reload):
#     uvicorn server.app:app --reload --host 0.0.0.0 --port 8000

#     # Production:
#     uvicorn server.app:app --host 0.0.0.0 --port 8000 --workers 4

#     # Or run directly:
#     python -m server.app
# """

# import sys
# import os
# import argparse
# import uvicorn

# try:
#     from openenv.core.env_server.http_server import create_app
# except Exception as e:  # pragma: no cover
#     raise ImportError(
#         "openenv is required for the web interface. Install dependencies with 'uv sync'"
#     ) from e

# # Add parent directory to path for absolute imports
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# try:
#     from models import TradingAction, TradingObservation
#     from server.openEnv_proj_environment import TradingEnvironment
# except ImportError:
#     try:
#         from ..models import TradingAction, TradingObservation
#         from .openEnv_proj_environment import TradingEnvironment
#     except ImportError:
#         from openEnv_proj_environment import TradingEnvironment
#         from models import TradingAction, TradingObservation


# # Create the app with trading environment
# app = create_app(
#     TradingEnvironment,
#     TradingAction,
#     TradingObservation,
#     env_name="trading",
#     max_concurrent_envs=1,
# )


# def main(host: str = "0.0.0.0", port: int = 8000) -> None:
#     """Entry point for running the server.
    
#     Args:
#         host: Host address to bind to (default: "0.0.0.0")
#         port: Port number to listen on (default: 8000)
#     """
#     uvicorn.run(app, host=host, port=port)


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Start the trading environment server")
#     parser.add_argument("--host", type=str, default="0.0.0.0", help="Host address")
#     parser.add_argument("--port", type=int, default=8000, help="Port number")
#     args = parser.parse_args()
#     main(host=args.host, port=args.port)



import sys
import os

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError(
        "openenv is required for the web interface. Install dependencies with 'uv sync'"
    ) from e

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from models import TradingAction, TradingObservation
    from server.openEnv_proj_environment import TradingEnvironment
except ImportError:
    try:
        from ..models import TradingAction, TradingObservation
        from .openEnv_proj_environment import TradingEnvironment
    except ImportError:
        from openEnv_proj_environment import TradingEnvironment
        from models import TradingAction, TradingObservation


app = create_app(
    TradingEnvironment,
    TradingAction,
    TradingObservation,
    env_name="trading",
    max_concurrent_envs=1,
)


def main(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Entry point for running the server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
