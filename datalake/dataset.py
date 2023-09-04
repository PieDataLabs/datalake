import os
from typing import List, Union
from PIL import Image
import numpy as np
from imantics import Annotation

from .data_request import DataRequest
from .annotations import AnnotationSearch, ImageWithAnnotations
from .settings import FEATURE_DIMENSION, FREEMIUM_SEARCH_LIMIT
from .utils import to_base64


class Dataset(object):
    def __init__(self, searcher,
                 dataset_id: str):
        super(Dataset, self).__init__()
        self.searcher = searcher
        self.dataset_id = dataset_id

    def add(self,
            data_request: DataRequest,
            ids: List[int]):
        self.searcher.dataset_add(self.dataset_id,
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

        if search_limit > FREEMIUM_SEARCH_LIMIT:
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

        if search_limit > FREEMIUM_SEARCH_LIMIT:
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
