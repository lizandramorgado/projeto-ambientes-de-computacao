# PDB Scraper controller

This repository contains the original scrapper script `service.py` and a small Flask controller `controller.py` that exposes an HTTP endpoint:

- GET /pdb/{pdbid}

The endpoint will load `service.py` dynamically and call `get_pdb_info(pdbid)`, returning the scraped data as JSON.

Quick start (Windows PowerShell):

```powershell
python -m pip install -r requirements.txt
python controller.py
# then visit http://127.0.0.1:5000/ 
```

Notes:
- The scraper file is named `service.py`. The controller loads it by path to avoid import-name issues.
- Starting the server does not pre-run network calls. The scraper's imports (requests, bs4) must be installed to call the endpoint successfully.
