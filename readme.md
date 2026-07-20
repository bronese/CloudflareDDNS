# Cloudflare DDNS

This script is used to automatically update your dns record on Cloudflare when your ip changes. It uses the Cloudflare API to update your dns record.

## Installation

You can pull the latest image from Docker Hub using this command:

```
docker pull bronese/ddns-updater:latest
```

## Environment Variables:

You must set the following environment variables when you create your Docker container:

- `DOMAIN`: Your domain name in Cloudflare.
- `NAME`: The name of your A or AAAA record on Cloudflare.
- `RECORDTYPE`: The type of your record, either A or AAAA.
- `TOKEN`: Your Cloudflare API token with DNS read and edit permissions.
- `ZONEID`: Zone ID of your domain on Cloudflare.
- `RECORDID`: (optional): Record ID of your A or AAAA record. If omitted, the script finds it from `NAME` and `RECORDTYPE`.
- `IPURL`: (optional): A third-party service URL that returns your IP address in plain text. If omitted, it defaults to "https://ifconfig.me".
- `UPDATEINTERVAL`: (optional): Interval in seconds specifying how frequently the IP update should occur. If not provided, it defaults to 300 seconds (5 minutes).
- `TTL`: (optional): Time-to-live value for the updated DNS record. If not provided, it defaults to the Cloudflare zone's default TTL value.

## Usage

To start the app in Docker, run the following command (substitute your environment variables):

```
docker run -e DOMAIN=<your_domain> -e NAME=<your_name> -e RECORDTYPE=<record_type> -e IPURL=<ip_url> -e TOKEN=<your_token> -e ZONEID=<your_zone_id> -e RECORDID=<your_record_id> -e UPDATEINTERVAL=<update_interval> -e TTL=<ttl> bronese/ddns-updater:latest
```

You can also use a .env file to configure your environment variables and run the Docker command:

```
docker run --env-file .env bronese/ddns-updater:latest
```

The script checks every five minutes by default and immediately updates Cloudflare whenever its DNS value differs from your public IP.
