#!/bin/python

import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

CACHE_DIR = Path.home() / ".local" / "share" / "pypdb"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def fetch_pdb_info(pdbid):
    # Scrape RCSB PDB information from HTML
    url = f"https://www.rcsb.org/structure/{pdbid}"

    try:
        req = requests.get(url, timeout=10)
    except requests.RequestException as e:
        print(f"Network error: {e}")
        sys.exit(1)

    # HTTP status handling
    if 400 <= req.status_code <= 499:
        print(f"Client error ({req.status_code}).")
        if req.status_code == 429:
            print("Too many requests; you are being rate-limited.")
            retry_after = req.headers.get("Retry-After")
            if retry_after:
                print(f"Retry-After: {retry_after} seconds.")
        print("Exiting...")
        sys.exit(1)

    if 500 <= req.status_code <= 599:
        print(f"Server error ({req.status_code}).")
        print("Exiting...")
        sys.exit(1)

    if 200 <= req.status_code <= 299:
        print(f"Request successful ({req.status_code}). Parsing...")
    else:
        print(f"Unexpected response ({req.status_code}). Exiting...")
        sys.exit(1)

    soup = BeautifulSoup(req.text, "html.parser")

    def get_text(elem_id, split_colon=True):
        e = soup.find(id=elem_id)
        if not e or not e.text:
            return None
        text = e.text.replace("\xa0", " ").strip()
        if split_colon and ":" in text:
            # only split when caller explicitly wants prefix removal
            text = text.split(":", 1)[1].strip()
        return text

    info = {
        "pdbid": pdbid,
        "title": None,
        #"title": soup.title.text if soup.title else None,
        "classification": (get_text("header_classification").capitalize()),
        "organism": get_text("header_organism"),
        "method": (get_text("exp_header_0_method").capitalize()),
        "resolution": (
            get_text("exp_header_0_em_resolution") or
            get_text("exp_header_0_diffraction_resolution")
        ),
        "publication_title": None,
        "authors": [],
        "doi": None,
        "related_structures": None,
        "abstract": get_text("abstract", split_colon=False),
    }

    # Title
    if soup.title and soup.title.text:
        title = soup.title.text.replace("\xa0", " ").strip()
        if ":" in title:
            title = title.split(":", 1)[1].strip()
        info["title"] = title

    citation = soup.find("div", id="primarycitation")
    if citation:
        h4 = citation.find("h4")
        if h4: info["publication_title"] = h4.text.strip()
        # Authors
        authors = [a.text.strip() for a in citation.find_all("a", class_="querySearchLink")]
        info["authors"] = [a for a in authors if not a.isnumeric()]
        # DOI
        doi = soup.find("li", id="pubmedDOI")
        if doi: info["doi"] = doi.text.replace("DOI:\xa0", "").strip()
        # Related structures
        relatedst = [a.text.strip() for a in soup.select("li#citationPrimaryRelatedStructures a[href]") if a.text.strip()]
        if relatedst: info["related_structures"] = relatedst

    return info

def load_from_cache(pdbid: str):
    # Try to load cached info; return dict or None.
    path = CACHE_DIR / f"{pdbid.lower()}.json"
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_to_cache(pdbid: str, data: dict):
    # Save scraped info to cache as JSON.
    path = CACHE_DIR / f"{pdbid.lower()}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def cache_image(pdbid: str):
    # Fetch and cache structure image if not cached.
    img_url = f"https://cdn.rcsb.org/images/structures/{pdbid}_assembly-1.jpeg"
    img_path = CACHE_DIR / f"{pdbid}.jpeg"

    if not img_path.exists():
        print(f"Downloading image for {pdbid}...")
        img_data = requests.get(img_url, timeout=10).content
        with img_path.open("wb") as f:
            f.write(img_data)
    return img_path

def get_pdb_info(pdbid: str):
    # Main helper: get info from cache or scrape.
    pdbid = pdbid.lower()

    cached = load_from_cache(pdbid)
    img_path = CACHE_DIR / f"{pdbid}.jpeg"

    if cached and img_path.exists():
        print(f"Loaded {pdbid} from cache.")
        cached["local_image"] = str(img_path if img_path.exists() else None)
        return cached

    print(f"Cache not found for {pdbid}. Fetching from RCSB...")
    info = fetch_pdb_info(pdbid)

    # cache image and store local path
    cache_image(pdbid)
    info["local_image"] = str(img_path) if img_path else None

    save_to_cache(pdbid, info)
    return info

if __name__ == "__main__":
    import argparse
    import sys
    import os
    import contextlib

    parser = argparse.ArgumentParser(description="Fetch one or more PDB IDs and cache results.")
    parser.add_argument("pdbids", nargs="+", help="One or more PDB IDs (e.g. 7wyv 1tup ...)")
    parser.add_argument("-s", "--silent", action="store_true",
                        help="Silent mode: produce no output, just save JSON/image to cache.")
    args = parser.parse_args()

    any_error = False
    for pdbid in args.pdbids:
        pdbid = pdbid.strip()
        if not pdbid:
            continue
        try:
            if args.silent:
                with open(os.devnull, "w") as devnull, \
                     contextlib.redirect_stdout(devnull), \
                     contextlib.redirect_stderr(devnull):
                    data = get_pdb_info(pdbid)
            else:
                data = get_pdb_info(pdbid)
        except Exception as e:
            print(f"Error fetching {pdbid}: {e}", file=sys.stderr)
            any_error = True
            continue

        if not args.silent:
            print(f"--- {pdbid} ---")
            for k, v in data.items():
                print(f"{k}: {v}")
            print()

    if any_error:
        raise SystemExit(1)