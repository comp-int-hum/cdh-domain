from cdh import settings
from cdh.vega import CdhVisualization




class TemporalEvolution(CdhVisualization):

    def __init__(self, values, prefix=None):
        self.prefix = prefix
        print(self.prefix)
        self.model_info = values[2]
        #print(values[1][0])
        self.values = [] #values #[0:10]        
        #elf.buckets = list(sorted(values[1].items()))
        #self.min_timestamp = self.buckets[0][1]["start"]
        #self.max_timestamp = self.buckets[-1][1]["end"]
        for bucket, info in sorted(values[1].items(), key=lambda x : x[0]):
            total = sum(info["weights"].values())
            for topic, count in info["weights"].items():
                self.values.append(
                    {
                        "bucket" : bucket,
                        "topic" : topic,
                        "count" : count,
                        "percent" : count / total
                    }
                )
        #print([x["topic"] for x in self.values if x["bucket"] == 0])
        #print(self.buckets, self.min_timestamp, self.max_timestamp)
        super(TemporalEvolution, self).__init__()

    @property
    def background(self):
        return "black"

    @property
    def signals(self):
        return [
            {
                "name": "width",
                "value": 800
            },
            {
                "name": "height",
                "value": 350
            },
            # {
            #     "name": "tooltip",
            #     "value": {},
            #     "on": [
            #         {"events": "rect:mouseover", "update": "datum"},
            #         {"events": "rect:mouseout",  "update": "{}"}
            #     ]
            # },
            {
                "name" : "topic",
                "value" : "",
                "bind" : {
                    "input" : "textarea",
                    "element" : "#{}_1".format(self.prefix) if self.prefix else "#topicinfo"
                },
                "on" : [
                   {"events" : "area:mouseover", "update" : "datum.topic"},
                   {"events" : "area:mouseout", "update" : {"value" : ""}}
                ],
            },
            # {
            #     "name" : "time",
            #     "value" : "None",
            #     "bind" : {
            #         "element" : "#{}_2".format(self.prefix) if self.prefix else "#timeinfo"
            #     },
            #     "on" : [
            #         {
            #             "events" : "area:mousemove",
            #             #"update" : "utcFormat(1000*round(extent(pluck(data('temporal_weights'), 'time'))[0] + ((x() / width) * ((extent(pluck(data('temporal_weights'), 'time'))[1]) - (extent(pluck(data('temporal_weights'), 'time'))[0])))), '%m/%d/%Y')",
            #         },
            #         {"events" : "area:mouseout", "update" : {"value" : ""}}
            #     ],
            # }
            
        ]
        
    @property
    def data(self):
        return [
            {
                "name": "temporal_weights",
                "values": self.values,
                "transform": [
                    {
                        "type": "stack",
                        "field": "percent",
                        "groupby": ["bucket"],
                        "sort": {
                            "field": ["topic"],
                            "order": ["descending"]
                        }
                    },
                    # {
                    #     "type" : "bin",
                    #     "maxbins" : 10,
                    #     "field" : "timestamp",
                    #     "interval" : False,
                    #     "as" : ["timebin", "other"],
                    #     "extent" : [self.min_timestamp, self.max_timestamp]
                    # },
                    # {
                    #     "type": "aggregate",
                    #     "cross" : True,
                    #     "groupby": [
                    #         "timebin",
                    #         "label"
                    #     ],
                    #     "fields": [
                    #         "value",
                    #         "value"
                    #     ],
                    #     "ops": [
                    #         "sum",
                    #         "argmax"
                    #     ],
                    #     "as": [
                    #         "sum",
                    #         "argmax"
                    #     ]
                    # },
                    # {
                    #     "type": "stack",
                    #     "field": "sum",
                    #     "offset": "normalize",
                    #     "groupby": ["timebin"],
                    #     "sort": {
                    #         "field": ["label"],
                    #         "order": ["descending"]
                    #     }
                    # }
                ]
            },
            {
                "name": "series",
                "source": "temporal_weights",
                "transform": [
                    {
                        "type": "aggregate",
                        "groupby": ["bucket"],
                        "fields": ["percent", "percent"],
                        "ops": ["sum", "argmax"],
                        "as": ["sum", "argmax"]
                    }
                ]
            }            
        ]

    @property
    def scales(self):
        return [
            {
                "name": "xscale",
                "type": "point",
                "range": "width",
                "domain": {"data": "temporal_weights", "field": "bucket"}
            },
            {
                "name": "yscale",
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
                "domain": {"data": "temporal_weights", "field": "topic"}
            },
            {
                "name": "font",
                "type": "sqrt",
                "range": [0, 20], "round": True, "zero": True,
                "domain": {"data": "series", "field": "argmax.value"}
            },
            {
                "name": "opacity",
                "type": "quantile",
                "range": [0, 0, 0, 0, 0, 0.1, 0.2, 0.4, 0.7, 1.0],
                "domain": {"data": "series", "field": "argmax.value"}
            }
        ]

    
    @property
    def marks(self):
        return [
            {
                "type": "group",
                "from": {
                    #"data" : "series",
                    "facet": {
                        "name": "facet",
                        "data": "temporal_weights",
                        "groupby": ["topic"]
                    }
                },
                "marks": [
                    {
                        "type": "area",
                        "from": {"data": "facet"},
                        #"tooltip" : {"value" : "dsadsa"},
                        "encode": {
                            "update": {
                                "x": {"scale": "xscale", "field": "bucket"},
                                "y": {"scale": "yscale", "field": "y0"},
                                "y2": {"scale": "yscale", "field": "y1"},
                                "fill": {"scale": "color", "field": "topic"},
                                "fillOpacity": {"value": 1.0}
                            },
                            "hover": {
                                "fillOpacity": {"value": 0.5}
                            },
                        },                    
                    }

                ]
            }
            # ,
            # {
            #     "type": "text",
            #     "from": {"data": "temporal_weights"},
            #     "interactive": False,
            #     "encode": {
            #         "update": {
            #             "x": {"scale": "x", "field": "bucket"},
            #             #"dx": {"scale": "offset", "field": "argmax.time"},
            #             "y": {"signal": "scale('y', 0.5 * (datum.y0 + datum.y1))"},
            #             "fill": {"value": "#000"},
            #             #"fillOpacity": {"scale": "opacity", "field": "value"},
            #             "fontSize": {"scale": "font", "field": "value", "offset": 5},
            #             "text": {"field": "topic"},
            #             #"align": {"scale": "align", "field": "time"},
            #             "baseline": {"value": "middle"}
            #         }
            #     }
            # }
            
        ]

    # @property
    # def scales(self):
    #     return [
    #         {
    #             "name": "xscale",
    #             "type": "point",
    #             "range": "width",
    #             "domain": {"data": "temporal_weights", "field": "timebin"}
    #         },
    #         {
    #             "name": "yscale",
    #             "type": "linear",
    #             "range": "height",
    #             "nice": True,
    #             "zero": True,
    #             "domain": {"data": "temporal_weights", "field": "y1"}
    #         },
    #         {
    #             "name": "color",
    #             "type": "ordinal",
    #             "range": "category",
    #             "domain": {"data": "temporal_weights", "field": "label"}
    #         },
    #         # {
    #         #    "name": "offset",
    #         #    "type": "quantize",
    #         #    "range": [6, 0, -6], "zero": False,
    #         #     #"domain": [1730, 2130]
    #         # },
    #         # # {
    #         # #     "name": "alpha",
    #         # #     "type": "linear", "zero": true,
    #         # #     "domain": {"data": "series", "field": "sum"},
    #         # #     "range": [0.4, 0.8]
    #         # # },
    #         {
    #             "name": "font",
    #             "type": "sqrt",
    #             "range": [0, 20], "round": True, "zero": True,
    #             "domain": {"data": "sseries", "field": "argmax.value"}
    #         },
    #         {
    #             "name": "opacity",
    #             "type": "quantile",
    #             "range": [0, 0, 0, 0, 0, 0.1, 0.2, 0.4, 0.7, 1.0],
    #             "domain": {"data": "sseries", "field": "argmax.value"}
    #         },
    #         # {
    #         #     "name": "align",
    #         #     "type": "quantize",
    #         #     "range": ["left", "center", "right"], "zero": False,
    #         #     #"domain": [1730, 2130]
    #         # },
    #     ]

    @property
    def background(self):
        return "black"
    #    return {"value": "white"}

    
    #@property
    #def signals(self):
    #    return [
    #    ]

    # @property
    # def marks(self):
    #     return [
    #         {
    #             "type": "group",
    #             "from": {
    #                 "facet": {
    #                     "name": "series",
    #                     "data": "temporal_weights",
    #                     "groupby": ["label"]
    #                 }
    #             },
    #             "marks": [
    #                 {
    #                     "type": "area",
    #                     "from": {"data": "series"},
    #                     #"tooltip" : {"value" : "dsadsa"},
    #                     "encode": {
    #                         "update": {
    #                             "x": {"scale": "xscale", "field": "timebin"},
    #                             "y": {"scale": "yscale", "field": "y0"},
    #                             "y2": {"scale": "yscale", "field": "y1"},
    #                             "fill": {"scale": "color", "field": "label"},
    #                             "fillOpacity": {"value": 1.0}
    #                         },
    #                         "hover": {
    #                             "fillOpacity": {"value": 0.5}
    #                         },
    #                     },                    
    #                 }

    #             ]
    #         },
    #         # {
    #         #     "type": "text",
    #         #     "from": {"data": "temporal_weights"},
    #         #     "interactive": False,
    #         #     "encode": {
    #         #         "update": {
    #         #             "x": {"scale": "x", "field": "time"},
    #         #             #"dx": {"scale": "offset", "field": "argmax.time"},
    #         #             "y": {"signal": "scale('y', 0.5 * (datum.y0 + datum.y1))"},
    #         #             "fill": {"value": "#000"},
    #         #             "fillOpacity": {"scale": "opacity", "field": "value"},
    #         #             "fontSize": {"scale": "font", "field": "value", "offset": 5},
    #         #             "text": {"field": "label"},
    #         #             #"align": {"scale": "align", "field": "time"},
    #         #             "baseline": {"value": "middle"}
    #         #         }
    #         #     }
    #         # }
    #     ]




# class SpatialDistribution(CdhVisualization):

#     def __init__(self, values, prefix=None):
#         self.values = values
#         self.prefix = prefix
#         super(SpatialDistribution, self).__init__()

#     @property
#     def background(self):
#         return {"value": "white"}

#     @property
#     def scales(self):
#         return [
#         ]

#     @property
#     def autosize(self):
#         return "none"

#     @property
#     def signals(self):
#         return [
#             {"name": "width", "value": 800},
#             {"name": "height", "value": 350},
#             { "name": "scale", "value": 150},
#             { "name": "rotate0", "value": 0},
#             { "name": "rotate1", "value": 0},
#             { "name": "rotate2", "value": 0},
#             { "name": "center0", "value": 0},
#             { "name": "center1", "value": 0},
#             { "name": "translate0", "update": "width / 2" },
#             { "name": "translate1", "update": "height / 2" },
#             { "name": "graticuleDash", "value": 0},
#             { "name": "borderWidth", "value": 1},
#             { "name": "background", "value": "#ffffff"},
#             { "name": "invert", "value": False},
#             #{"name": "tx", "update": "width / 2"},
#             #{"name": "ty", "update": "height / 2"},
#             #{"name": "scale", "value": 150, "on" : [{"events" : {"type" : "wheel", "consume" : True}, "update" : "clamp(scale * pow(1.0005, -event.deltaY * pow(16, event.deltaMode)), 150, 3000)"}]},
#             #{"name": "angles", "value": [0, 0], "on": [{"events": "mousedown", "update": "[rotateX, centerY]"}]},
#             #{"name": "cloned", "value": None, "on": [{"events": "mousedown", "update": "copy('focus')"}]},
#             #{"name": "start", "value": None, "on": [{"events": "mousedown", "update": "invert(cloned, xy())" }]},
#             #{"name": "drag", "value": None, "on": [{"events": "[mousedown, window:mouseup] > window:mousemove", "update": "invert(cloned, xy())"}]},
#             #{"name": "delta", "value": None, "on": [{"events": {"signal": "drag"}, "update": "[drag[0] - start[0], start[1] - drag[1]]"}]},
#             #{"name": "rotateX", "value": 0, "on": [{"events": {"signal": "delta"}, "update": "angles[0] + delta[0]"}]},
#             #{"name": "centerY", "value": 0, "on": [{"events": {"signal": "delta"}, "update": "clamp(angles[1] + delta[1], -60, 60)"}]},
#         ]

#     @property
#     def legend(self):
#         return [
#         ]

#     @property
#     def title(self):
#         return {}
    
#     @property
#     def data(self):        
#         return [
#             {
#                 "name": "topics",
#                 "values": self.values,
#                 #"transform" : [
#                 #    {
#                 #        "type" : "geoshape",
#                 #        #"projection" : "focus",
#                 #        "field" : "datum.bounding_box",
#                 #    }
#                 #],
#             },
#             {
#                 "name" : "world",
#                 "url" : "/static/primary_sources/data/countries-110m.json",
#                 "format": {"type": "topojson", "feature" : "countries"},
#             },
#             {
#                 "name": "graticule",
#                 "transform": [
#                     { "type": "graticule", "stepMinor" : [2, 2] }
#                 ]
#             }
#         ]

#     @property
#     def scales(self):
#         return [
#             #{
#             #    "name" : "color",
#             #    "type" : "ordinal",
#             #    "domain" : {"data" : "starcoder", "field" : {"signal" : "dependent"}},
#             #    "range" : {"scheme" : "category20"},
#             #}
#         ]
    
#     @property
#     def axes(self):
#         return [
#         ]
    
#     @property
#     def marks(self):
#         return [
#             {
#                 "type": "shape",
#                 "from": {"data": "graticule"},
#                 "zindex" : 1,
#                 "encode": {
#                     "update": {
#                         "strokeWidth": {"value": .1},
#                         "stroke": {"value" : "white"},
#                         "fill": {"value": None}
#                     }
#                 },
#                 "transform": [
#                     { "type": "geoshape", "projection": "focus" }
#                 ]
#             },
#             {
#                 "type": "shape",
#                 "from": {"data": "world"},
#                 "encode": {
#                     "update": {
#                         "strokeWidth": {"value" : 1},
#                         "stroke": {"value": "#777"},
#                         "fill": {"value": "#000"},
#                         "zindex": {"value": 0}
#                     },
#                 },
#                "transform": [
#                    { "type": "geoshape", "projection": "focus" }
#                 ]
#             },
#             {
#                 "type": "shape",
#                 "from": {"data": "topics"},
#                 #"shape" : "circle",
#                 "encode": {
#                     "update": {
#                         "strokeWidth": {"value" : 0},
#                         #"stroke": {"value": "red"},
#                         "fill": {"value": "blue"},
#                         "zindex": {"value": 1},
#                         "tooltip" : {"signal" : "datum.content"},
#                     },
#                 },
#                 "transform": [
#                     { "type": "geoshape", "projection": "focus", "field": "datum.bounding_box" }
#                 ]
#             },

#         ]
    
#     @property
#     def projections(self):
#         return [
#             {
#                 "name": "focus",
#                 "type": "mercator", #{"signal": "type"},
#                 "scale": {"signal": "scale"},
#                 "rotate": [
#                     {"signal": "rotate0"},
#                     {"signal": "rotate1"},
#                     {"signal": "rotate2"}
#                 ],
#                 "center": [
#                     {"signal": "center0"},
#                     {"signal": "center1"}
#                 ],
#                 "translate": [
#                     {"signal": "translate0"},
#                     {"signal": "translate1"}
#                 ]
#             },
#         ]

