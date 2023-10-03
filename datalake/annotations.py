import re
from imantics import Annotation, BBox, Mask, Polygons, Category
from parse import parse
import numpy as np
from .utils import from_url


class AnnotationSearch(object):
    def __init__(self, name, color):
        super(AnnotationSearch, self).__init__()
        if not self.check_hex_color(color):
            raise RuntimeError(f"Expected hex color in format #FFFFFF, found: {color}")
        self.name = name
        self.color = color

    @staticmethod
    def check_hex_color(color_string: str):
        if not color_string.startswith("#"):
            return False
        if len(color_string) != 7:
            return False
        if re.sub("[0-9a-fA-F]", '', color_string[1:]) != '':
            return False
        return True

    @staticmethod
    def from_string(s: str) -> 'AnnotationSearch':
        s = s.lower()
        if s.startswith("tagsearch"):
            try:
                name = parse("tagsearch[{}]", s).fixed[0]
            except:
                raise RuntimeError(f"Expected tagsearch[name] found: {s}")

            return TagSearch(name)
        elif s.startswith("polygonssearch"):
            try:
                name, color = parse("polygonssearch[{},{}]", s).fixed
            except:
                raise RuntimeError(f"Expected polygonssearch[name,hexcolor] found: {s}")

            return PolygonsSearch(name, color=color)
        elif s.startswith("bboxsearch"):
            try:
                name, color = parse("bboxsearch[{},{}]", s).fixed
            except:
                raise RuntimeError(f"Expected bboxsearch[name,hexcolor] found: {s}")

            return BBoxSearch(name, color=color)
        elif s.startswith("textsearch"):
            try:
                name, color = parse("textsearch[{},{}]", s).fixed
            except:
                raise RuntimeError(f"Expected textsearch[query] found: {s}")

            return TextSearch(name)
        else:
            raise NotImplementedError()

    def to_string(self) -> str:
        raise NotImplementedError()

    def to_dict(self):
        return {
            "type": ANNOTATION_MAPPING[self.__class__],
            "name": self.name,
            "color": self.color,
        }

    @staticmethod
    def from_dict(d):
        if 'type' not in d:
            raise RuntimeError(f"Invalid dict: {d}")
        dtype = d.pop('type')
        if 'id' in d:
            d.pop("id")
        if dtype == "Tag":
            return TagSearch(d["name"])
        elif dtype == "Polygon":
            return PolygonsSearch(**d)
        elif dtype == "Box":
            return BBoxSearch(**d)
        elif dtype == "Text":
            return TextSearch(d["name"])
        else:
            raise NotImplementedError()

    def __repr__(self):
        return self.to_string()


class TagSearch(AnnotationSearch):
    def __init__(self, name):
        super(TagSearch, self).__init__(name, "#FFFFFF")

    @staticmethod
    def from_string(s):
        s = s.lower()
        return TagSearch(s)

    def to_string(self):
        return f"TagSearch[{self.name}]"


class TextSearch(AnnotationSearch):
    def __init__(self, query):
        super(TextSearch, self).__init__(query,
                                         "#FFFFFF")

    @staticmethod
    def from_string(s):
        s = s.lower()
        return TextSearch(s)

    def to_string(self):
        return f"TextSearch[{self.name}]"


class PolygonsSearch(AnnotationSearch):
    def __init__(self, name, color):
        super(PolygonsSearch, self).__init__(name, color)

    @staticmethod
    def from_string(s):
        s = s.lower()
        try:
            name, color = parse("{},{}", s).fixed
        except:
            raise RuntimeError(f"Expected name,hexcolor found: {s}")

        return PolygonsSearch(name, color=color)

    def to_string(self):
        return f"PolygonsSearch[{self.name},{self.color}]"


class BBoxSearch(AnnotationSearch):
    def __init__(self, name, color):
        super(BBoxSearch, self).__init__(name, color)

    @staticmethod
    def from_string(s):
        s = s.lower()
        try:
            name, color = parse("{},{}", s).fixed
        except:
            raise RuntimeError(f"Expected name,hexcolor found: {s}")

        return BBoxSearch(name, color=color)

    def to_string(self):
        return f"BBoxSearch[{self.name},{self.color}]"


ANNOTATION_MAPPING = {
    BBoxSearch: "Box",
    PolygonsSearch: "Polygon",
    TextSearch: "Text",
    TagSearch: "Tag",
    AnnotationSearch: "None",
}


class ImageWithAnnotations(object):
    def __init__(self, image=None,
                 annotations=None,
                 image_url=None):
        super(ImageWithAnnotations, self).__init__()
        if annotations is None:
            annotations = []

        self.image = image
        self.image_url = image_url
        self.annotations = annotations

    @staticmethod
    def annotation_from_dict(d, size,
                             annotation_id: int = 0):
        pietype = d.pop('type')
        if 'box' in d:
            d['bbox'] = BBox.create(np.int32(np.array(d.pop('box')) * np.array([size[0], size[1]] * 2)),
                                    style=BBox.MIN_MAX)
        if 'segmentation' in d:
            d["polygons"] = Polygons([(np.int32(np.array(p) * np.repeat([size[0], size[1]], len(p) // 2)))
                                      for p in d.pop('segmentation')])

        d["category"] = Category(d.pop('name'), color=d.pop('color'))
        return Annotation(**d,
                          id=annotation_id,
                          width=size[0],
                          height=size[1],
                          metadata={
                              "pietype": pietype
                          })

    @staticmethod
    def annotation_to_dict(annotation: Annotation):
        pietype = annotation.metadata.get('pietype')
        if pietype is None:
            raise NotImplementedError("Please provide type of Annotation")
        if pietype == "Text":
            text = annotation.category.name
            return {
                "type": "Text",
                "name": text,
            }
        elif pietype == "Tag":
            tag = annotation.category.name
            return {
                "type": "Tag",
                "name": tag,
            }
        elif pietype == "Polygon":

            box = np.array(list(annotation.bbox.top_left + annotation.bbox.bottom_right), dtype=np.float32)
            box /= np.array(np.repeat(annotation.size, 2), dtype=np.float32)

            segmentation = [(poly / np.repeat(annotation.size, poly.shape[0] // 2)).tolist()
                            for poly in annotation.polygons]

            return {
                "type": "Polygon",
                "name": annotation.category.name,
                "color": annotation.color.hex,
                "box": box.tolist(),
                "segmentation": segmentation
            }
        elif pietype == "Box":
            box = np.array(list(annotation.bbox.top_left + annotation.bbox.bottom_right), dtype=np.float32)
            box /= np.array(list(annotation.size + annotation.size), dtype=np.float32)
            return {
                "type": "Box",
                "name": annotation.category.name,
                "color": annotation.color.hex,
                "box": box.tolist(),
            }
        else:
            raise NotImplementedError("No such pietype")

    @staticmethod
    def from_dict(d):
        image_url = d["image_url"]

        image = from_url(image_url)
        if image is None:
            return ImageWithAnnotations(image_url=image_url)

        return ImageWithAnnotations(image,
                                    [ImageWithAnnotations.annotation_from_dict(ann, image.size)
                                     for ann in d["annotations"]],
                                    image_url=image_url)

    def to_dict(self):
        return {"image_url": self.image_url, "score": 1., "annotations": [self.annotation_to_dict(ann)
                                                                          for ann in self.annotations]}


__all__ = ["AnnotationSearch",
           "BBoxSearch",
           "PolygonsSearch",
           "TextSearch",
           "TagSearch",
           "ImageWithAnnotations"]
