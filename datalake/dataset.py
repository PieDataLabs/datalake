import os
import subprocess
from multiprocessing import cpu_count
from typing import List, Union, Callable, Dict, Any
import math
import urllib.parse
from PIL import Image
from pathlib import Path
from tqdm import tqdm
from parse import parse
import numpy as np
from imantics import Annotation

from .data_request import DataRequest
from .annotations import AnnotationSearch, ImageWithAnnotations
from .settings import FEATURE_DIMENSION, FREEMIUM_SEARCH_LIMIT, PAGE_SIZE
from .utils import to_base64
from .integrations.cvat import CVATForImages


class Dataset(object):
    def __init__(self, searcher,
                 dataset_id: str):
        super(Dataset, self).__init__()
        self.searcher = searcher
        self.dataset_id = dataset_id

    @staticmethod
    def new(searcher,
            name=None) -> 'Dataset':
        dataset_id = searcher.dataset_new(name=name)["dataset_id"]
        return Dataset(searcher,
                       dataset_id=dataset_id)

    @staticmethod
    def from_cvat(searcher, cvat_url, credentials, name=None):
        ds = Dataset.new(searcher, name=name)
        try:
            ds.add_from_cvat(cvat_url, credentials=credentials)
        except:
            ds.drop()
            raise
        return ds

    def add_from_cvat(self, cvat_url,
                      credentials):
        # TODO: add annotations from cvat
        from cvat_sdk import make_client

        if cvat_url.endswith("/"):
            cvat_url = cvat_url[:-1]

        parsed = parse("{host}/tasks/{task_id}/jobs/{job_id}",
                       cvat_url)
        if parsed is None:
            parsed = parse("{host}/tasks/{task_id}",
                           cvat_url)
        if parsed is None:
            raise RuntimeError("cvat_url must be in format: host/tasks/$task_id or host/tasks/$task_id/jobs/$job_id")

        cvat_url = parsed.named.get("host")
        task_id = parsed.named.get("task_id")
        job_id = parsed.named.get("job_id")

        try:
            client = make_client(cvat_url,
                                 credentials=credentials)
        except:
            raise RuntimeError("Bad credentials")

        if job_id is not None:
            cvat_container = client.jobs.retrieve(int(job_id))
        elif task_id is not None:
            cvat_container = client.tasks.retrieve(int(task_id))
        else:
            raise RuntimeError("Can't retrieve data by url")

        i = 0
        pbar = tqdm()
        while True:
            try:
                frame = Image.open(cvat_container.get_frame(i, quality="original"))
            except:
                break
            self.add_image(frame)
            i += 1
            pbar.update(1)
        pbar.close()

    def drop(self):
        self.searcher.dataset_drop(self.dataset_id)

    def add(self,
            data_request: DataRequest,
            ids: List[int] = None,
            exclude_ids: List[int] = None):
        if ids is None:
            ids = list(range(len(data_request.retrieve())))
        if exclude_ids is None:
            exclude_ids = []
        ids = list(set(ids) - set(exclude_ids))
        self.searcher.dataset_add(self.dataset_id,
                                  data_request.request_id,
                                  data_ids=ids)
        return self

    def remove(self,
               data_request: DataRequest,
               ids: List[int] = None,
               exclude_ids: List[int] = None):
        if ids is None:
            ids = list(range(len(data_request.retrieve())))
        if exclude_ids is None:
            exclude_ids = []
        ids = list(set(ids) - set(exclude_ids))
        self.searcher.dataset_remove(self.dataset_id,
                                     data_request.request_id,
                                     data_ids=ids)
        return self

    def count(self):
        return self.searcher.dataset_info(self.dataset_id).get("images_count", 0)

    def count_annotations(self):
        return self.searcher.dataset_info(self.dataset_id).get("annotations_count", 0)

    def list(self) -> List['Dataset']:
        return self.searcher.dataset_list()

    def __repr__(self):
        info = self.searcher.dataset_info(self.dataset_id)
        return f"Dataset#{info['keyname']}(images={info['images_count']}, annotations={info['annotations_count']}, public={info['public']}, indexed={info['n_images_has_index']})"

    @property
    def keyname(self):
        return self.searcher.dataset_info(self.dataset_id)["keyname"]

    def add_image(self,
                  image_or_image_url: Union[str, Image.Image],
                  annotations=None):

        if annotations is None:
            annotations = []
        annotations = [ImageWithAnnotations.annotation_to_dict(ann)
                       if isinstance(ann, Annotation) else ann
                       for ann in annotations]

        response = self.searcher.pierequest("/add_image_to_dataset",
                                            dataset_id=self.dataset_id,
                                            **(dict(image=to_base64(image_or_image_url)) if isinstance(image_or_image_url, Image.Image) else dict(image_url=image_or_image_url)),
                                            annotations=annotations)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))

    def remove_image(self, image_url):
        response = self.searcher.pierequest("/remove_image_from_dataset",
                                            dataset_id=self.dataset_id,
                                            image_url=image_url)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))

    def clear(self):
        nPages = math.ceil(self.count() / 10)
        for page in tqdm(range(nPages)):
            page = nPages - page - 1
            data = self.retrieve(page)
            for obj in data:
                self.remove_image(obj['image_url'])

    def retrieve(self, page=0):
        response = self.searcher.pierequest("/retrieve_from_dataset",
                                            dataset_id=self.dataset_id,
                                            page=page)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))
        return response.get("data", [])

    def export(self, output_path: Path,
               format='csv'):
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        if format == 'csv':
            csv_path = output_path / f"{self.keyname}.csv"
            with csv_path.open("w") as f:
                f.write('\n'.join([obj['image_url']
                                   for obj in self.iter(progress=True)]))
            return csv_path
        elif format == "images":
            csv_path = self.export(output_path, format='csv')
            os.system(f"cd {output_path} && cat {csv_path.name} | xargs -P{cpu_count()} -IIMAGE_URL wget 'IMAGE_URL'")
            os.system(f"rm {csv_path}")
            return output_path
        else:
            raise NotImplementedError()

    def import_from(self, path: Path, format="cvat_for_images"):
        if format == "cvat_for_images":
            reader = CVATForImages(path)
            for i in tqdm(range(len(reader))):
                image, annotations = reader[i]
                if max(image.size) > 2048:
                    print(f"Image {i} larger than 2048")
                    continue
                self.add_image(image,
                               annotations=annotations)
        else:
            raise NotImplementedError("This format does not supported")

    def search(self, query,
               images: List[Image.Image] = None,
               annotations: List[AnnotationSearch] = None,
               search_limit=FREEMIUM_SEARCH_LIMIT) -> DataRequest:
        if images is None:
            images = []
        if annotations is None:
            annotations = []

        if self.dataset_id is None and search_limit > FREEMIUM_SEARCH_LIMIT:
            raise NotImplementedError(f"Now free search limit is {FREEMIUM_SEARCH_LIMIT} photos")

        response = self.searcher.pierequest("/search",
                                            query=query,
                                            images=[to_base64(im)
                                                    for im in images
                                                    if isinstance(im, Image.Image)],
                                            image_urls=[im
                                                        for im in images
                                                        if isinstance(im, str)],
                                            annotations=[ann.to_dict()
                                                         for ann in annotations],
                                            knum=search_limit,
                                            dataset_id=self.dataset_id)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))

        return DataRequest(self.searcher, response.get("request_id"))

    def deepsearch(self, embedding: np.ndarray,
                   annotations: List[AnnotationSearch] = None,
                   search_limit=FREEMIUM_SEARCH_LIMIT):

        if annotations is None:
            annotations = []

        if embedding.shape != (FEATURE_DIMENSION, ):
            raise RuntimeError("Bad embedding shape")

        if self.dataset_id is None and search_limit > FREEMIUM_SEARCH_LIMIT:
            raise NotImplementedError(f"Now free search limit is {FREEMIUM_SEARCH_LIMIT} photos")

        response = self.searcher.pierequest("/deepsearch",
                                            embedding=embedding.tolist(),
                                            annotations=[ann.to_dict()
                                                         for ann in annotations],
                                            knum=search_limit,
                                            dataset_id=self.dataset_id)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("message"))

        return DataRequest(self.searcher, response.get("request_id"))

    def iter(self, progress=True):
        n_images = self.count()
        n_pages = math.ceil(n_images / PAGE_SIZE)

        if progress:
            pbar = iter(tqdm(range(n_images)))
        else:
            pbar = iter(range(n_images))

        for page in range(n_pages):
            for obj in self.retrieve(page):
                next(pbar)
                yield obj

    def __iter__(self):
        return self.iter()

    def __len__(self):
        return self.count()

    def __getitem__(self, index):
        if isinstance(index, int):
            page = index // PAGE_SIZE
            page_index = index - PAGE_SIZE * page
            return self.retrieve(page)[page_index]
        if isinstance(index, list):
            pages = set(map(lambda idx: idx // PAGE_SIZE, index))
            pages_data = {page: self.retrieve(page)
                          for page in pages}
            return [pages_data[idx // PAGE_SIZE][idx - PAGE_SIZE * (idx // PAGE_SIZE)]
                    for idx in index]
        if isinstance(index, slice):
            return self[list(range(index.start, index.stop, index.step))]
        raise NotImplementedError("index must be only slice, list or int")

    def filter(self, fn: Callable[[Dict[str, Any]], bool],
               suffix: str = "filtered",
               progress=True):
        info = self.searcher.dataset_info(self.dataset_id)
        name = info["name"] + "/" + suffix
        new_ds = Dataset.new(self.searcher, name)
        for obj in self.iter(progress=progress):
            if fn(obj):
                new_ds.add_image(obj['image_url'],
                                 annotations=obj["annotations"])
        return new_ds

    def map(self, fn: Callable[[Dict[str, Any]], Dict[str, Any]],
            suffix: str = "mapped",
            progress=True):
        info = self.searcher.dataset_info(self.dataset_id)
        name = info["name"] + "/" + suffix
        new_ds = Dataset.new(self.searcher, name)
        for obj in self.iter(progress=progress):
            new_obj = fn(obj)
            new_ds.add_image(new_obj['image_url'], new_obj["annotations"])
        return new_ds

    def nearest_n(self, image_or_image_url: Union[str, Image.Image],
                  n=5):
        request = self.search("",
                              images=[image_or_image_url],
                              annotations=[],
                              search_limit=n).wait(n=n)
        return [{
            "image_url": request[i]["image_url"],
            "score": request[i]["score"]
        } for i in range(len(request))]

    def nearest(self, image_or_image_url: Union[str, Image.Image]):
        return self.nearest_n(image_or_image_url, 1)[0]

    def duplicates(self, th=0.9,
                   progress=True,
                   batch_size=10):
        if batch_size <= 1:
            raise RuntimeError("If batch_size == 1, nearest=self")
        groups = {}

        def connect(i, j):
            if i == j:
                return
            group_i = groups.get(i, frozenset({i}))
            group_j = groups.get(j, frozenset({j}))
            group = frozenset.union(group_i, group_j)
            for k in group:
                groups[k] = group

        for data in self.iter(progress=progress):
            image_url = data["image_url"]
            nearest_list = self.nearest_n(image_url,
                                          n=batch_size)
            for nearest in nearest_list:
                if nearest["score"] > th:
                    connect(image_url, nearest["image_url"])

        return set(groups.values())

    def make_public(self):
        self.searcher.dataset_make_public(self.dataset_id)
        action = "/invite?dataset_id=%s" % self.dataset_id
        return f"https://console.piedata.ai/proxy?project_id=64b61f572e9765980a0640d3&action={urllib.parse.quote(action)}"

    def make_private(self):
        self.searcher.dataset_make_private(self.dataset_id)
