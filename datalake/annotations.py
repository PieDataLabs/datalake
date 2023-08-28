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
    def from_dict(d):
        image_url = d["image_url"]

        image = from_url(image_url)
        if image is None:
            return ImageWithAnnotations(image_url=image_url)

        def create_annotation(size, d):
            if 'box' in d:
                d['bbox'] = BBox.create(np.int32(np.array(d.pop('bbox')) * np.array([size[0], size[1]] * 2)),
                                        style=BBox.MIN_MAX)
            if 'segmentation' in d:
                polygons = [np.int32(poly.reshape([-1, 2]) * np.array([[size[0], size[1]]]))
                            for poly in d.pop('segmentation')]
                d["polygons"] = Polygons.create(polygons)
            d["category"] = Category(d.pop('name'), color=d.pop('color'))
            return Annotation(**d, id=None)

        return ImageWithAnnotations(image,
                                    [create_annotation(image.size, ann)
                                     for ann in d["annotations"]],
                                    image_url=image_url)


__all__ = ["AnnotationSearch",
           "BBoxSearch",
           "PolygonsSearch",
           "TextSearch",
           "TagSearch",
           "ImageWithAnnotations"]
