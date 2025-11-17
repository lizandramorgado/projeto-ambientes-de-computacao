#!/usr/bin/env python3
from flask import Flask, jsonify
import importlib.util
from pathlib import Path
import traceback

app = Flask(__name__)

# Path to the existing scrapper script (note: filename contains a hyphen so we load by path)
SCRAPPER_PATH = Path(__file__).resolve().parent / "service.py"


def load_scraper_module():
    """Dynamically load the scrapper module from file path.

    Returns the loaded module or raises an exception.
    """
    spec = importlib.util.spec_from_file_location("scrapper_service_module", str(SCRAPPER_PATH))
    module = importlib.util.module_from_spec(spec)
    # This will execute the top-level of service.py (imports, function defs)
    spec.loader.exec_module(module)
    return module


@app.route("/pdb/<pdbid>", methods=["GET"])
def pdb_endpoint(pdbid: str):
    """Endpoint that loads service and calls get_pdb_info(pdbid).

    Returns JSON with the scraped info or an error JSON on failure.
    """
    try:
        module = load_scraper_module()
    except Exception as e:
        return jsonify({
            "error": "Failed to load service.py",
            "details": str(e),
            "trace": traceback.format_exc()
        }), 500

    get_pdb_info = getattr(module, "get_pdb_info", None)
    if not callable(get_pdb_info):
        return jsonify({"error": "get_pdb_info not found in service.py"}), 500

    try:
        result = get_pdb_info(pdbid)
        # Ensure we return JSON-serializable data
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "error": f"Failed to fetch PDB info for {pdbid}",
            "details": str(e),
            "trace": traceback.format_exc()
        }), 500


@app.route("/")
def index():
    # Serve the single-page frontend (static/index.html)
    return app.send_static_file("index.html")


if __name__ == "__main__":
    # Simple local server for development/testing
    app.run(host="127.0.0.1", port=5000, debug=True)
