import os
from typing import List, Union, Callable, Dict, Any
import math
from PIL import Image
from tqdm import tqdm
import numpy as np
from imantics import Annotation

from .data_request import DataRequest
from .annotations import AnnotationSearch, ImageWithAnnotations
from .settings import FEATURE_DIMENSION, FREEMIUM_SEARCH_LIMIT, PAGE_SIZE
from .utils import to_base64


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

    def export(self, format=None):
        raise NotImplementedError()

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
