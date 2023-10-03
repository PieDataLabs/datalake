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
from xml.etree.ElementTree import parse
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
