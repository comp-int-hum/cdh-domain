from cdh import settings

class BaseVisualization(object):

    def __init__(self, *argv, **argd):
        pass
        #self.project_id = project_id
        #self.ifield = independent_field
        #self.schema = schema
        #self.relationships = {"" : []}
        #for field in self.schema["entity_types"][self.ifield[0]]["data_fields"]:
        #    ft = self.schema["data_fields"][field]["type"]
        #    if field != self.ifield[1] and ft in dependent_types:
        #        self.relationships[""].append((self.ifield[0], field, ft))

    @property
    def json(self):
        retval = {
            "$schema": "https://vega.github.io/schema/vega/v5.json",
            "description": self.description,
            "background": self.background,
            "width": self.width,
            "height": self.height,
            "padding": self.padding,
            "autosize": self.autosize,
            "config" : self.config,
            "signals": self.signals,
            "data": self.data,
            "scales": self.scales,
            "projections": self.projections,
            "axes": self.axes,
            "legends": self.legends,
            "title" : self.title,
            "marks": self.marks,
            "encode": self.encode,
            "usermeta": self.usermeta,
        }
        return retval

    @property
    def description(self):
        return "A Vega visualization."

    @property
    def width(self):
        return 640

    @property
    def height(self):
        return 480

    @property
    def padding(self):
        return None

    @property
    def autosize(self):
        return None

    @property
    def background(self):
        return None

    @property
    def legends(self):
        return []

    @property
    def projections(self):
        return []

    @property
    def other_data(self):
        return []

    @property
    def signals(self):
        return []

    @property
    def config(self):
        return []

    @property
    def title(self):
        return None

    @property
    def transforms(self):
       return []

    @property
    def marks(self):
        return []

    @property
    def axes(self):
        return []

    @property
    def scales(self):
        return []

    @property
    def data(self):
        return []

    @property
    def scales(self):
        return []

    @property
    def encode(self):
        return []

    @property
    def usermeta(self):
        return []

class WordCloud(BaseVisualization):
    def __init__(self, topic):
        self.values = []  # spec was word/prob pairs
        self.values = [
          {
              "topic": 0, 
              "word": word, 
              "value": float(prob),
              #"link": "{}://{}:{}/topic_modeling/word_filler/{}".format(settings.PROTO, settings.HOSTNAME, settings.PORT, wid),
          } for wid, (word, prob) in enumerate(topic)]
        self.num_topics = 1
        super(WordCloud, self).__init__()

    @property
    def background(self):
        return {"value": "blue"}

    @property
    def scales(self):
        return [
            {
                "name": "groupy",
                "type": "band",
                "range": "height",
                "domain": {"data": "starcoder_data", "field": "topic"}
            },
            {
                "name": "cscale",
                "type": "ordinal",
                "range": {"scheme": "category20"},
                "domain": {"data": "starcoder_data", "field": "type"}
            },
        ]

    @property
    def autosize(self):
        return "pad"

    @property
    def signals(self):
        return [
            {"name": "width", "value": 400},
            {"name": "cellHeight", "value": 300},
            {"name": "cellWidth", "value": 400},
            {"name": "height", "value": 300 * self.num_topics},
        ]

    @property
    def data(self):
        return [
            {
                "name": "starcoder_data",
                "values": self.values,
                "transform": [
                    {
                        "type": "formula", "as": "angle",
                        "expr": "[-45, 0, 45][~~(random() * 3)]"
                    },
                    {
                        "type": "formula", "as": "size",
                        "expr": "round(datum.value * 200)"
                    }
                ]
            }
        ]

    @property
    def marks(self):
        return [
            {
                "type": "group",
                "from": {
                    "facet": {
                        "name": "facet",
                        "data": "starcoder_data",
                        "groupby": "topic",
                    }
                },
                "encode": {
                    "update": {
                        "y": {"scale": "groupy", "field": "topic"},
                        "fill": {"value": "blue"},
                        "stroke": {"value": "blue"},
                    },
                },
                "marks": [
                    {
                        "type": "text",
                        "from": {"data": "facet"},
                        "encode": {
                            "enter": {
                                "text": {"signal": "datum.word"},
                                "align": {"value": "center"},
                                "baseline": {"value": "alphabetic"},
                                "fill": {"scale": "cscale", "field": "type"},
                            },
                            "update": {
                              "href": {"signal": "datum.link"}
                            }
                        },
                        "transform": [
                            {
                                "type": "wordcloud",
                                "size": [{"signal": "cellWidth"}, {"signal": "cellHeight"}],
                                "text": {"field": "datum.word"},
                                "rotate": {"field": "datum.angle"},
                                "font": "Helvetica Neue, Arial",
                                "fontSize": {"field": "datum.size"},
                                "fontSizeRange": [12, 56],
                                "padding": 2
                            }
                        ],
                    }
                ]
            },
        ]


class TemporalEvolution(BaseVisualization):

    def __init__(self, values):
        self.values = values
        #self.topics = topics
        super(TemporalEvolution, self).__init__()

    @property
    def background(self):
        return {"value": "white"}

    @property
    def scales(self):
        return [
            {
                "name": "x",
                "type": "point",
                "range": "width",
                "domain": {"data": "temporal_weights", "field": "year"}
            },
            {
                "name": "y",
                "type": "linear",
                "range": "height",
                "nice": True,
                "zero": True,
                "domain": {"data": "temporal_weights", "field": "y1"}
            },
            {
                "name": "color",
                "type": "ordinal",
                "range": "category",
                "domain": {"data": "temporal_weights", "field": "label"}
            },
            {
               "name": "offset",
               "type": "quantize",
               "range": [6, 0, -6], "zero": False,
                #"domain": [1730, 2130]
            },
            # {
            #     "name": "alpha",
            #     "type": "linear", "zero": true,
            #     "domain": {"data": "series", "field": "sum"},
            #     "range": [0.4, 0.8]
            # },
            {
                "name": "font",
                "type": "sqrt",
                "range": [0, 20], "round": True, "zero": True,
                "domain": {"data": "sseries", "field": "argmax.value"}
            },
            {
                "name": "opacity",
                "type": "quantile",
                "range": [0, 0, 0, 0, 0, 0.1, 0.2, 0.4, 0.7, 1.0],
                "domain": {"data": "sseries", "field": "argmax.value"}
            },
            {
                "name": "align",
                "type": "quantize",
                "range": ["left", "center", "right"], "zero": False,
                #"domain": [1730, 2130]
            },
        ]

    @property
    def autosize(self):
        return "pad"

    @property
    def signals(self):
        return [
            {"name": "width", "value": 800},
            {"name": "cellWidth", "value": 800},
            {"name": "height", "value": 350},
            {"name": "cellHeight", "value": 350},
            {
                "name": "tooltip",
                "value": {},
                "on": [
                    {"events": "rect:mouseover", "update": "datum"},
                    {"events": "rect:mouseout",  "update": "{}"}
                ]
            },
            {
                "name" : "topic",
                "value" : "None",
                "bind" : {
                    "element" : "#words"
                    #"input" : "text"
                },
                "on" : [
                    {"events" : "area:mouseover", "update" : "datum.label"}
                ],
            }
        ]

    @property
    def legend(self):
        return [
        ]

    @property
    def title(self):
        return {}
        #     "text" : "testing",
        #     "encode" : {
        #         "title" : {
        #             "interactive" : True,
        #             "update": {
        #                 "fontStyle": {"value": "italic"}
        #             },
        #             "hover": {
        #                 "fontStyle": {"value": "normal"}
        #             },
        #             "enter" : {
        #                 "fill" : {"value" : "white"}
        #             }
        #         }
        #     }
        # }
    
    @property
    def data(self):
        return [
            {
                "name": "temporal_weights",
                "values": self.values,
                "transform": [
                    {
                        "type": "stack",
                        "field": "value",
                        "groupby": ["year"],
                        "sort": {
                            "field": ["label"],
                            "order": ["descending"]
                        }
                    }
                ]
            },
            #{
            #    "name": "topics",
            #    "values": self.topics,
            #    "transform": [
            #    ]
            #},
            {
                "name": "sseries",
                "source": "temporal_weights",
                "transform": [
                    {
                        "type": "aggregate",
                        "groupby": ["year"],
                        "fields": ["value", "value"],
                        "ops": ["sum", "argmax"],
                        "as": ["sum", "argmax"]
                    }
                ]
            }
        ]

    @property
    def axes(self):
        return [
            {
                "orient": "bottom", "scale": "x", "zindex" : 1, "format": "d"
            },
            {
                "orient": "right", "scale": "y", "zindex" : 1 #"format": "%", "tickCount": 10
                #"grid": True, "domain": False, "tickSize": 12,
                #"encode": {
                #    "grid": {"enter": {"stroke": {"value": "#ccc"}}},
                #    "ticks": {"enter": {"stroke": {"value": "#ccc"}}}
                #}
            }
        ]
    
    @property
    def marks(self):
        return [
            {
                "type": "group",
                "from": {
                    "facet": {
                        "name": "series",
                        "data": "temporal_weights",
                        "groupby": ["label"]
                    }
                },
                "marks": [
                    {
                        "type": "area",
                        "from": {"data": "series"},
                        #"tooltip" : {"value" : "dsadsa"},
                        "encode": {
                            "update": {
                                "x": {"scale": "x", "field": "year"},
                                "y": {"scale": "y", "field": "y0"},
                                "y2": {"scale": "y", "field": "y1"},
                                "fill": {"scale": "color", "field": "label"},
                                "fillOpacity": {"value": 1.0}
                            },
                            "hover": {
                                "fillOpacity": {"value": 0.5}
                            },
                        },                    
                    }

                ]
            },
            # {
            #     "type": "text",
            #     "from": {"data": "temporal_weights"},
            #     "interactive": False,
            #     "encode": {
            #         "update": {
            #             "x": {"scale": "x", "field": "year"},
            #             #"dx": {"scale": "offset", "field": "argmax.year"},
            #             "y": {"signal": "scale('y', 0.5 * (datum.y0 + datum.y1))"},
            #             "fill": {"value": "#000"},
            #             "fillOpacity": {"scale": "opacity", "field": "value"},
            #             "fontSize": {"scale": "font", "field": "value", "offset": 5},
            #             "text": {"field": "label"},
            #             #"align": {"scale": "align", "field": "year"},
            #             "baseline": {"value": "middle"}
            #         }
            #     }
            # }
        ]




class SpatialDistribution(BaseVisualization):

    def __init__(self, values):
        self.values = values
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
        return "pad"

    @property
    def signals(self):
        return [
            {"name": "width", "value": 800},
            {"name": "height", "value": 350},
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
                    {
                        "type" : "geopoint",
                        "projection" : "focus",
                        "fields" : ["longitude", "latitude"],
                    }
                ],
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
            #{
            #    "name" : "color",
            #    "type" : "ordinal",
            #    "domain" : {"data" : "starcoder", "field" : {"signal" : "dependent"}},
            #    "range" : {"scheme" : "category20"},
            #}
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
            {
                "type": "symbol",
                "from": {"data": "topics"},
                "shape" : "circle",
                "encode": {
                    "enter": {
                        "size": {"value" : 4}, #{"scale": "size", "field": "traffic.flights"},
                        "fill": {"value": "steelblue"},
                        "fillOpacity": {"value": 0.8},
                        "stroke": {"value": "white"},
                        "strokeWidth": {"value": 0}
                    },
                    "update": {
                        "x": {"field": "x"},
                        "y": {"field": "y"}
                    }
                }

                # "encode": {
                #     "update": {
                #         "x": {"field": "longitude"},
                #         "y": {"field": "latitude"},
                #         "fill" : {
                #             #"scale" : "color",
                #             "value" : "red",
                #             "field" : "weight",#{"signal" : "dependent"},
                #         },
                #         "size" : {"value" : 40},
                #     }
                # },
                #"transform" : [
                #    {"type" : "geopoint", "projection": "focus"}
                #]
            },

        ]
    
    @property
    def projections(self):
        return [
            #{
            #    "name": "overall",
            #    "type" : "mercator",
            #},
            {
                 "name": "focus",
                 "type" : "mercator",
            #     #"fit" : {"signal" : "data('table')"},
            #     #"scale" : 500,                
            #     #"size" : {"signal" : "[width,height]"},
             }
        ]
