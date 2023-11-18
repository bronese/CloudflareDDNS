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
- `EMAIL`: Your email used for login on Cloudflare.
- `TOKEN`: Your API token on Cloudflare.
- `ZONEID`: Zone ID of your domain on Cloudflare.
- `RECORDID`: Record ID of your A or AAAA record on Cloudflare.
- `IPURL` (optional): A third-party service URL that returns your IP address in plain text. If left empty or not provided, it will default to "http://ifconfig.me".
- `UPDATEINTERVAL` (optional): Interval in seconds specifying how frequently the IP update should occur. If not provided, it defaults to 300 seconds (5 minutes).
- `TTL` (optional): Time-to-live value for the updated DNS record. If not provided, it defaults to the Cloudflare zone's default TTL value.

## Usage

To start the app in Docker, run the following command (substitute your environment variables):

```
docker run -e DOMAIN=<your_domain> -e NAME=<your_name> -e RECORDTYPE=<record_type> -e IPURL=<ip_url> -e EMAIL=<your_email> -e TOKEN=<your_token> -e ZONEID=<your_zone_id> -e RECORDID=<your_record_id> -e UPDATEINTERVAL=<update_interval> -e TTL=<ttl> bronese/ddns-updater:latest
```

You can also use a .env file to configure your environment variables and run the Docker command:

```
docker run --env-file .env bronese/ddns-updater:lastest
```

The script will run indefinitely, checking your IP every 30 minutes and updating the DNS record if a change is detected.
