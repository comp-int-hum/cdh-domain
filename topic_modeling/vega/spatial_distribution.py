from cdh import settings
from cdh.vega import CdhVisualization

class SpatialDistribution(CdhVisualization):

    def __init__(self, values, prefix=None):
        self.values = values[0]
        self.model_info = values[2]
        self.topic_names = list(set([v["topic"] for v in self.values]))
        self.prefix = prefix
        super(SpatialDistribution, self).__init__()

    @property
    def background(self):
        return {"value": "white"}

    @property
    def scales(self):
        return [
        ]

    @property
    def autosize(self):
        return "none"

    @property
    def signals(self):
        return [
            {"name": "width", "value": 800},
            {"name": "height", "value": 350},
            { "name": "scale", "value": 150},
            { "name": "rotate0", "value": 0},
            { "name": "rotate1", "value": 0},
            { "name": "rotate2", "value": 0},
            { "name": "center0", "value": 0},
            { "name": "center1", "value": 0},
            { "name": "translate0", "update": "width / 2" },
            { "name": "translate1", "update": "height / 2" },
            { "name": "graticuleDash", "value": 0},
            { "name": "borderWidth", "value": 1},
            { "name": "background", "value": "#ffffff"},
            { "name": "invert", "value": False},
            {
                "name": "topic",
                "bind" : {
                    "input" : "select",
                    "options" : list(range(len(self.topic_names))),
                    "labels" : self.topic_names, #[self.topic_names[x] for x in self.topics],
                },
                "init" : 0 #self.topic_names[0]
            },
            # {
            #     "name" : "words",
            #     "bind" : {
            #         "input" : "textarea",
            #         "element" : "{}_topicinfo".format(self.prefix)
            #     },
            #     "value" : self.topic_names[self.topics[0]],
            #     "on": [
            #         {
            #             "events" : {"signal" : "topic"},
            #             "update" : ""
            #         },
            #     ]
            # }
            #{"name": "tx", "update": "width / 2"},
            #{"name": "ty", "update": "height / 2"},
            #{"name": "scale", "value": 150, "on" : [{"events" : {"type" : "wheel", "consume" : True}, "update" : "clamp(scale * pow(1.0005, -event.deltaY * pow(16, event.deltaMode)), 150, 3000)"}]},
            #{"name": "angles", "value": [0, 0], "on": [{"events": "mousedown", "update": "[rotateX, centerY]"}]},
            #{"name": "cloned", "value": None, "on": [{"events": "mousedown", "update": "copy('focus')"}]},
            #{"name": "start", "value": None, "on": [{"events": "mousedown", "update": "invert(cloned, xy())" }]},
            #{"name": "drag", "value": None, "on": [{"events": "[mousedown, window:mouseup] > window:mousemove", "update": "invert(cloned, xy())"}]},
            #{"name": "delta", "value": None, "on": [{"events": {"signal": "drag"}, "update": "[drag[0] - start[0], start[1] - drag[1]]"}]},
            #{"name": "rotateX", "value": 0, "on": [{"events": {"signal": "delta"}, "update": "angles[0] + delta[0]"}]},
            #{"name": "centerY", "value": 0, "on": [{"events": {"signal": "delta"}, "update": "clamp(angles[1] + delta[1], -60, 60)"}]},
        ]

    @property
    def legend(self):
        return [
        ]

    @property
    def title(self):
        return {}
    
    @property
    def data(self):
        return [
            {
                "name": "topics",
                "values": self.values,
                "transform" : [
                {"type":"formula",
                "expr" : "datum.location[0]",
                "as" : "lon"
                },
                 {"type":"formula",
                  "expr" : "datum.location[1]",
                  "as" : "lat"
                },
                                {
                    "type" : "geopoint",
                    "projection" : "focus",
                    "fields" : ["lon", "lat"],
    "as" : ["x", "y"]
                }
                    #{
                    #    "type" : "filter",
                    #    "expr" : "topic == 0 || datum.properties.topic == topic"
                    #},
                ]
            },
            {
                "name" : "world",
                "url" : "/static/primary_sources/data/countries-110m.json",
                "format": {"type": "topojson", "feature" : "countries"},
            },
            {
                "name": "graticule",
                "transform": [
                    { "type": "graticule", "stepMinor" : [2, 2] }
                ]
            }
        ]

    @property
    def scales(self):
        return [
            {
                "name" : "color",
                "type" : "ordinal",
                "domain" : {"data" : "topics", "field" : "topic"},
                "range" : {"scheme" : "category20"},
            },
            {
                "name": "size",
                "type": "sqrt",
                "domain": [0.0, 1.0],
                "range": [1, 6]
            }
        ]
    
    @property
    def axes(self):
        return [
        ]
    
    @property
    def marks(self):
        return [
            {
                "type": "shape",
                "from": {"data": "graticule"},
                "zindex" : 1,
                "encode": {
                    "update": {
                        "strokeWidth": {"value": .1},
                        "stroke": {"value" : "white"},
                        "fill": {"value": None}
                    }
                },
                "transform": [
                    { "type": "geoshape", "projection": "focus" }
                ]
            },
            {
                "type": "shape",
                "from": {"data": "world"},
                "encode": {
                    "update": {
                        "strokeWidth": {"value" : 1},
                        "stroke": {"value": "#777"},
                        "fill": {"value": "#000"},
                        "zindex": {"value": 0}
                    },
                },
               "transform": [
                   { "type": "geoshape", "projection": "focus" }
                ]
            },
            # {
            #     "type": "shape",
            #     "from": {"data": "topics"},
            #     "encode": {
            #         "update": {
            #             "strokeWidth": {"value" : 0},
            #             "opacity": {"value": 0.25},
            #             "fill": {"value": "red"},
            #             "zindex": {"value": 1},
            #             "tooltip" : {"signal" : "datum.content"},
            #         },
            #     },
            #     "transform": [
            #         {
            #             "type": "geoshape",
            #             "projection": "focus",
            #             "field" : "location",
            #             "pointRadius" : 10, #{"expr": "scale('size', datum.weight)"},
            #         }
            #     ]
            # },
        {

            "type": "symbol",
            "from": {"data":"topics"},
            "encode": {
                "enter": {
                    "x" : {"field":"x"},
                    "y" : {"field":"y"},
                    "fill" : {"value" : "red"},
                    "tooltip" : {"value": "dsa"},
                    "size" : {"value" : 2}
                }
            }
        }
        ]
    
    @property
    def projections(self):
        return [
            {
                "name": "focus",
                "type": "mercator",
                "scale": {"signal": "scale"},
                "rotate": [
                    {"signal": "rotate0"},
                    {"signal": "rotate1"},
                    {"signal": "rotate2"}
                ],
                "center": [
                    {"signal": "center0"},
                    {"signal": "center1"}
                ],
                "translate": [
                    {"signal": "translate0"},
                    {"signal": "translate1"}
                ]
            },
        ]

