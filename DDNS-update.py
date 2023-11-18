import time
import os
import requests
import sys

# Environmental Variables
domain = os.getenv("DOMAIN")
name = os.getenv("NAME")
record_type = os.getenv("RECORDTYPE") or "A"
ip_url = os.getenv("IPURL") or "http://ifconfig.me"
email = os.getenv("EMAIL")
token = os.getenv("TOKEN")
zone_id = os.getenv("ZONEID")
record_id = os.getenv("RECORDID")
update_interval = os.getenv("UPDATEINTERVAL") or 300 # 5 minutes
ttl = os.getenv("TTL") or 1 # 1 second
selecteditem = int(os.getenv("SELECTEDITEM")) if os.getenv("SELECTEDITEM") else None

current_time=(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))

# Var checker
def check_env(env_name):
    value = (env_name)
    if not value:
        print(f"{env_name} is empty.")
        return False
    return True

# Get DNS records
def get_dns_record(email, token, zone_id):
    headers = get_headers(email, token)
    response = requests.get(
        f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records",
        headers=headers
    )
    dns_records = response.json()["result"]
    if not dns_records:
        print("No DNS records found.")
    else:
        return dns_records

# Build headers
def get_headers(email, token):
    return {
        "X-Auth-Email": email,
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
    }


# Cloudflare auth
def verify_auth(email, token):
    headers = get_headers(email, token)
    response = requests.get(
        "https://api.cloudflare.com/client/v4/user", headers=headers
    )

    if response.status_code == 200:
        print(f"Authentication successful")
    else:
        print(f"Failed to authenticate user. Response: {response.json()}")

# Get IP
def get_ip(ip_url):
    response = requests.get(ip_url)
    return response.text.rstrip()

# Get generated record ID
def get_generated_record_id(dns_record, selecteditem):
    filtered_payload = []
    counter = 0
    while counter < len(dns_record):
        if record_type is None or dns_record[counter]['type'] == record_type:
            filtered_payload.append(dns_record[counter])
        counter += 1
    if len(filtered_payload) == 1:
        dns_record_id = filtered_payload[0]
        return dns_record_id['id'], dns_record_id['name']
    else:
        dns_record_id = filtered_payload[selecteditem]
        return dns_record_id['id'], dns_record_id['name']
# Main function
def main(domain, final_name, record_type, ip_url, email, token, zone_id, final_record_id):
    # Get IP
    new_ip = get_ip(ip_url)

    # Get headers
    headers = get_headers(email, token)

    # Define the data
    data = {
        "content": new_ip,
        "name": final_name,
        "proxied": False,
        "type": record_type,
        "comment": "IP updated at " + current_time,
        "ttl": ttl
    }
    print(data)
    
    # Send the PUT request
    response = requests.put(
        f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{final_record_id}",
        headers=headers,
        json=data,
    )

    # Print the response
    response_data = response.json()

    for key, value in response_data.items():
        if isinstance(value, dict):
            print(f"{key}:")
            for inner_key, inner_value in value.items():
                print(f"  {inner_key}: {inner_value}")
        else:
            print(f"{key}: {value}")

start_time = time.time()
# Environment Variables check
check_env("DOMAIN")
check_env("NAME")
check_env("RECORDTYPE")
check_env("EMAIL")
check_env("TOKEN")
check_env("ZONEID")
check_env("RECORDID")

if not check_env(record_type):
    print(f"Record Type is empty, 'A' record will be used by default.")

if not check_env("TOKEN") or not check_env("ZONEID"):
    print(f"Either Token: [{token}] or Zone ID: [{zone_id}] is empty, or both.")
    sys.exit()


# Verify authentication on boot
verify_auth(email, token)

# Set current IP
current_ip=get_ip(ip_url)

#DNS record ID checker
dns_record = get_dns_record(email, token, zone_id)
if selecteditem is not None or (record_id is None and name is None):
    final_record_id, final_name = get_generated_record_id(dns_record, selecteditem==0)
    print("No RecordID, Record Name, or Item selection provided, using first record found.")

elif selecteditem is not None and record_id is None and name is None:
    final_record_id, final_name = get_generated_record_id(dns_record, selecteditem)

elif selecteditem is None:
    final_record_id = record_id
    final_name = name

end_time = time.time()
runtime = end_time - start_time
print(f"Boot runtime: {runtime} seconds")

# Main loop
while current_ip != None:
    new_ip = get_ip(ip_url)
    main(domain, final_name, record_type, ip_url, email, token, zone_id, final_record_id)
    print(f"Updated IP from {current_ip} to {new_ip} at {current_time}.")
    current_ip = new_ip
    wait_time = int(update_interval)    
    time.sleep(wait_time)
