import argparse
import json
from pathlib import Path
from time import time
from datalake import Searcher
from datalake.annotations import Annotation, Tag, Polygon, Box
from PIL import Image
from datalake.credentials import load_credentials, save_credentials


def format_path(output_path, query, annotations):
    output_path = output_path.replace("$query", query)
    for i in range(len(annotations)):
        output_path = output_path.replace(f"$ann[{i}]", annotations[i].name)
    return output_path


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
    search_parser.add_argument("--tag",
                               type=str,
                               action="append",
                               dest="tags")
    search_parser.add_argument("--polygon",
                               type=str,
                               action="append",
                               dest="polygons")
    search_parser.add_argument("--box",
                               type=str,
                               action="append",
                               dest="boxes")
    search_parser.add_argument("--output_format",
                               default="$query.json")

    stats_parser = subparsers.add_parser("stats")
    stats_parser.add_argument("--limits", action="store_true")

    host_parser = subparsers.add_parser("host")
    host_parser.add_argument("image_path", type=Path)

    license_parser = subparsers.add_parser("license")

    args = parser.parse_args()
    return args


def run_search(query, images,
               annotations,
               tags,
               polygons,
               boxes,
               output_format):
    credentials = load_credentials()
    if credentials is None:
        print("ERROR: credentials are invalid.\nUse `datalake auth` command first.\n")
        exit()

    if images is None:
        images = []
    if annotations is None:
        annotations = []
    if tags is None:
        tags = []
    if polygons is None:
        polygons = []
    if boxes is None:
        boxes = []

    images = [Image.open(image_path).convert("RGB")
              for image_path in images]
    annotations = [Annotation.from_string(ann) for ann in annotations]
    annotations.extend([Tag.from_string(tag) for tag in tags])
    annotations.extend([Polygon.from_string(polygon)
                        for polygon in polygons])
    annotations.extend([Box.from_string(box)
                        for box in boxes])

    searcher = Searcher(**credentials)

    print("Query:")
    print(query)
    print("Annotations:")
    print(annotations)
    print("Number of samples: ")
    print(len(images))

    search_limit = 10
    data_request = searcher.search(query,
                                   images=images,
                                   annotations=annotations,
                                   search_limit=search_limit)
    print("Data request: ")
    print(data_request)
    t_start = time()
    data = data_request.wait(search_limit)
    print(f"Elapsed time: {time() - t_start}")
    output_path = format_path(output_format,
                              query,
                              annotations)
    print(f"Writing results to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(data, f)


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
        exit()
    for i, request_id in enumerate(searcher.recent_searches()):
        request_params = searcher.view_search(request_id)
        print(f"Search#{i + 1}")
        print("Query: ", request_params.get("query", ""))
        print("Annotations: ", request_params.get("annotations", []))
        print("NSampleImages: ", len(request_params.get("images")))
        print("--------------\n")


def run_host(image_path: Path):
    raise NotImplementedError()


def run_license():
    pass


def main(command, **kwargs):
    if command == "search":
        run_search(**kwargs)
    elif command == "auth":
        run_auth(**kwargs)
    elif command == "stats":
        run_stats(**kwargs)
    elif command == "host":
        run_host(**kwargs)
    elif command == "license":
        run_license()
    else:
        raise NotImplementedError()


if __name__ == "__main__":
    main(**vars(parse_args()))
