import argparse
from pathlib import Path
from datalake import Searcher


def parse_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

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
    args = parser.parse_args()
    return args


def run_search(query, images, annotations):
    searcher = Searcher("###")
    searcher.search(query,
                    images=images,
                    annotations=annotations)


def main(command, **kwargs):
    if command == "search":
        run_search(**kwargs)
    else:
        raise NotImplementedError()


if __name__ == "__main__":
    main(**vars(parse_args()))
