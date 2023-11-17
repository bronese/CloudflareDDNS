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

current_time = time.ctime()


# Var checker
def check_env(env_name):
    value = os.getenv(env_name)
    if not value:
        print(f"{env_name} is empty.")


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
def get_ip(ip_url="http://ifconfig.me"):
    response = requests.get(ip_url)
    return response.text.rstrip()


def get_headers(email, token):
    return {
        "X-Auth-Email": email,
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
    }


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
    }

    print(f"updated IP: {new_ip} at {current_time}")

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
if verify_auth(email, token) == True:
    print("Awaiting IP check...")

# IP update schedule
current_ip = get_ip()
wait_time = 60 * 30  # 30 minutes
while True:
    new_ip = get_ip()
    print("No IP Changes")
    if new_ip != current_ip:
        print(f"IP has changed from {current_ip} to {new_ip}. Updating...")
        main(domain, name, record_type, ip_url, email, token, zone_id, record_id)
        current_ip = new_ip
    time.sleep(wait_time)


# if __name__ == "__main__":
#     config = configparser.ConfigParser()
#     config.read("ddns.ini")

#     section = config["DEFAULT"]
#     domain = section["Domain"]
#     name = section["Name"]
#     record_type = section["RecordType"]
#     ip_url = section["IpUrl"]
#     email = section["Email"]
#     token = section["Token"]
#     zone_id = section["ZoneId"]
#     record_id = section["RecordId"]
