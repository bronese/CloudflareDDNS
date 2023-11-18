import time
import os
import requests

# Environmental Variables
domain = os.getenv("DOMAIN")
name = os.getenv("NAME")
record_type = os.getenv("RECORDTYPE")
ip_url = os.getenv("IPURL")
email = os.getenv("EMAIL")
token = os.getenv("TOKEN")
zone_id = os.getenv("ZONEID")
record_id = os.getenv("RECORDID")
update_interval = os.getenv("UPDATEINTERVAL")
ttl = os.getenv("TTL")

current_time=(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))

# Var checker
def check_env(env_name):
    value = os.getenv(env_name)
    if not value:
        print(f"{env_name} is empty.")


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
        print(f"Authentication successful for user {email}.")
    else:
        print(f"Failed to authenticate user {email}. Response: {response.json()}")

# Get IP
def get_ip(ip_url=None):
    if ip_url is None:
        ip_url = "http://ifconfig.me"
    response = requests.get(ip_url)
    return response.text.rstrip()

# Main function
def main(domain, name, record_type, ip_url, email, token, zone_id, record_id):
    # Get IP
    new_ip = get_ip(ip_url)

    # Get headers
    headers = get_headers(email, token)

    # Define the data
    data = {
        "content": new_ip,
        "name": name,
        "proxied": False,
        "type": record_type,
        "comment": "IP updated at " + current_time,
        "ttl": ttl
    }
    print(data)
    
    # Send the PUT request
    response = requests.put(
        f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}",
        headers=headers,
        json=data,
    )

    # Print the response
    print(response.json())


# Environment Variables check
check_env("DOMAIN")
check_env("NAME")
check_env("RECORDTYPE")
check_env("EMAIL")
check_env("TOKEN")
check_env("ZONEID")
check_env("RECORDID")

# Verify authentication on boot
verify_auth(email, token)

# IP update schedule
current_ip=get_ip()

while True:
    new_ip = get_ip(ip_url)
    main(domain, name, record_type, ip_url, email, token, zone_id, record_id)
    print(f"Updated IP from {current_ip} to {new_ip} at {current_time}.")
    current_ip = new_ip
    wait_time = int(update_interval if update_interval is not None else 300)
    time.sleep(wait_time)