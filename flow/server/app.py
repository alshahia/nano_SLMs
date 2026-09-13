"""FastAPI layer for the flow/ MVP (Task 7).

A THIN wrapper around the Task 2-6 modules (graph_schema, nodes, flows,
config_gen, runner): every route only parses the request, calls one
already-tested function and maps a typed error to an HTTP status. All
real logic lives in those imported modules (or in this module's pure
helpers below, which the contract tests exercise directly).

Error -> HTTP status mapping (also codified in status_for_error()):
- runner.JobRunningError / runner.NoJobRunningError (typed runner errors) -> 409
- flows/config_gen validation ValueError                                 -> 400 {"errors": [...]}
- flows.load FileNotFoundError (no such flow)                            -> 404 {"detail": ...}

Port resolution: --port wins when given; otherwise FLOW_PORT env; default 3010.
Prod static serving: mounts flow/dist at "/" when NOT --dev and dist exists
(dev mode needs nothing - the frontend dev server proxies /api).
"""

import argparse
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from flow.server import config_gen, flows, nodes, runner

FLOW_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = FLOW_ROOT / "dist"

DEFAULT_PORT = 3010
# CORS is for the frontend dev server only (Vite on 5174, historical 5173).
DEV_ORIGINS = ("http://localhost:5174", "http://localhost:5173")

DEFAULT_HOST = "127.0.0.1"


# ---------------------------------------------------------------------------
# Pure helpers (contract-tested)
# ---------------------------------------------------------------------------

def resolve_port(port_arg, env=None):
    """--port wins when present; else FLOW_PORT env; else DEFAULT_PORT.

    env overrides os.environ for tests (None = use os.environ). A
    non-integer FLOW_PORT falls back to the default port, never crashes.
    """
    if port_arg is not None:
        return int(port_arg)
    if env is None:
        env = os.environ
    raw = env.get("FLOW_PORT")
    if raw:
        try:
            return int(raw)
        except (TypeError, ValueError):
            return DEFAULT_PORT
    return DEFAULT_PORT


def error_list(exc):
    """Split a validator ValueError (newline-joined reasons) into a list."""
    return [line for line in str(exc).split("\n") if line]


def status_for_error(exc):
    """HTTP status for an exception of a backend module (409/404/400).

    runner.JobRunningError subclasses ValueError, so the typed runner
    errors are checked FIRST (409 wins over the generic 400).
    """
    if isinstance(exc, (runner.JobRunningError, runner.NoJobRunningError)):
        return 409           # typed runner errors: busy / no live job
    if isinstance(exc, FileNotFoundError):
        return 404           # no such flow
    if isinstance(exc, ValueError):
        return 400           # flows/config_gen validation reasons
    return 500


def validate_preflight(g):
    """Collect every validation error WITHOUT writing into the repo.

    Runs graph_schema.validate and the per-node registry prop checks (via
    flows' dual-validator collector), then a config_gen.generate dry-run
    through a process-local tempfile out_dir so NO repo file is touched by
    validation (reserved names / rows cap surface from there too).
    Returns a list of human-readable reason strings; [] means valid.
    """
    errors = list(flows.collect_validation_errors(g))
    try:
        with tempfile.TemporaryDirectory(prefix="flow-validate-") as out_dir:
            config_gen.generate(g, out_dir=out_dir)
    except ValueError as exc:
        errors.extend(error_list(exc))
    return errors


def flows_validation_response(exc):
    """400 JSONResponse carrying the newline-split validation reasons."""
    return JSONResponse(status_code=400, content={"errors": error_list(exc)})


def nodes_snapshot():
    """Registry view for the frontend (kinds/ports/props/gates)."""
    return {
        "valid_kinds": sorted(nodes.VALID_KINDS),
        "nodes": nodes.NODES,
        "gates": dict(nodes.GATES),
    }


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app(dev=False):
    """Build the FastAPI app. dev=True adds CORS for the Vite dev server
    and skips the flow/dist static mount; prod mounts dist when present."""
    app = FastAPI(title="flow server", docs_url=None, redoc_url=None,
                  openapi_url=None)
    if dev:
        app.add_middleware(
            CORSMiddleware, allow_origins=list(DEV_ORIGINS),
            allow_methods=["*"], allow_headers=["*"])

    @app.get("/api/health")
    def health():
        return {"ok": True}

    @app.get("/api/nodes")
    def get_nodes():
        return nodes_snapshot()

    @app.get("/api/flows")
    def list_all_flows():
        return flows.list_flows()

    @app.get("/api/flows/{name}")
    def read_flow(name: str):
        try:
            return flows.load(name)
        except FileNotFoundError as exc:
            return JSONResponse(status_code=404, content={"detail": str(exc)})
        except ValueError as exc:
            return flows_validation_response(exc)

    @app.put("/api/flows/{name}")
    async def write_flow(name: str, request: Request):
        try:
            graph = await request.json()
        except Exception:
            return JSONResponse(status_code=400,
                                content={"errors": ["body: invalid JSON"]})
        try:
            flows.save(name, graph)
        except ValueError as exc:
            return flows_validation_response(exc)
        return {"ok": True, "name": name}

    @app.delete("/api/flows/{name}")
    def remove_flow(name: str):
        try:
            flows.delete_flow(name)
        except (FileNotFoundError, ValueError) as exc:
            return JSONResponse(status_code=status_for_error(exc),
                                content={"detail": str(exc)})
        return {"ok": True}

    @app.post("/api/validate")
    async def validate(request: Request):
        try:
            graph = await request.json()
        except Exception:
            return JSONResponse(status_code=400,
                                content={"errors": ["body: invalid JSON"]})
        errors = validate_preflight(graph)
        return {"ok": not errors, "errors": errors}

    @app.post("/api/run")
    async def run_flow(request: Request):
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(status_code=400,
                                content={"errors": ["body: invalid JSON"]})
        name = body.get("name") if isinstance(body, dict) else None
        try:
            graph = flows.load(name)
        except ValueError as exc:
            return flows_validation_response(exc)
        except FileNotFoundError as exc:
            return JSONResponse(status_code=404, content={"detail": str(exc)})
        # Same preflight the validate endpoint runs: an invalid graph is a
        # 400 with reasons (never a started job generated from junk).
        errors = validate_preflight(graph)
        if errors:
            return JSONResponse(status_code=400, content={"errors": errors})
        try:
            # Deliverable configs/flow_<slug>.yaml first, then start.
            config_path = config_gen.generate(graph)
            pid = runner.start(config_path)
        except runner.JobRunningError as exc:
            return JSONResponse(status_code=409, content={"detail": str(exc)})
        except (FileNotFoundError, ValueError, RuntimeError) as exc:
            return JSONResponse(status_code=status_for_error(exc),
                                content={"detail": str(exc)})
        return {"ok": True, "pid": pid}

    @app.get("/api/run/status")
    def run_status():
        return runner.status()

    @app.post("/api/run/stop")
    def run_stop():
        try:
            stop_flag = runner.request_stop()
        except runner.NoJobRunningError as exc:
            return JSONResponse(status_code=409, content={"detail": str(exc)})
        except RuntimeError as exc:
            return JSONResponse(status_code=status_for_error(exc),
                                content={"detail": str(exc)})
        return {"ok": True, "stop_flag": stop_flag}

    if not dev and DIST_DIR.is_dir():
        app.mount("/", StaticFiles(directory=str(DIST_DIR), html=True),
                  name="static")
    return app


app = create_app(dev=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description="flow MVP FastAPI server")
    parser.add_argument("--port", type=int, default=None,
                        help="server port (default "
                             + str(DEFAULT_PORT) + "; FLOW_PORT env wins "
                             "when --port is absent)")
    parser.add_argument("--dev", action="store_true",
                        help="dev mode: CORS for the Vite dev server, no "
                             "flow/dist static mount")
    parser.add_argument("--host", default=DEFAULT_HOST)
    args = parser.parse_args(argv)
    port = resolve_port(args.port, os.environ)
    import uvicorn
    uvicorn.run(create_app(dev=args.dev), host=args.host, port=port)


if __name__ == "__main__":
    main()
