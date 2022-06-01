#from interact import models
import datetime

dependent_types = [
    "scalar",
    "numeric",
    "categorical"
]

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
        return "A specification outline example."
    
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


class StarcoderVisualization(BaseVisualization):
    
    def __init__(self, project_id, schema, independent_field, *argv, **argd):        
        super(StarcoderVisualization, self).__init__(*argv, **argd)
        self.project_id = project_id
        self.ifield = independent_field
        self.ifield_name = "{}({})".format(self.ifield[0].title(), self.ifield[1])
        self.schema = schema
        self.relationships = {"" : []}
        self.dfield_names = []
        for field in self.schema["entity_types"][self.ifield[0]]["data_fields"]:
            ft = self.schema["data_fields"][field]["type"]
            if field != self.ifield[1] and ft in dependent_types:
                self.relationships[""].append((self.ifield[0], field, ft))
                self.dfield_names.append((ft, "{}({})".format(self.ifield[0].title(), field)))
                
    @property
    def title(self):
        return None #"Plotting against {}({})".format(self.ifield[0].title(), self.ifield[1])

    @property
    def signals(self):
        return [
            {
                "name" : "independent",
                "value" : self.ifield_name,
            },
            {
                "name": "dependent",
                "value" : self.dfield_names[0][1],
                "bind": {
                    "name" : " ",
                    "input": "select",
                    "element" : "#dependent",
                    "options": sum(
                        [
                            [("{1}({2})" if rel == "" else "{0} {1}({2})").format(rel, e.title(), f) for e, f, ft in fields] for rel, fields in self.relationships.items()
                        ],
                        []
                    ),
                    "labels": sum(
                        [
                            [("{1}({2})" if rel == "" else "{0} {1}({2})").format(rel, e.title(), f) for e, f, ft in fields] for rel, fields in self.relationships.items()
                        ],
                        []
                    )
                    
                },
            }
        ] #if len(sum([f for _, f in self.relationships.items()], [])) > 1 else []
                
    @property
    def data(self):
        pass

class DatasetRelationalGraph(BaseVisualization):

    def __init__(self, entities, relationships, properties):
        self._entities = entities
        self._relationships = relationships
        self._properties = properties
        print(entities, relationships, properties)
        super(DatasetRelationalGraph, self).__init__()

    @property
    def signals(self):
        return [
            { "name": "cx", "update": "width / 2" },
            { "name": "cy", "update": "height / 2" },
            { "name": "nodeRadius", "value": 20},
            { "name": "nodeCharge", "value": -30},
            { "name": "linkDistance", "value": 30},
            { "name": "static", "value": False},
        ]

    @property
    def autosize(self):
        return "fit"

    @property
    def data(self):
        return [
            {
                "name": "entities",
                "values" : [{"label" : n, "index" : i} for i, n in enumerate(self._entities)]
            },
            {
                "name": "relationships",
                "values" : self._relationships,
            },
            {
                "name" : "properties",
                "values" : self._properties,
            },
        ]
    
    @property
    def height(self):
      return 300

    @property
    def width(self):
      return 1024 #800
    
    @property
    def padding(self):
        return 5
    
    @property
    def scales(self):
        return [
            {
                "name": "color",
                "type": "ordinal",
                "domain" : {"data" : "entities", "field" : "label"},
                "range": {"scheme": "category20c"}
            }
        ]
    
    @property
    def axes(self):
        return []
    
    @property
    def marks(self):
        return [
            {
                #"name": "nodes",
                "type" : "group",
                "fill" : "blue",
                "zindex": 1,
                "from" : {
                    "facet" : {
                        "data" : "properties",
                        "groupby" : "source",
                        "name" : "nodes"
                    }
                },
                # "on": [
                #     {
                #         "trigger": "fix",
                #         "modify": "node",
                #         "values": "fix === true ? {fx: node.x, fy: node.y} : {fx: fix[0], fy: fix[1]}"
                #     },
                #     {
                #         "trigger": "!fix",
                #         "modify": "node", "values": "{fx: null, fy: null}"
                #     }
                # ],
                "scales" : [
                    {
                        "name" : "propertyScale",
                        "type" : "band",
                        "domain" : {"data" : "nodes", "field" : "label"},
                        "range" : "height",
                    }
                ],
                "marks" : [
                    {
                        "type" : "symbol",
                        "from" : {"data" : "nodes"},

                        "name" : "ent",
                        "encode": {
                            "enter": {
                                "fill": {"value" : "lightblue"}, #{"scale": "color", "field": "source"},
                                "stroke": {"value": "blue"}
                            },
                            "update": {
                                "shape" : {"value" : "square"},
                                "size": {"signal": "25 * nodeRadius * nodeRadius"},
                                "cursor": {"value": "pointer"},
                                "tooltip" : {"signal" : "datum.source"},
                                "zindex" : {"value" : 1},
                            }
                        },
                    },
                    {
                        "type" : "text",
                        "from" : {"data" : "ent"},

                        "encode" : {
                            "enter": {
                                "fill": {"value" : "red"},
                            },
                            "update": {
                                "align" : {"value" : "center"},
                                "dy" : {"value" : -30},
                                "fontSize" : {"value" : 15},
                                "fontStyle" : {"value" : "bold"},
                                "fill": {"value" : "red"},
                                "text" : {"signal" : "parent.source"},
                            }
                            
                        }
                    },
                    {
                        "type" : "text",
                        "from" : {"data" : "ent"},

                        "encode" : {
                            "enter": {
                                "fill": {"value" : "red"},
                            },
                            "update": {
                                "align" : {"value" : "center"},
                                "dy" : {"value" : 30},
                                "fontSize" : {"value" : 10},
                                "fill": {"value" : "red"},
                                "text" : {"field" : "datum.label"},
                            }
                            
                        }
                    }
                            
                ],

                "transform": [
                    {
                        "type": "force",
                        "iterations": 300,
                        #"restart": {"signal": "restart"},
                        "static": {"signal": "static"},
                        "signal": "force",
                        "forces": [
                            #{"force" : "y", "y" : "datum.direction", "strength" : 0.03},
                            {"force": "center", "x": {"signal": "cx"}, "y": {"signal": "cy"}},
                            {"force": "collide", "radius": {"signal": "nodeRadius * 6"}, "iterations" : 10},
                            #{"force": "nbody", "strength": {"signal": "nodeCharge"}},
                            {"force": "link", "links": "relationships", "distance": {"signal": "linkDistance"}}
                        ]
                    }
                ]
            },
            {
                "type": "path",
                "name" : "links",
                "from": {"data": "relationships"},
                "encode": {
                    "update": {
                        "stroke": {"value": "#ccc"},
                        "strokeWidth": {"value": 10},
                        #"tooltip" : {"signal" : "datum.label"},
                    }
                },
                "transform": [
                    {
                        "type": "linkpath",
                        "require": {"signal": "force"},
                        "shape": "line",
                        "sourceX": "datum.source.x",
                        "sourceY": "datum.source.y",
                        "targetX": "datum.target.x",
                        "targetY": "datum.target.y"
                    }
                ]
            },
            {
                "type" : "text",
                "from" : {"data" : "relationships"},
                "encode" : {
                    "update": {
                        "x": {"field" : "source.x"},
                            #"field": "x", "offset": 4},
                        "y": {"field": "source.y"},
                        "align" : {"value" : "center"},
                        #"dy" : {"value" : 30},
                        "fontSize" : {"value" : 10},
                        "fill": {"value" : "red"},
                        "text" : {"value" : "test"}, #{"signal" : "datum.label"},
                    }
                }
            }
            # {
            #     "type": "symbol",
            #     "from": {"data": "relationships"},
            #     "interactive": False,
            #     #"style" : ["triangle"],
            #     "encode": {
            #         "enter": {
            #             #"shape" : {"value" : "triangle"},
            #             "fill": {"scale": "color", "field": "group"},
            #             "stroke": {"value": "red"},
            #             "x" : {"signal" : "datum.target.x"},
            #             "y" : {"signal" : "datum.target.y"},                        
            #         },
            #         "update": {
            #             "shape" : {"value" : "triangle"},
            #             "x" : {"signal" : "datum.target.x"},
            #             "y" : {"signal" : "datum.target.y"},
            #         }
            #     },
            #     "transform": [
            #         {
            #             "type": "linkpath",
            #             "require": {"signal": "force"},
            #             "shape": "line",
            #             "sourceX": "datum.source.x", "sourceY": "datum.source.y",
            #             "targetX": "datum.target.x", "targetY": "datum.target.y"
            #         }
            #     ]
            # },
            # {
            #     "type": "symbol",
            #     "from": {"data": "properties"},
            #     "interactive": False,
            #     #"style" : ["triangle"],
            #     "encode": {
            #         "enter": {
            #             #"shape" : {"value" : "triangle"},
            #             "fill": {"scale": "color", "field": "group"},
            #             "stroke": {"value": "red"},
            #             "x" : {"signal" : "datum.target.x"},
            #             "y" : {"signal" : "datum.target.y"},                        
            #         },
            #         "update": {
            #             "shape" : {"value" : "triangle"},
            #             "x" : {"signal" : "datum.target.x"},
            #             "y" : {"signal" : "datum.target.y"},
            #         }
            #     },
            #     "transform": [
            #         {
            #             "type": "linkpath",
            #             "require": {"signal": "force"},
            #             "shape": "line",
            #             "sourceX": "datum.source.x", "sourceY": "datum.source.y",
            #             "targetX": "datum.target.x", "targetY": "datum.target.y"
            #         }
            #     ]
            # }

        ]
