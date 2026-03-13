#!/usr/bin/env python3
"""
Grafana Dashboard Setup Script

This script configures and imports the Agent Analytics Grafana dashboards.
The source JSON files are generic and shareable - this script customizes them
with your specific GCP project, BigQuery dataset, and Grafana datasource UID,
then automatically imports them into your Grafana instance.

Usage:
    python3 setup_dashboards.py --project PROJ --dataset DATASET --table TABLE --url URL --user USER --folder FOLDER
"""

import json
import os
import sys
import base64
import getpass
import argparse
import urllib.request

DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(DASHBOARD_DIR, "configured")

DASHBOARD_FILES = [
    "grafana_landing_page.template.json",
    "grafana_finops_dashboard.template.json",
    "grafana_chat_dashboard.template.json",
    "grafana_diagnostics_dashboard.template.json",
    "grafana_guide_dashboard.template.json",
]


def connect_grafana(args):
    """Connect to Grafana and return URL + auth header."""
    grafana_url = args.url or input("Enter Grafana URL [http://localhost:3000]: ").strip() or "http://localhost:3000"
    grafana_user = args.user or input("Enter Grafana username: ").strip()
    grafana_pass = args.password or getpass.getpass("Enter Grafana password: ")

    if not grafana_user or not grafana_pass:
        print("❌ Grafana credentials are required.")
        sys.exit(1)

    credentials = base64.b64encode(f"{grafana_user}:{grafana_pass}".encode()).decode()
    auth_header = f"Basic {credentials}"
    return grafana_url, auth_header


def get_datasource_uid(grafana_url, auth_header):
    """Auto-detect the BigQuery datasource UID."""
    try:
        req = urllib.request.Request(f"{grafana_url}/api/datasources")
        req.add_header("Authorization", auth_header)
        with urllib.request.urlopen(req, timeout=5) as resp:
            datasources = json.loads(resp.read())
            for ds in datasources:
                if ds.get("type") == "grafana-bigquery-datasource":
                    return ds["uid"], ds["name"]
    except Exception as e:
        print(f"   ⚠️  Could not connect to Grafana: {e}")
    return None, None


def get_or_create_folder(grafana_url, auth_header, folder_name):
    """Get the folder ID for a folder name, creating it if it doesn't exist."""
    if not folder_name:
        return 0, "General"

    # Search for existing folder
    try:
        req = urllib.request.Request(f"{grafana_url}/api/folders")
        req.add_header("Authorization", auth_header)
        with urllib.request.urlopen(req, timeout=5) as resp:
            folders = json.loads(resp.read())
            for folder in folders:
                if folder.get("title").lower() == folder_name.lower():
                    return folder["id"], folder["title"]
    except Exception as e:
        print(f"   ⚠️  Folder search failed: {e}")

    # Create folder if not found
    try:
        print(f"   📂 Creating folder: '{folder_name}'...")
        payload = json.dumps({"title": folder_name}).encode("utf-8")
        req = urllib.request.Request(f"{grafana_url}/api/folders", data=payload, method="POST")
        req.add_header("Authorization", auth_header)
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read())
            return result["id"], result["title"]
    except Exception as e:
        print(f"   ❌ Folder creation failed: {e}")
        return 0, "General"


def import_dashboard(grafana_url, auth_header, dashboard_data, folder_id=0):
    """Import a dashboard JSON into Grafana via the API."""
    # Ensure the dashboard has a UID but NO internal ID to allow folder reassignment
    dashboard_data.pop("id", None)
    
    payload = json.dumps({
        "dashboard": dashboard_data,
        "overwrite": True,
        "folderId": int(folder_id)
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{grafana_url}/api/dashboards/db",
        data=payload,
        method="POST"
    )
    req.add_header("Authorization", auth_header)
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"   ❌ HTTP Error {e.code}: {error_body}")
        raise e


def main():
    parser = argparse.ArgumentParser(description="Configure and import Grafana dashboards for Agent Analytics.")
    parser.add_argument("--project", help="GCP Project ID")
    parser.add_argument("--dataset", help="BigQuery Dataset name")
    parser.add_argument("--table", help="Base BigQuery Table name")
    parser.add_argument("--url", help="Grafana URL")
    parser.add_argument("--user", help="Grafana Username")
    parser.add_argument("--password", help="Grafana Password")
    parser.add_argument("--folder", help="Target Grafana Folder")
    parser.add_argument("--datasource-uid", help="Manual Grafana Datasource UID")
    args = parser.parse_args()

    print("=" * 60)
    print("  Agent Analytics - Grafana Dashboard Setup")
    print("=" * 60)
    print()

    # Step 1: GCP Project
    gcp_project = args.project or input("Enter your GCP Project ID: ").strip()
    if not gcp_project:
        print("❌ GCP Project ID is required. Exiting.")
        sys.exit(1)

    # Step 2: BQ Dataset
    bq_dataset = args.dataset or input("Enter your BigQuery Dataset: ").strip()
    if not bq_dataset:
        print("❌ BigQuery Dataset is required. Exiting.")
        sys.exit(1)

    # Step 3: Base Table
    bq_table = args.table or input("Enter your Base BigQuery Table: ").strip()
    if not bq_table:
        print("❌ BigQuery Table is required. Exiting.")
        sys.exit(1)

    # Step 4: Connect to Grafana
    print("\n🔌 Connecting to Grafana...")
    grafana_url, auth_header = connect_grafana(args)

    # Step 5: Folder Selection
    folder_name = args.folder or input(f"Enter destination Folder Name: ").strip()
    if not folder_name:
        folder_name = "General"
    
    folder_id, folder_title = get_or_create_folder(grafana_url, auth_header, folder_name)
    print(f"✅ Target Folder: '{folder_title}' (id: {folder_id})")

    # Step 6: Datasource detection
    ds_uid = args.datasource_uid
    auto_name = "BigQuery"
    
    if not ds_uid:
        auto_uid, detected_name = get_datasource_uid(grafana_url, auth_header)
        if auto_uid:
            auto_name = detected_name
            print(f"\n✅ Auto-detected BigQuery datasource: '{auto_name}' (uid: {auto_uid})")
            use_auto = input("Use this datasource? [Y/n]: ").strip().lower()
            if use_auto != "n":
                ds_uid = auto_uid
            else:
                ds_uid = input("Enter your Grafana BigQuery datasource UID: ").strip()
        else:
            print("\n⚠️  Could not auto-detect datasource.")
            ds_uid = input("Enter your Grafana BigQuery datasource UID: ").strip()

    if not ds_uid:
        print("❌ Datasource UID is required. Exiting.")
        sys.exit(1)

    # Step 7: Configure and import dashboards
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fqdn = f"{gcp_project}.{bq_dataset}"

    print(f"\n📝 Configuring dashboards...")
    print(f"   Project:    {gcp_project}")
    print(f"   Dataset:    {bq_dataset}")
    print(f"   Base Table: {bq_table}")
    print(f"   Datasource: {ds_uid}")
    print()

    configured_dashboards = []

    for filename in DASHBOARD_FILES:
        src_path = os.path.join(DASHBOARD_DIR, filename)
        if not os.path.exists(src_path):
            print(f"   ⚠️  Skipping {filename} (not found)")
            continue

        with open(src_path, "r") as f:
            data = json.load(f)

        # Update hidden textbox defaults
        for var in data.get("templating", {}).get("list", []):
            if var.get("name") == "gcp_project":
                var["current"] = {"text": gcp_project, "value": gcp_project}
                var["options"] = [{"text": gcp_project, "value": gcp_project}]
                var["hide"] = 0
            elif var.get("name") == "bq_dataset":
                var["current"] = {"text": bq_dataset, "value": bq_dataset}
                var["options"] = [{"text": bq_dataset, "value": bq_dataset}]
                var["hide"] = 0
            elif var.get("name") == "bq_table":
                var["current"] = {"text": bq_table, "value": bq_table}
                var["options"] = [{"text": bq_table, "value": bq_table}]
                var["hide"] = 0
            elif var.get("name") == "datasource":
                var["current"] = {"text": auto_name, "value": ds_uid}
                var["options"] = [{"text": auto_name, "value": ds_uid}]
                var["hide"] = 0
            elif var.get("type") == "query":
                # Hardcode project/dataset in variable queries (template vars don't resolve here)
                q = var.get("query", "")
                if isinstance(q, dict) and "rawSql" in q:
                    q["rawSql"] = q["rawSql"].replace("${gcp_project}.${bq_dataset}", fqdn).replace("${bq_table}", bq_table)
                    q["project"] = gcp_project
                elif isinstance(q, str):
                    var["query"] = q.replace("${gcp_project}.${bq_dataset}", fqdn).replace("${bq_table}", bq_table)
                
                var["datasource"] = {
                    "type": "grafana-bigquery-datasource",
                    "uid": ds_uid
                }

        # Save configured copy - strip '.template' from filename for the output
        clean_filename = filename.replace(".template.json", ".json")
        out_path = os.path.join(OUTPUT_DIR, clean_filename)
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)
        
        configured_dashboards.append((clean_filename, data))
        print(f"   ✅ Configured: {clean_filename}")

    # Step 8: Import into Grafana
    print(f"\n🚀 Importing dashboards into Grafana...")
    for filename, data in configured_dashboards:
        try:
            result = import_dashboard(grafana_url, auth_header, data, folder_id)
            url = result.get("url", "")
            print(f"   ✅ Imported: {filename} → {grafana_url}{url} (Status: {result.get('status')})")
        except Exception as e:
            print(f"   ❌ Failed: {filename} — {e}")

    print(f"\n🎉 All done! Open Grafana to see your dashboards in the '{folder_title}' folder.")


if __name__ == "__main__":
    main()
