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
- `RECORDTYPE`: The type of your record, should be either A or AAAA.
- `EMAIL`: Your email used for login on Cloudflare.
- `TOKEN`: Your API token on Cloudflare.
- `ZONEID`: Zone ID of your domain on Cloudflare.
- `RECORDID`: Record ID of your A or AAAA record on Cloudflare.
- `IPURL` (optional): A third-party service URL that returns your IP address in plain text. If left empty or not provided, it will default to "http://ifconfig.me".

An example .env file is also [included](https://github.com/bronese/CloudflareDDNS/blob/main/example.env).

## Usage

To start the app in Docker, run the following command (substitute your environment variables):

```
docker run -e DOMAIN=yourdomain -e NAME=yourname -e RECORDTYPE=A -e EMAIL=youremail -e TOKEN=yourtoken -e ZONEID=yourzoneid -e RECORDID=yourrecordid bronese/ddns-updater:lastest -v /home/
```

You can also use a .env file to configure your environment variables and run the Docker command:

```
docker run --env-file .env bronese/ddns-updater:lastest
```

The script will run indefinitely, checking your IP every 30 minutes and updating the DNS record if a change is detected.
