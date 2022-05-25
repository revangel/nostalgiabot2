import argparse
import csv
import os
import pathlib

import requests

NB2_PORT = os.environ["NB2_PORT"] or "8000"


def get_url(url):
    return f"{'http' if parsed_args.use_http else 'https'}://127.0.0.1:{NB2_PORT}{url}"


def post(url, data):
    response = requests.post(get_url(url), data)
    if response.status_code > 400 and response.status_code != 409:
        raise Exception(response.json())
    return response


if __name__ == "__main__":
    # parser
    parser = argparse.ArgumentParser(description="Beep borp I migrate data for the cutest bot ever")
    parser.add_argument(
        "source_file",
        type=open,
        help="A csv where each line denotes a user's slack_id, ghost_id, display_name, first_name and file(s) associated with them.",  # noqa: E501
    )
    parser.add_argument(
        "quotes_folder", help="The source folder of where the quote files are", type=pathlib.Path
    )
    parser.add_argument("--use-http", help="Use http instead of https", action="store_true")

    parsed_args = parser.parse_args()
    source_file = parsed_args.source_file

    csvreader = csv.DictReader(source_file, delimiter=",")
    for row in csvreader:
        quote_filename = row.pop("file")
        post("/people", row)

        f = parsed_args.quotes_folder.joinpath(quote_filename).open()
        for quote in f:
            post(
                "/quotes",
                {"user_id": row["slack_user_id"] or row["ghost_user_id"], "content": quote[:-1]},
            )  # get rid of the newline
        f.close()

    source_file.close()
