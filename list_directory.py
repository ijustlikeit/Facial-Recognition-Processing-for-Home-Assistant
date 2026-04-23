"""
Pyscript Home Assistant service: csv file 
Lists a directory and writes a CSV (underscore separated) file with a columns facelabel, name, area, pctlabel, nbr, date, timejpg. 
This file will be used in Grafana using infinity source and UQL to display images detected by the facial recognition process.

Service call example:
  service: pyscript.list_directory
  data:
    directory: /config/www/AI/Don
    output_file: /config/www/grafana/don.txt
"""

import asyncio
import csv
import functools
import io
import os
from pathlib import Path


@service
async def list_directory(directory: str = None, output_file: str = None):
    """
    List a directory and save the comma-delimited result to a file.

    Parameters
    ----------
    directory   : str  – absolute path of the directory to list
    output_file : str  – absolute path of the file to write the listing into
    """
    if not directory:
        log.error("list_directory: 'directory' parameter is required")
        return
    if not output_file:
        log.error("list_directory: 'output_file' parameter is required")
        return

    loop = asyncio.get_running_loop()

    is_dir = await loop.run_in_executor(None, os.path.isdir, directory)
    if not is_dir:
        log.error(f"list_directory: Not a directory: {directory}")
        return

    log.info(f"list_directory: listing '{directory}' → '{output_file}'")

    try:
        entries = await loop.run_in_executor(None, os.listdir, directory)

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["facelabel_name_area_pctlabel_nbr_date_timejpg"])
        writer.writerows([[e] for e in sorted(entries)])
        listing = buf.getvalue()

        out = Path(output_file)
        await loop.run_in_executor(None, functools.partial(out.parent.mkdir, parents=True, exist_ok=True))
        await loop.run_in_executor(None, functools.partial(out.write_text, listing, encoding="utf-8"))

        log.info(f"list_directory: wrote {len(listing)} chars to '{output_file}'")
    except OSError as exc:
        log.error(f"list_directory: error — {exc}")
