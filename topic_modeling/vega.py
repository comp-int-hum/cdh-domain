from cdh import settings
from cdh.vega import BaseVisualization


class TopicModelWordCloud(BaseVisualization):
    def __init__(self, words):
        self.values = words  # spec was word/prob pairs
        # self.values = [
        #   {
        #       "topic": 0, 
        #       "word": word, 
        #       "value": float(prob),
        #       #"link": "{}://{}:{}/topic_modeling/word_filler/{}".format(settings.PROTO, settings.HOSTNAME, settings.PORT, wid),
        #   } for wid, (word, prob) in enumerate(topic)]
        # self.num_topics = 1
        super(TopicModelWordCloud, self).__init__()

    @property
    def background(self):
        return {"value": "blue"}

    @property
    def scales(self):
        return [
            {
                "name": "groupy",
                "type": "band",
                "domain": {"data": "words", "field": "topic"},
                "range": {"step": {"signal" : "cellHeight"}}
            },
            {
                "name": "cscale",
                "type": "ordinal",
                "range": {"scheme": "category20"},
                "domain": {"data": "words", "field": "topic"}
            },
        ]

    @property
    def signals(self):
        return [
            {"name": "width", "value": 400},
            {"name": "cellHeight", "value": 300},
            {"name": "cellWidth", "value": 400},
            {"name": "height", "update": "domain('groupy') * cellHeight"}, #300 * 10},
        ]

    @property
    def data(self):
        return [
            {
                "name": "words",
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
                        "data": "words",
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
                                "fill": {"scale": "cscale", "field": "topic"},
                            },
                            "update": {
                                #"y": {
                                #    "scale": "groupy",
                                #    "field": "topic",
                                    #"offset": {"signal" : "-zoom * 20"}
                                #}

                                #"href": {"signal": "datum.link"}
                            }
                        },
                        "transform": [
                            {
                                "type": "wordcloud",
                                "size": [{"signal": "cellWidth"}, {"signal": "cellHeight"}],
                                #"text": {"value" : "test"}, #{"field": "datum.word"},
                                "rotate": {"field": "datum.angle"},
                                "font": "Helvetica Neue, Arial",
                                "fontSize": {"field": "datum.probability"},
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
            # # {
            # #     "name": "alpha",
            # #     "type": "linear", "zero": true,
            # #     "domain": {"data": "series", "field": "sum"},
            # #     "range": [0.4, 0.8]
            # # },
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
                #"bind" : {
                #    "element" : "#words"
                #    #"input" : "text"
                #},
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

    #@property
    #def autosize(self):
    #    return "fit"

    @property
    def signals(self):
        return [
            {"name": "width", "value": 800},
            {"name": "height", "value": 350},

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
                #"scale": {"signal": "scale"},
                #"rotate": [{"signal": "rotateX"}, 0, 0],
                #"center": [0, {"signal": "centerY"}],
                #"translate": [{"signal": "tx"}, {"signal": "ty"}]
                # "scale": {"signal": "scale"},
                # "rotate": [
                #     {"signal": "rotate0"},
                #     {"signal": "rotate1"},
                #     {"signal": "rotate2"}
                # ],
                # "center": [
                #     {"signal": "center0"},
                #     {"signal": "center1"}
                # ],
                # "translate": [
                #     {"signal": "translate0"},
                #     {"signal": "translate1"}
                # ]
                
                #     #"fit" : {"signal" : "data('table')"},
            #     #"scale" : 500,                
            #     #"size" : {"signal" : "[width,height]"},
             }
        ]
