import time
import os
import requests

current_time = time.ctime()


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


def main(domain, name, record_type, ip_url, email, token, zone_id, record_id):
    # Verify authentication
    verify_auth(email, token)


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


domain = os.getenv("DOMAIN")
name = os.getenv("NAME")
record_type = os.getenv("RECORDTYPE")
ip_url = os.getenv("IPURL")
email = os.getenv("EMAIL")
token = os.getenv("TOKEN")
zone_id = os.getenv("TOKENID")
record_id = os.getenv("RECORDID")

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
