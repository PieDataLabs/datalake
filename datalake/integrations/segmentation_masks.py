from pathlib import Path
import numpy as np
import cv2
from parse import parse
from PIL import Image
from tqdm import tqdm
from imantics import Annotation, Category, BBox, Polygons, Mask


class SegmentationMasks(object):
    def __init__(self, path: Path):
        self.path = Path(path)
        self.labelmap_path = self.path / "labelmap.txt"
        self.imageset_path = self.path / "ImageSets" / "Segmentation" / "default.txt"
        self.images_path = self.path / "JPEGImages"
        self.binary_masks_path = self.path / "SegmentationClass"
        self.instance_masks_path = self.path / "SegmentationObject"

        self.labelmap = self.read_labelmap(self.labelmap_path)
        self.imageset = self.read_imageset(self.imageset_path)

        self.key2image_path = self.read_key2path(self.imageset, self.images_path)
        self.key2binary_mask_path = self.read_key2path(self.imageset, self.binary_masks_path)
        self.key2instance_mask_path = self.read_key2path(self.imageset, self.instance_masks_path)

        self.imageset = list(self.key2image_path.keys())

    @staticmethod
    def read_labelmap(path):
        path = Path(path)
        labelmap = []
        with path.open('r') as f:
            for line in f.readlines():
                if line.startswith('#'):
                    continue
                line = line[:-1]
                res = parse("{name}:{color}::", line)
                name = res['name']
                color = parse("{},{},{}", res['color']).fixed
                color = (int(color[0]), int(color[1]), int(color[2]))
                labelmap.append((name, color))

        return labelmap

    @staticmethod
    def read_imageset(path):
        path = Path(path)
        with path.open('r') as f:
            return list(map(lambda x: x[:-1], f.readlines()))

    def read_key2path(self, keys, dir_path):
        data = {}
        for path in dir_path.iterdir():
            if path.stem in keys:
                data[path.stem] = path

        print("Missing keys: ")
        print(list(set(keys).difference(set(data.keys()))))
        print("Extra keys: ")
        print(list(set(data.keys()).difference(set(keys))))

        return data

    @staticmethod
    def read_image(path):
        return Image.open(path).convert("RGB")

    @staticmethod
    def read_annotations(labelmap,
                         mask_path,
                         instance_path):
        mask = np.array(Image.open(mask_path).convert("RGB"))
        anns = []
        for i, (name, color) in enumerate(labelmap):
            color_array = np.array([[color]], dtype=np.uint8)
            m = Mask(np.all(mask == color_array, axis=-1))
            ann = Annotation(mask=m,
                             category=Category(name),
                             metadata={"pietype": "Polygon"})
            anns.append(ann)
        return anns

    @staticmethod
    def read_binary_mask(labelmap, path):
        mask = np.array(Image.open(path).convert("RGB"))
        mask_bin = np.zeros(mask.shape[:2], dtype=np.int32)
        for i, (name, color) in enumerate(labelmap):
            mask_bin += i * np.int32(np.all(mask == np.array([[color]], dtype=np.uint8), axis=-1))
        return mask_bin

    @staticmethod
    def read_instance_mask(path):
        mask = np.array(Image.open(path).convert('RGB'))
        mask_bin = np.zeros(mask.shape[:2], dtype=np.int32)
        colors = list(map(tuple, np.unique(mask.reshape((-1, 3)), axis=0).tolist()))
        colors.remove((0, 0, 0))
        curnum = 0
        for color in tqdm(colors):
            num, labels = cv2.connectedComponents(255 * np.uint8(np.all(mask == np.array([[color]], dtype=np.uint8), axis=-1)),
                                                  connectivity=8)
            mask_bin += (labels > 0) * (labels + curnum)
            curnum += num

        return mask_bin

    def __getitem__(self, index):
        key = self.imageset[index]
        image = self.read_image(self.key2image_path[key])
        anns = self.read_annotations(self.labelmap,
                                     self.key2binary_mask_path[key],
                                     self.key2instance_mask_path[key])
        return image, anns

    def __len__(self):
        return len(self.imageset)
