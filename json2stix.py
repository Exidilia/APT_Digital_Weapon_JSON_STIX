import os
import json
import uuid
from datetime import datetime

def hash_type_from_string(type_str):
    t = type_str.lower()
    if 'md5' in t:
        return 'MD5'
    if 'sha1' in t:
        return 'SHA-1'
    if 'sha256' in t or 'sha-256' in t:
        return 'SHA-256'
    if 'sha512' in t or 'sha-512' in t:
        return 'SHA-512'
    return None

def make_file_indicator(row):
    hash_val = row.get('Hash')
    type_val = row.get('Type')
    name_val = row.get('Name')
    first_seen = row.get('First_Seen')
    resource = row.get('resource')
    hash_type = hash_type_from_string(type_val or '')
    if not hash_type:
        if hash_val:
            if len(hash_val) == 32:
                hash_type = 'MD5'
            elif len(hash_val) == 40:
                hash_type = 'SHA-1'
            elif len(hash_val) == 64:
                hash_type = 'SHA-256'
    hashes = {hash_type: hash_val} if hash_type and hash_val else {}
    pattern = None
    if hashes:
        for k, v in hashes.items():
            pattern = f"[file:hashes.'{k}' = '{v}']"
            break
    else:
        pattern = f"[file:name = '{name_val}']"
    indicator = {
        "type": "indicator",
        "spec_version": "2.1",
        "id": f"indicator--{uuid.uuid4()}",
        "created": datetime.utcnow().isoformat() + 'Z',
        "modified": datetime.utcnow().isoformat() + 'Z',
        "name": name_val or hash_val,
        "description": f"File indicator for {name_val or hash_val}",
        "pattern": pattern,
        "pattern_type": "stix",
        "valid_from": (first_seen + 'Z') if first_seen and 'T' in first_seen else datetime.utcnow().isoformat() + 'Z',
    }
    if resource:
        indicator["external_references"] = [{"source_name": "resource", "url": resource}]
    return indicator

def convert_json_to_stix(json_path, stix_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        rows = json.load(f)
    stix_objs = []
    for row in rows:
        ind = make_file_indicator(row)
        stix_objs.append(ind)
    bundle = {
        "type": "bundle",
        "id": f"bundle--{uuid.uuid4()}",
        "spec_version": "2.1",
        "objects": stix_objs
    }
    os.makedirs(os.path.dirname(stix_path), exist_ok=True)
    with open(stix_path, 'w', encoding='utf-8') as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2)

def main():
    input_root = os.path.join(os.path.dirname(__file__), 'APT_DIGITAL_WEAPON_JSON')
    output_root = os.path.join(os.path.dirname(__file__), 'APT_DIGITAL_WEAPON_STIX')
    for dirpath, _, files in os.walk(input_root):
        for file in files:
            if file.endswith('.json'):
                rel_dir = os.path.relpath(dirpath, input_root)
                in_path = os.path.join(dirpath, file)
                out_dir = os.path.join(output_root, rel_dir)
                out_file = os.path.splitext(file)[0] + '.stix.json'
                out_path = os.path.join(out_dir, out_file)
                print(f"Converting {in_path} -> {out_path}")
                convert_json_to_stix(in_path, out_path)

if __name__ == "__main__":
    main()
