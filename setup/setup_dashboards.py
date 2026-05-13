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
import urllib.error

SETUP_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = os.path.join(os.path.dirname(SETUP_DIR), "dashboard_templates")
OUTPUT_DIR = os.path.join(SETUP_DIR, "configured")

DASHBOARD_FILES = [
    "grafana_landing_page.template.json",
    "grafana_finops_dashboard.template.json",
    "grafana_chat_dashboard.template.json",
    "grafana_diagnostics_dashboard.template.json",
    "grafana_traces_dashboard.template.json",
    "grafana_llm_calls_dashboard.template.json",
    "grafana_guide_dashboard.template.json",
]


def connect_grafana(args):
    """Connect to Grafana and return URL + auth header."""
    grafana_url = args.url or input("Enter Grafana URL [http://localhost:3000]: ").strip() or "http://localhost:3000"
    grafana_user = args.user or input("Enter Grafana username: ").strip()
    grafana_pass = args.password or getpass.getpass("Enter Grafana password: ")

    if not grafana_user or not grafana_pass:
        print("❌ Grafana credentials are required for direct upload.")
        return None, None

    credentials = base64.b64encode(f"{grafana_user}:{grafana_pass}".encode()).decode()
    auth_header = f"Basic {credentials}"

    # Test the connection
    try:
        req = urllib.request.Request(f"{grafana_url}/api/user")
        req.add_header("Authorization", auth_header)
        with urllib.request.urlopen(req, timeout=5) as resp:
            pass # Login successful
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print(f"\n❌ Login Failed: Invalid username or password for {grafana_url}.")
        else:
            print(f"\n❌ Login Failed: HTTP Error {e.code} - {e.reason}")
        return None, None
    except urllib.error.URLError as e:
        print(f"\n❌ Connection Failed: Could not reach Grafana at {grafana_url}. Is it running?")
        return None, None
    except Exception as e:
        print(f"\n❌ Unexpected error connecting to Grafana: {e}")
        return None, None

    return grafana_url, auth_header


def get_datasource_uid(grafana_url, auth_header):
    """Auto-detect the BigQuery datasource UID."""
    if not grafana_url or not auth_header:
        return None, None
    try:
        req = urllib.request.Request(f"{grafana_url}/api/datasources")
        req.add_header("Authorization", auth_header)
        with urllib.request.urlopen(req, timeout=5) as resp:
            datasources = json.loads(resp.read())
            for ds in datasources:
                if ds.get("type") in ["grafana-bigquery-datasource", "grafana-google-bigquery-datasource"]:
                    return ds["uid"], ds["name"]
    except Exception as e:
        print(f"   ⚠️  Could not fetch datasources from Grafana: {e}")
    return None, None

def create_adc_datasource(grafana_url, auth_header, project_id):
    """Create a BigQuery Datasource using Application Default Credentials (ADC)."""
    if not grafana_url or not auth_header:
        return None, None
    payload = json.dumps({
        "name": "BigQuery (ADC Auto-Created)",
        "type": "grafana-bigquery-datasource",
        "access": "proxy",
        "isDefault": True,
        "jsonData": {
            "authenticationType": "gce",
            "defaultProject": project_id
        }
    }).encode("utf-8")

    req = urllib.request.Request(f"{grafana_url}/api/datasources", data=payload, method="POST")
    req.add_header("Authorization", auth_header)
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read())
            return result["datasource"]["uid"], result["datasource"]["name"]
    except Exception as e:
        print(f"   ❌ Failed to auto-create BigQuery datasource: {e}")
        return None, None


def get_or_create_folder(grafana_url, auth_header, folder_name):
    """Get the folder ID for a folder name, creating it if it doesn't exist."""
    if not grafana_url or not auth_header:
        return 0, "Local-Only"
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
    if not grafana_url or not auth_header:
        return {"status": "skipped", "message": "Local generation only"}
    
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
    parser.add_argument("--datasource", help="Manual Grafana Datasource UID")
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

    # Step 4: Optional Direct Upload
    do_upload = (args.url and args.user) or input("\n📤 Would you like to upload directly to Grafana? (y/n) [n]: ").strip().lower() == 'y'
    grafana_url, auth_header = None, None
    if do_upload:
        if args.url and args.user:
            # If provided via CLI, use those
            print("\n🔌 Connecting to Grafana (using CLI credentials)...")
        else:
            print("\n🔌 Connecting to Grafana...")
        grafana_url, auth_header = connect_grafana(args)
    
    # Step 5: Datasource detection or placeholder
    ds_uid = args.datasource
    auto_name = "BigQuery"
    
    if do_upload and not ds_uid:
        auto_uid, detected_name = get_datasource_uid(grafana_url, auth_header)
        if auto_uid:
            auto_name = detected_name
            print(f"\n✅ Auto-detected BigQuery datasource: '{auto_name}' (uid: {auto_uid})")
            use_auto = input("Use this datasource? [Y/n]: ").strip().lower()
            if use_auto != "n":
                ds_uid = auto_uid
    
    if not ds_uid:
        if do_upload:
             ds_uid = input("Enter your Grafana BigQuery datasource UID: ").strip()
        else:
             ds_uid = "bigquery-default"
             print(f"\nℹ️  Using placeholder datasource UID: {ds_uid}")

    # Step 6: Folder Selection
    folder_id = 0
    folder_title = "General"
    if do_upload:
        folder_name = args.folder or input(f"Enter destination Folder Name: ").strip()
        if not folder_name:
            folder_name = "General"
        folder_id, folder_title = get_or_create_folder(grafana_url, auth_header, folder_name)
        print(f"✅ Target Folder: '{folder_title}' (id: {folder_id})")

    # Step 7: Configure and import dashboards
    os.makedirs(OUTPUT_DIR, exist_ok=True)

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
            template_str = f.read()

        # Aggressive string replacement
        template_str = template_str.replace("${gcp_project}", gcp_project)
        template_str = template_str.replace("${bq_dataset}", bq_dataset)
        template_str = template_str.replace("${bq_table}", bq_table)
        template_str = template_str.replace("${datasource}", ds_uid)
        
        try:
            data = json.loads(template_str)
        except json.JSONDecodeError as e:
            print(f"   ❌ Failed to parse {filename}: {e}")
            continue

        # Save configured copy
        clean_filename = filename.replace(".template.json", ".json")
        out_path = os.path.join(OUTPUT_DIR, clean_filename)
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)
        
        configured_dashboards.append((clean_filename, data))
        print(f"   ✅ Configured: {clean_filename}")

    # Step 8: Import into Grafana
    if do_upload and grafana_url and auth_header:
        print(f"\n🚀 Importing dashboards into Grafana...")
        for filename, data in configured_dashboards:
            try:
                result = import_dashboard(grafana_url, auth_header, data, folder_id)
                url = result.get("url", "")
                print(f"   ✅ Imported: {filename} → {grafana_url}{url}")
            except Exception as e:
                print(f"   ❌ Failed: {filename} — {e}")

    print(f"\n🎉 Setup complete! Configured JSON files are in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
