# PDB Scraper controller

This repository contains the original scrapper script `scrapper-service.py` and a small Flask controller `controller.py` that exposes an HTTP endpoint:

- GET /pdb/{pdbid}

The endpoint will load `scrapper-service.py` dynamically and call `get_pdb_info(pdbid)`, returning the scraped data as JSON.

Quick start (Windows PowerShell):

```powershell
python -m pip install -r requirements.txt
python controller.py
# then visit http://127.0.0.1:5000/pdb/7wyv (example)
```

Notes:
- The scraper file is named `scrapper-service.py` (contains a hyphen). The controller loads it by path to avoid import-name issues.
- Starting the server does not pre-run network calls. The scraper's imports (requests, bs4) must be installed to call the endpoint successfully.
