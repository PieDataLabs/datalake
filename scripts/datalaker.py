import argparse
from pathlib import Path
from datalake import Searcher
from datalake.credentials import load_credentials, save_credentials


def parse_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    auth_parser = subparsers.add_parser("auth")

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")
    search_parser.add_argument("--image",
                               type=Path,
                               action="append",
                               dest="images")
    search_parser.add_argument("--annotation",
                               type=str,
                               action="append",
                               dest="annotations")

    stats_parser = subparsers.add_parser("stats")
    stats_parser.add_argument("--limits", action="store_true")

    args = parser.parse_args()
    return args


def run_search(query, images, annotations):
    credentials = load_credentials()
    if credentials is None:
        print("ERROR: credentials are invalid.\nUse `datalake auth` command first.\n")
        exit()
    searcher = Searcher(**credentials)
    searcher.search(query,
                    images=images,
                    annotations=annotations)


def run_auth():
    print("""
Visit the page:
https://console.piedata.ai/proxy?project_id=64b61f572e9765980a0640d3&action=/login
Click on your logo (the most right icon at navbar)
Paste here email and api key:
""")
    email = input("email: ")
    api_key = input("API_KEY: ")
    save_credentials(email, api_key)
    print("""
Credentials successfully saved!
""")


def run_stats(limits: bool = False):
    credentials = load_credentials()
    if credentials is None:
        print("ERROR: credentials are invalid.\nUse `datalake auth` command first.\n")
        exit()
    searcher = Searcher(**credentials)
    if limits:
        print(searcher.limits())


def main(command, **kwargs):
    if command == "search":
        run_search(**kwargs)
    elif command == "auth":
        run_auth(**kwargs)
    elif command == "stats":
        run_stats(**kwargs)
    else:
        raise NotImplementedError()


if __name__ == "__main__":
    main(**vars(parse_args()))
