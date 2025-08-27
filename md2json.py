import os
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed


logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def parse_markdown_file(md_path):
    import re
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # Find table header and rows
        table = []
        header = None
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('|') and line.endswith('|'):
                cells = [cell.strip() for cell in line.strip('|').split('|')]
                # Skip alignment row
                if set(cells[0]) == {':', '-'}:
                    continue
                if header is None:
                    header = cells
                else:
                    # Only add rows with correct number of columns
                    if len(cells) == len(header):
                        row = dict(zip(header, cells))
                        # Look for links in each cell
                        for key, val in row.items():
                            match = link_pattern.search(val)
                            if match:
                                row['resource'] = match.group(2)
                                # Optionally, keep the text only in the original cell
                                row[key] = match.group(1)
                                break
                        table.append(row)
        return md_path, table
    except Exception as e:
        logging.error(f"Failed to parse {md_path}: {e}")
        return md_path, None

def parse_markdown_files_to_json(root_dir, max_workers=8):
    md_files = []

    # Collect markdown files first
    for root, _, files in os.walk(root_dir):
        md_files.extend([
            os.path.join(root, f)
            for f in files
            if f.endswith('.md') and f.lower() != 'readme.md'
        ])

    logging.info(f"Found {len(md_files)} markdown files in {root_dir}")

    # Prepare output directory
    output_root = os.path.join(os.path.dirname(root_dir.rstrip('/')), 'APT_DIGITAL_WEAPON_JSON')
    os.makedirs(output_root, exist_ok=True)

    # Use ThreadPoolExecutor to parse files concurrently
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {executor.submit(parse_markdown_file, md_file): md_file for md_file in md_files}
        for future in as_completed(future_to_path):
            file_path = future_to_path[future]
            rel_path = os.path.relpath(file_path, root_dir)
            md_json = future.result()[1]
            if md_json is not None:
                # Write JSON file to output directory, preserving relative path
                json_rel_path = os.path.splitext(rel_path)[0] + '.json'
                json_out_path = os.path.join(output_root, json_rel_path)
                os.makedirs(os.path.dirname(json_out_path), exist_ok=True)
                with open(json_out_path, 'w', encoding='utf-8') as jf:
                    json.dump(md_json, jf, ensure_ascii=False, indent=2)
                logging.info(f"Converted {rel_path} -> {json_rel_path}")
            else:
                logging.warning(f"Skipped {rel_path} due to errors")

if __name__ == "__main__":
    repo_root_dir = "."  # adjust this path
    parse_markdown_files_to_json(repo_root_dir)
    logging.info(f"Completed conversion of markdown files to JSON in APT_DIGITAL_WEAPON_JSON.")
