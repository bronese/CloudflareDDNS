import time
import os
import requests
import sys

# --- Configuration & Environment Variables ---
# These are typically set in your environment (e.g., Dockerfile, .env file, system variables)
domain_env = os.getenv("DOMAIN")  # e.g., example.com (your zone name)
name_env = os.getenv("NAME")  # e.g., dyndns, www, or @ for root. If not FQDN, DOMAIN will be appended.
record_type_env = os.getenv("RECORDTYPE") or "A"
ip_url = os.getenv("IPURL") or "http://ifconfig.me"
email = os.getenv("EMAIL") # Your Cloudflare account email
token = os.getenv("TOKEN") # Your Cloudflare API Token (Global API Key or specific token)
zone_id = os.getenv("ZONEID") # The Zone ID of your domain in Cloudflare
record_id_env = os.getenv("RECORDID") # Optional: if you know the specific record ID
selected_item_env = os.getenv("SELECTEDITEM") # Optional: index if NAME+TYPE yields multiple records

# Update interval
update_interval_str = os.getenv("UPDATEINTERVAL")
if update_interval_str and update_interval_str.isdigit():
    update_interval = int(update_interval_str)
    if update_interval < 60: # Minimum sensible interval
        print(f"[WARN] UPDATEINTERVAL '{update_interval}' is very short. Setting to 60 seconds.")
        update_interval = 60
else:
    update_interval = 300 # Default 5 minutes
    if update_interval_str :
        print(f"[WARN] Invalid UPDATEINTERVAL value '{update_interval_str}', using default {update_interval}s.")

# TTL for the DNS record
ttl_str = os.getenv("TTL")
if ttl_str and ttl_str.isdigit():
    ttl = int(ttl_str)
    if ttl < 1: # Cloudflare: 1 means "Auto", otherwise usually >=60 for specific durations
        print(f"[WARN] TTL value '{ttl}' is less than 1. Setting to 1 (auto).")
        ttl = 1
elif ttl_str == "1": # Explicitly "1" for Auto TTL
    ttl = 1
else:
    ttl = 1 # Default TTL (1 = Auto)
    if ttl_str:
        print(f"[WARN] Invalid TTL value '{ttl_str}', using default TTL {ttl} (auto).")

# --- Helper Functions ---
def get_current_timestamp():
    """Returns a formatted current timestamp."""
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

def get_headers(cf_email, cf_token):
    """Builds the standard headers for Cloudflare API requests."""
    return {
        "X-Auth-Email": cf_email,
        "Authorization": f"Bearer {cf_token}",
        "Content-Type": "application/json",
    }

def verify_auth(cf_email, cf_token):
    """Verifies Cloudflare API authentication."""
    headers = get_headers(cf_email, cf_token)
    try:
        response = requests.get(
            "https://api.cloudflare.com/client/v4/user", headers=headers, timeout=10
        )
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
        if response.json().get("success"):
            return True
        else:
            print(f"[ERROR] Failed to authenticate with Cloudflare. API success=false. Response: {response.json()}")
            return False
    except requests.exceptions.HTTPError as http_err:
        print(f"[ERROR] HTTP error during Cloudflare authentication: {http_err}")
        if hasattr(response, 'text'): print(f"  Response content: {response.text}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request exception during Cloudflare authentication: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred in verify_auth: {e}")
        return False

def get_public_ip(url_to_fetch_ip):
    """Fetches the public IP address from a given URL."""
    try:
        response = requests.get(url_to_fetch_ip, timeout=10)
        response.raise_for_status()
        ip_address = response.text.strip()
        if not ip_address: # Basic validation for an IP-like string could be added here
            print(f"[ERROR] IP address from {url_to_fetch_ip} is empty or invalid.")
            return None
        return ip_address
    except requests.exceptions.HTTPError as http_err:
        print(f"[ERROR] HTTP error while fetching IP from {url_to_fetch_ip}: {http_err}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Could not fetch IP from {url_to_fetch_ip}: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred in get_public_ip: {e}")
        return None

def get_all_dns_records(cf_email, cf_token, cf_zone_id):
    """Fetches all DNS records for a given Cloudflare zone."""
    headers = get_headers(cf_email, cf_token)
    print(f"[DEBUG] Requesting DNS records for Zone ID: {cf_zone_id}")
    try:
        response = requests.get(
            f"https://api.cloudflare.com/client/v4/zones/{cf_zone_id}/dns_records",
            headers=headers,
            timeout=20
        )
        response.raise_for_status()
        response_data = response.json()
        if response_data.get("success"):
            dns_records = response_data.get("result")
            if dns_records is None:
                 print(f"[ERROR] Cloudflare API success true, but no 'result' field for DNS records in zone {cf_zone_id}.")
                 return None
            if not dns_records:
                print(f"[INFO] No DNS records found in zone {cf_zone_id}.")
            else:
                print(f"[DEBUG] Successfully fetched {len(dns_records)} DNS records.")
            return dns_records
        else:
            print(f"[ERROR] Cloudflare API reported failure when fetching DNS records for zone {cf_zone_id}.")
            print(f"  Errors: {response_data.get('errors')}")
            print(f"  Messages: {response_data.get('messages')}")
            return None
    except requests.exceptions.HTTPError as http_err:
        print(f"[ERROR] HTTP error fetching DNS records: {http_err}")
        if hasattr(response, 'text'): print(f"  Response content: {response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request exception fetching DNS records: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred in get_all_dns_records: {e}")
        return None

def find_record_details_by_name_and_type(dns_records_list, target_name, target_type, selected_idx_str=None):
    """
    Finds a specific DNS record ID and name from a list based on name and type.
    """
    if dns_records_list is None:
        print("[ERROR] Cannot search for record: DNS records list is None (fetch failed).")
        return None, None
    if not dns_records_list:
        print("[DEBUG] No DNS records provided to search in find_record_details_by_name_and_type.")
        return None, None

    if not target_name:
        print("[ERROR] Target record name must be provided to find a record automatically.")
        return None, None
    
    print(f"[INFO] Searching for DNS record: Name='{target_name}', Type='{target_type}'")
    matches = [
        r for r in dns_records_list
        if r.get('name') == target_name and r.get('type') == target_type
    ]

    if not matches:
        print(f"[ERROR] No DNS record found with Name='{target_name}' and Type='{target_type}'.")
        return None, None

    if len(matches) == 1:
        record = matches[0]
        print(f"[SUCCESS] Found unique DNS record: Name='{record.get('name')}', Type='{record.get('type')}', ID='{record.get('id')}'")
        return record.get('id'), record.get('name')
    else: # Multiple matches
        print(f"[WARN] Multiple DNS records found for Name='{target_name}', Type='{target_type}':")
        for i, r_val in enumerate(matches):
            print(f"  Match {i}: ID='{r_val.get('id')}', Name='{r_val.get('name')}', Type='{r_val.get('type')}', Content='{r_val.get('content')}'")
        
        if selected_idx_str is not None:
            try:
                idx = int(selected_idx_str)
                if 0 <= idx < len(matches):
                    selected_record = matches[idx]
                    print(f"[INFO] Using record at index {idx} (SELECTEDITEM='{selected_idx_str}').")
                    return selected_record.get('id'), selected_record.get('name')
                else:
                    print(f"[ERROR] SELECTEDITEM index {idx} is out of range for {len(matches)} matches.")
                    return None, None
            except ValueError:
                print(f"[ERROR] SELECTEDITEM '{selected_idx_str}' is not a valid integer index.")
                return None, None
        else:
            print("[ERROR] Ambiguous record. Provide RECORDID or use SELECTEDITEM to choose from multiple matches.")
            return None, None

def main_update_dns(record_name_to_update, record_type_to_update, new_ip_address, 
                    cf_email, cf_token, cf_zone_id, cf_record_id, 
                    record_ttl_value, update_timestamp_str):
    """Updates a specific DNS record on Cloudflare."""
    print(f"[INFO] Preparing to update DNS record ID '{cf_record_id}' for '{record_name_to_update}' to IP '{new_ip_address}'.")
    headers = get_headers(cf_email, cf_token)
    data = {
        "content": new_ip_address,
        "name": record_name_to_update,
        "proxied": False, 
        "type": record_type_to_update,
        "comment": f"DDNS script update. IP set to {new_ip_address} at {update_timestamp_str}",
        "ttl": record_ttl_value
    }
    
    print(f"[DEBUG] DNS Update Payload: {data}")

    try:
        response = requests.put(
            f"https://api.cloudflare.com/client/v4/zones/{cf_zone_id}/dns_records/{cf_record_id}",
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        
        response_data = response.json()
        print("[DEBUG] DNS update API call processed.")

        if response_data.get("success"):
            updated_record_details = response_data.get("result", {})
            print(f"[SUCCESS] Successfully updated DNS record for '{record_name_to_update}'.")
            print(f"  Record ID: {updated_record_details.get('id')}")
            print(f"  New IP:    {updated_record_details.get('content')}")
            print(f"  Comment:   '{updated_record_details.get('comment')}'")
            return True
        else:
            print(f"[ERROR] Cloudflare API reported failure for DNS update of '{record_name_to_update}'.")
            print(f"  Errors: {response_data.get('errors')}")
            print(f"  Messages: {response_data.get('messages')}")
            return False
    except requests.exceptions.HTTPError as http_err:
        print(f"[ERROR] HTTP error during DNS update for '{record_name_to_update}': {http_err}")
        if hasattr(response, 'text'): print(f"  Response content: {response.text}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"[ERROR] Connection error during DNS update for '{record_name_to_update}': {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"[ERROR] Timeout during DNS update for '{record_name_to_update}': {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"[ERROR] General error during DNS update for '{record_name_to_update}': {req_err}")
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred in main_update_dns: {e}")
    return False

# --- Main Script Execution ---
if __name__ == "__main__":
    script_start_time = time.time()
    
    print("\n" + "="*70)
    print(f" Cloudflare Dynamic DNS Updater Script - Started at {get_current_timestamp()}")
    print("="*70 + "\n")

    print("--- Initial Configuration ---")
    email_hidden = email[:2] + "****" + email[len(email)-4:] if email and len(email) > 6 else "Not Set"
    print(f"  Cloudflare Email:         {email_hidden}")
    print(f"  Cloudflare Zone ID:       {zone_id or 'Not Set'}")
    print(f"  Cloudflare Token:         {'Set' if token else 'Not Set'}")
    print(f"  Domain/Zone (DOMAIN):     {domain_env or 'Not Set'}")
    print(f"  Record Name (NAME):       {name_env or 'Not Set'}")
    print(f"  Record Type (RECORDTYPE): {record_type_env}")
    print(f"  Record ID (RECORDID):     {record_id_env or 'Not set, will attempt to find'}")
    print(f"  Public IP URL (IPURL):    {ip_url}")
    print(f"  Record TTL:               {ttl}")
    print(f"  Update Interval:          {update_interval} seconds")
    print(f"  Selected Item (SELECTEDITEM): {selected_item_env or 'Not set'}")
    print("-----------------------------\n")

    # Critical Environment Variables Check
    required_vars_map = {"EMAIL": email, "TOKEN": token, "ZONEID": zone_id}
    missing_critical_vars = [k for k, v in required_vars_map.items() if not v]
    if missing_critical_vars:
        print(f"[FATAL] Missing critical environment variables: {', '.join(missing_critical_vars)}. Exiting.")
        sys.exit(1)

    if not record_id_env and not name_env and not domain_env:
        print("[FATAL] Must provide either RECORDID, or (NAME and/or DOMAIN). Exiting.")
        sys.exit(1)

    # Determine target record name (FQDN)
    target_record_name_fqdn = None
    if name_env:
        if name_env == "@":
            if domain_env:
                target_record_name_fqdn = domain_env
                print(f"[INFO] NAME is '@', targeting root domain: '{target_record_name_fqdn}'.")
            else:
                print("[FATAL] NAME is '@' but DOMAIN (zone name) is not set. Exiting.")
                sys.exit(1)
        elif domain_env:
            if not name_env.endswith(f".{domain_env}") and name_env != domain_env:
                target_record_name_fqdn = f"{name_env}.{domain_env}"
                print(f"[INFO] Constructed FQDN: '{target_record_name_fqdn}' from NAME='{name_env}' and DOMAIN='{domain_env}'.")
            else: 
                target_record_name_fqdn = name_env
                print(f"[INFO] Using NAME '{name_env}' as target (assumed FQDN or root).")
        else: 
            target_record_name_fqdn = name_env
            print(f"[INFO] DOMAIN not set. Using NAME '{name_env}' as target (must be FQDN).")
    elif domain_env: 
        target_record_name_fqdn = domain_env
        print(f"[INFO] NAME not set. Targeting root domain based on DOMAIN env: '{target_record_name_fqdn}'.")
    
    if not record_id_env and not target_record_name_fqdn:
         print("[FATAL] Could not determine target record name. Set RECORDID, or NAME and/or DOMAIN. Exiting.")
         sys.exit(1)
    print("-" * 30)

    # Verify Cloudflare Authentication
    print("[INFO] Verifying Cloudflare authentication...")
    if not verify_auth(email, token):
        print("[FATAL] Cloudflare authentication failed. Check EMAIL and TOKEN. Exiting.")
        sys.exit(1)
    print("[SUCCESS] Cloudflare authentication successful.")
    print("-" * 30 + "\n")

    # Determine final_record_id and final_name_for_update
    final_record_id_to_update = None
    final_name_for_update = None
    effective_record_type = record_type_env

    print("[INFO] Fetching all DNS records for the zone...")
    all_zone_records = get_all_dns_records(email, token, zone_id)
    if all_zone_records is None:
        print(f"[FATAL] Failed to fetch DNS records for zone {zone_id}. Cannot proceed. Exiting.")
        sys.exit(1)

    if record_id_env:
        print(f"[INFO] Using provided RECORDID: {record_id_env} to identify target record.")
        found_record_by_id = next((r for r in all_zone_records if r.get('id') == record_id_env), None)
        if found_record_by_id:
            actual_name = found_record_by_id.get('name')
            actual_type = found_record_by_id.get('type')
            print(f"[SUCCESS] Record with ID '{record_id_env}' found: Name='{actual_name}', Type='{actual_type}'.")
            
            final_record_id_to_update = record_id_env
            final_name_for_update = actual_name 
            effective_record_type = actual_type

            if target_record_name_fqdn and target_record_name_fqdn != actual_name:
                print(f"[WARN] Env-derived name '{target_record_name_fqdn}' differs from actual name '{actual_name}' for RECORDID '{record_id_env}'. Using actual name: '{actual_name}'.")
            if record_type_env != actual_type:
                 print(f"[WARN] Provided RECORDTYPE '{record_type_env}' differs from actual type '{actual_type}' for RECORDID '{record_id_env}'. Using actual type: '{actual_type}'.")
        else:
            print(f"[FATAL] RECORDID '{record_id_env}' provided, but no such record found in zone '{zone_id}'. Exiting.")
            sys.exit(1)
    else:
        print(f"[INFO] RECORDID not provided. Finding record by Name='{target_record_name_fqdn}', Type='{record_type_env}'.")
        if not target_record_name_fqdn:
            print("[FATAL] Target record name (target_record_name_fqdn) is not set. Cannot find record. Exiting.")
            sys.exit(1)
        
        final_record_id_to_update, retrieved_name = find_record_details_by_name_and_type(
            all_zone_records, target_record_name_fqdn, record_type_env, selected_item_env
        )
        if not final_record_id_to_update:
            print(f"[FATAL] Could not automatically determine the record for Name='{target_record_name_fqdn}', Type='{record_type_env}'. Exiting.")
            sys.exit(1)
        final_name_for_update = retrieved_name
    
    if not final_record_id_to_update or not final_name_for_update:
        print("[FATAL] Could not determine final_record_id or final_name_for_update. Exiting before loop.")
        sys.exit(1)

    print("\n" + "*"*20 + " Target Record Identified " + "*"*20)
    print(f"  Record ID to Update: {final_record_id_to_update}")
    print(f"  Record Name:         {final_name_for_update}")
    print(f"  Record Type:         {effective_record_type}")
    print("*"* (40 + len(" Target Record Identified ")) + "\n")
    
    setup_end_time = time.time()
    print(f"[INFO] Setup and record identification completed in {setup_end_time - script_start_time:.2f} seconds.")

    # Get current public IP before starting loop
    print("[INFO] Fetching initial public IP address...")
    current_public_ip = get_public_ip(ip_url)
    if not current_public_ip:
        print(f"[FATAL] Failed to get initial public IP from {ip_url}. Exiting.")
        sys.exit(1)
    print(f"[SUCCESS] Initial public IP: {current_public_ip}")

    # --- Main DDNS Update Loop ---
    loop_count = 0
    print("\n" + "="*70)
    print(" Starting DDNS Update Loop...")
    print("="*70)
    while True:
        loop_count += 1
        current_loop_time = get_current_timestamp()
        print(f"\n--- DDNS Check Loop #{loop_count} ({current_loop_time}) ---")
        
        print(f"[INFO] Current known public IP: {current_public_ip}")
        print(f"[INFO] Fetching new public IP from {ip_url}...")
        new_public_ip = get_public_ip(ip_url)
        
        if not new_public_ip:
            print(f"[WARN] Failed to get new public IP in this loop cycle. Skipping update.")
        elif new_public_ip == current_public_ip:
            print(f"[INFO] Public IP address has not changed ({current_public_ip}). No update needed.")
        else:
            print(f"[!!!!] IP ADDRESS CHANGE DETECTED [!!!!]")
            print(f"  Old IP: {current_public_ip}")
            print(f"  New IP: {new_public_ip}")
            print(f"[INFO] Updating DNS record '{final_name_for_update}'...")
            
            update_timestamp = get_current_timestamp()
            update_successful = main_update_dns(
                final_name_for_update, effective_record_type, new_public_ip,
                email, token, zone_id, final_record_id_to_update,
                ttl, update_timestamp
            )
            if update_successful:
                print(f"[SUCCESS] DNS update for '{final_name_for_update}' to '{new_public_ip}' was successful.")
                current_public_ip = new_public_ip 
            else:
                print(f"[ERROR] DNS update for '{final_name_for_update}' failed. Old IP '{current_public_ip}' will be checked next cycle.")

        print(f"[INFO] Waiting for {update_interval} seconds before next check...")
        time.sleep(update_interval)
