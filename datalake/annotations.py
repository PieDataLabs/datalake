import re

from parse import parse


class Annotation(object):
    def __init__(self, name, color):
        super(Annotation, self).__init__()
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
    def from_string(s: str) -> 'Annotation':
        s = s.lower()
        if s.startswith("tag"):
            try:
                name = parse("tag[{}]", s).fixed[0]
            except:
                raise RuntimeError(f"Expected tag[name] found: {s}")

            return Tag(name)
        elif s.startswith("polygon"):
            try:
                name, color = parse("polygon[{},{}]", s).fixed
            except:
                raise RuntimeError(f"Expected polygon[name,hexcolor] found: {s}")

            return Polygon(name, color=color)
        elif s.startswith("box"):
            try:
                name, color = parse("box[{},{}]", s).fixed
            except:
                raise RuntimeError(f"Expected box[name,hexcolor] found: {s}")

            return Box(name, color=color)
        else:
            raise NotImplementedError()

    def to_string(self) -> str:
        raise NotImplementedError()

    def to_dict(self):
        return {
            "type": self.__class__.__name__,
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
            return Tag(d["name"])
        elif dtype == "Polygon":
            return Polygon(**d)
        elif dtype == "Box":
            return Box(**d)
        elif dtype == "Text":
            return Text(d["name"] == "detailed")
        else:
            raise NotImplementedError()

    def __repr__(self):
        return self.to_string()


class Tag(Annotation):
    def __init__(self, name):
        super(Tag, self).__init__(name, "#FFFFFF")

    @staticmethod
    def from_string(s):
        s = s.lower()
        return Tag(s)

    def to_string(self):
        return f"Tag[{self.name}]"


class Text(Annotation):
    def __init__(self, detailed=False):
        super(Text, self).__init__("detailed" if detailed else "common",
                                   "#FFFFFF")

    @staticmethod
    def from_string(s):
        s = s.lower()
        if s == "detailed":
            return Text(detailed=True)
        elif s == "common":
            return Text(detailed=False)
        else:
            raise NotImplementedError()

    def to_string(self):
        if self.name == "detailed":
            return f"Text[detailed]"
        else:
            return "Text[common]"


class Polygon(Annotation):
    def __init__(self, name, color):
        super(Polygon, self).__init__(name, color)

    @staticmethod
    def from_string(s):
        s = s.lower()
        try:
            name, color = parse("{},{}", s).fixed
        except:
            raise RuntimeError(f"Expected name,hexcolor found: {s}")

        return Polygon(name, color=color)

    def to_string(self):
        return f"Polygon[{self.name},{self.color}]"


class Box(Annotation):
    def __init__(self, name, color):
        super(Box, self).__init__(name, color)

    @staticmethod
    def from_string(s):
        s = s.lower()
        try:
            name, color = parse("{},{}", s).fixed
        except:
            raise RuntimeError(f"Expected name,hexcolor found: {s}")

        return Box(name, color=color)

    def to_string(self):
        return f"Box[{self.name},{self.color}]"
