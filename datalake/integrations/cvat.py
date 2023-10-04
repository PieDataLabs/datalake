import os
import sys
import zipfile
import os
import numpy as np
from pathlib import Path
from PIL import Image
import zipfile
import io
from tqdm import tqdm
from xml.etree.ElementTree import parse, ElementTree, SubElement, Element
from imantics import Annotation, Category, BBox, Polygons


class CVATForImages(object):
    def __init__(self, path):
        super(CVATForImages, self).__init__()
        self.path = path
        with zipfile.ZipFile(path) as zf:
            annotations_zip_info = list(filter(lambda x: os.path.basename(x.filename) == "annotations.xml",
                                               zf.filelist))[0]
            xml_content = zf.read(annotations_zip_info.filename)
            self.keys = [finfo.filename
                         for finfo in zf.filelist]
        tree = parse(io.StringIO(xml_content.decode('utf-8')))
        root = tree.getroot()
        self.annotations = {}
        for child in tqdm(root, total=len(root)):
            if child.tag == "image":
                key = os.path.basename(child.attrib["name"])
                self.annotations[key] = {
                    "name": child.attrib["name"],
                    "width": int(child.attrib["width"]),
                    "height": int(child.attrib["height"]),
                    "annotations": []
                }
                for ann_child in child:
                    if ann_child.tag == "box":
                        ann = Annotation(bbox=BBox([
                            float(ann_child.attrib['xtl']),
                            float(ann_child.attrib['ytl']),
                            float(ann_child.attrib['xbr']),
                            float(ann_child.attrib['ybr'])]),
                            category=Category(ann_child.attrib['label']),
                            metadata={"pietype": "Box"},
                            image=None,
                            width=int(child.attrib['width']),
                            height=int(child.attrib['height']))

                    elif ann_child.tag == "polygon" or ann_child.tag == "polyline":
                        points = [[float(c) for c in xy.split(',')]
                                  for xy in ann_child.attrib['points'].split(';')]
                        points = np.array(points)
                        ann = Annotation(polygons=Polygons([points]),
                                         category=Category(ann_child.attrib['label']),
                                         metadata={"pietype": "Polygon"},
                                         image=None,
                                         width=int(child.attrib['width']),
                                         height=int(child.attrib['height']))
                    else:
                        print("Missing loader for", ann_child)
                        continue
                    self.annotations[key]["annotations"].append(ann)
        self.keys = list(filter(lambda key: os.path.basename(key) in self.annotations,
                                self.keys))

    def __getitem__(self, index):
        key = self.keys[index]
        annotations = self.annotations[os.path.basename(key)]["annotations"]
        with zipfile.ZipFile(self.path) as zf:
            im = Image.open(io.BytesIO(zf.read(key))).copy()
        return im, annotations

    def __len__(self):
        return len(self.keys)


class CVATForImagesWriter(object):
    def __init__(self, path):
        self.path = path
        self.n_images = 0
        self.root = Element("xml")

    def write(self, image, annotations=None, key=None):
        if key is None:
            key = str(self.n_images)
        if annotations is None:
            annotations = []
        buf = io.BytesIO()
        image.save(buf, "JPEG")
        buf.seek(0)
        image_el = SubElement(self.root,
                         "image",
                        {"name": f"{self.n_images}.jpg",
                               "width": str(image.size[0]),
                               "height": str(image.size[1])})
        for ann in annotations:
            if ann.metadata.get("pietype") == "Box":
                ann_el = SubElement(image_el,
                                    "box",
                                    {
                                        "xtl": str(ann.bbox.bbox()[0]),
                                        "ytl": str(ann.bbox.bbox()[1]),
                                        "xbr": str(ann.bbox.bbox()[2]),
                                        "ybr": str(ann.bbox.bbox()[3]),
                                        "label": ann.category.name,
                                    })
            else:
                print(ann.metadata)
                raise

        with zipfile.ZipFile(self.path, 'a') as zf:
            zf.writestr(f"{self.n_images}.jpg",
                        buf.getvalue())
            xml_content_file = io.BytesIO()
            ElementTree(self.root).write(xml_content_file)
            xml_content_file.seek(0)
            zf.writestr("annotations.xml",
                        xml_content_file.getvalue())

        self.n_images += 1
