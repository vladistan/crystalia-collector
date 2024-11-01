#! /usr/bin/env python3
import sys
import base64
import zlib
import argparse
import requests
import os

KROKI_SERVER_BASE_URL = os.environ.get(
    "KROKI_SERVER_BASE_URL",
    "https://kroki.r4.v-lad.org",
)


def main() -> None:
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Generate a diagram URL or save it to a file.",
    )
    parser.add_argument(
        "-u",
        "--url",
        action="store_true",
        help="Display the URL instead of saving the file",
    )
    parser.add_argument(
        "--filetype",
        type=str,
        default="png",
        help="Specify the output file type (default: png)",
    )
    parser.add_argument(
        "--diagtype",
        type=str,
        default="mermaid",
        help="Specify the diagram type (default: mermaid)",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=KROKI_SERVER_BASE_URL,
        help="Specify the base URL for the Kroki server",
    )
    args = parser.parse_args()

    # Read diagram source from stdin
    diagram_source = sys.stdin.read()

    # Compress using zlib with maximum compression level
    compressed_data = zlib.compress(diagram_source.encode("utf-8"), 9)

    # Encode the compressed data in base64 and make it URL-safe
    encoded_data = base64.urlsafe_b64encode(compressed_data).decode("utf-8")

    # Construct the URL
    url = f"{KROKI_SERVER_BASE_URL}/{args.diagtype}/{args.filetype}/{encoded_data}"

    if args.url:
        print(f"URL: {url}")
    else:
        # Send request to Kroki server
        response = requests.get(url)
        if response.status_code == 200:
            output_filename = f"output.{args.filetype}"
            with open(output_filename, "wb") as f:
                f.write(response.content)
            print(f"Diagram saved as {output_filename}")
        else:
            print(f"Failed to retrieve diagram: {response.status_code}")


if __name__ == "__main__":
    main()
