import requests
import configparser
import time

current_time = time.ctime()


def get_ip(ip_url):
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


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("ddns.ini")

    section = config["DEFAULT"]
    domain = section["Domain"]
    name = section["Name"]
    record_type = section["RecordType"]
    ip_url = section["IpUrl"]
    email = section["Email"]
    token = section["Token"]
    zone_id = section["ZoneId"]
    record_id = section["RecordId"]
