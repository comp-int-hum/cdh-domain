from cdh.vega import CdhVisualization
from rdflib import Graph
from rdflib.namespace import SH, RDF, RDFS
import rdflib
import json
import os.path


class PrimarySourceDomainGraph(CdhVisualization):

    def __init__(self, domain, prefix=None): # entities, relationships, properties):
        self.prefix = prefix
        g = Graph()
        g.parse(data=json.dumps(domain), format="application/ld+json")        
        entities, relationships, properties = {}, {}, {}
        
        for shape, _, entity in g.triples((None, SH.targetClass, None)):
            entities[shape] = {
                "entity_label" : os.path.basename(entity)
            }

        for bnode, _, entity in g.triples((None, SH["class"], None)):
            relationships[bnode] = {
                "target_label" : os.path.basename(entity)
            }
            
        for shape, _, bnode in g.triples((None, SH.property, None)):
            if bnode not in relationships:
                properties[bnode] = {
                    "entity_label" : entities[shape]["entity_label"]
                }
            else:
                relationships[bnode]["source_label"] = entities[shape]["entity_label"]

        for bnode, _, path in g.triples((None, SH.path, None)):
            if bnode in properties:
                properties[bnode]["property_label"] = os.path.basename(path)
            else:
                relationships[bnode]["relationship_label"] = os.path.basename(path)
                #return {"entities" : list(entities.values()), "relationships" : list(relationships.values()), "properties" : list(properties.values())}

        self._entities = list(entities.values())
        self._relationships = list(relationships.values())
        self._properties = list(properties.values())
        super(PrimarySourceDomainGraph, self).__init__()

    @property
    def signals(self):
        return [
            {"name": "width", "value": 800},
            {"name": "height", "value": 350},
            { "name": "cx", "update": "width / 2" },
            { "name": "cy", "update": "height / 2" },
            { "name": "nodeRadius", "update": "zoom * 20"},
            { "name": "nodeCharge", "value": -30},
            { "name": "linkDistance", "update": "zoom * 200"},
            { "name": "static", "value": True},
            {
                "description": "State variable for active node fix status.",
                "name": "fix", "value": False,
                "on": [
                    {
                        "events": "*:mouseout[!event.buttons], window:mouseup",
                        "update": "false"
                    },
                    {
                        "events": "*:mouseover",
                        "update": "fix || true"
                    },
                    {
                        "events": "[symbol:mousedown, window:mouseup] > window:mousemove!",
                        "update": "xy()",
                        "force": True
                    }
                ]
            },
            {
                "description": "Graph node most recently interacted with.",
                "name": "node", "value": None,
                "on": [
                    {
                        "events": "symbol:mouseover",
                        "update": "fix === true ? group() : node"
                    }
                ]
            },
            {
                "description": "Flag to restart Force simulation upon data changes.",
                "name": "restart", "value": False,
                "on": [
                    {"events": {"signal": "fix"}, "update": "fix && fix.length"}
                ]
            },
            {
                "name": "zoom",
                "value": 0.75,
                "on": [{
                    "events": {"type": "wheel", "consume": True},
                    "update": "clamp(zoom * pow(1.0005, -event.deltaY * pow(16, event.deltaMode)), 0.1, 1)"
                }]
            },
            # {
            #     "name": "create_entity",
            #     "on": [{
            #         "events": "window:mouseup!",
            #         "update": "warn(xy())",
            #     }]
            # },            
            # {
            #     "name": "create_relationship_or_property",
            #     "on": [
            #         {
            #             "events" : "@entityBackground:mousedown!",
            #             "update" : "warn('entity')",
            #             #"consume" : True
            #         },
            #         {
            #             "events" : "@entityBackground:mouseup!",
            #             "update" : "warn('entity')",
            #             #"consume" : True                        
            #         },                    
            #     ]
            # },
        ]

    #@property
    #def autosize(self):
    #    return {"type" : "fit", "resize" : True}

    @property
    def data(self):
        return [
            {
                "name": "entities",
                "values" : self._entities,
                #"on" : [
                #    {
                #        "trigger": "create_entity",
                #        "insert" : "{entity_label: 'Unnamed'}"
                #    }
                #]
            },
            {
                "name": "relationships",
                "values" : [dict(list(x.items()) + [("source", x["source_label"]), ("target", x["target_label"])]) for x in self._relationships],
            },
            {
                "name" : "properties",
                "values" : self._properties,
                #"on" : [
                #    {
                #        "trigger": "create_entity",
                #        "insert" : "warn({entity_label: 'Unnamed', property_label: 'Some property'})"
                #    }
                #]
                
            }
        ]
    
    #@property
    #def height(self):
    #  return 300

    #@property
    #def width(self):
    #  return None
    
    #@property
    #def padding(self):
    #    return 5
    
    @property
    def scales(self):
        return [
            {
                "name": "color",
                "type": "ordinal",
                "domain" : {"data" : "properties", "field" : "source"},
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
                "type" : "group",
                "name" : "node_group",
                "zindex": 1,
                "on" : [
                    {
                        "trigger": "fix",
                        "modify": "node",
                        "values": "fix === true ? {fx: node.x, fy: node.y} : {fx: fix[0], fy: fix[1]}"
                    },
                    {
                        "trigger": "!fix",
                        "modify": "node", "values": "{fx: null, fy: null}"
                    }
                ],
                "scales": [
                    {
                        "name": "property_scale",
                        "type": "band",
                        "domain": {"data": "entity", "field": "property_label"},
                        "range": {"step": {"signal" : "zoom * 10"}}
                    }
                ],
                "encode": {
                    "enter": {
                        #"fill": {"value" : "lightblue"},
                        "stroke": {"value": "blue"}
                    },
                    "update": {
                        "size": {"signal": "25 * nodeRadius * nodeRadius"},
                    }
                },
                "from" : {
                    "facet" : {
                        "data" : "properties",
                        "groupby" : ["entity_label"],
                        "name" : "entity"
                    }
                },
                "marks" : [
                    {
                        "type" : "symbol",
                        "from" : {"data" : "entity"},
                        "name" : "entityBackground",
                        "encode": {
                            "enter": {
                                "fill": {"value" : "lightblue"},
                                "stroke": {"value": "blue"}
                            },
                            "update": {
                                "shape" : {"value" : "M-1.5,-1H1.5V0.5H-1.5Z"},
                                "size": {"signal": "30 * nodeRadius * nodeRadius"},
                                "cursor": {"value": "pointer"},
                                "zindex" : {"value" : 1},                                
                            }
                        }
                    },
                    {
                        "type" : "text",
                        "from" : {"data" : "entityBackground"},
                        "encode" : {
                            "enter": {
                                "fill": {"value" : "red"},
                                "y":{
                                    "offset": {"signal" : "-zoom * 35"}
                                }
                            },
                            "update": {
                                "align" : {"value" : "center"},
                                "fontSize" : {"signal" : "zoom * 15"},
                                "fontStyle" : {"value" : "bold"},
                                "fill": {"value" : "red"},
                                "text" : {"signal" : "parent.entity_label"},
                                "y":{
                                    "offset": {"signal" : "-zoom * 35"}
                                }
                            }                            
                        }
                    },
                    {
                        "type": "text",
                        "zindex": 3,
                        "from": {"data": "entity"},
                        "encode": {
                            "enter": {
                                "fill": {"value": "black"},
                                "y": {
                                    "scale": "property_scale",
                                    "field": "property_label",
                                }
                            },
                            "update": {
                                "align": {"value": "center"},
                                "fontSize": {"signal": "zoom * 10"},
                                "fontStyle": {"value": "bold"},
                                "fill": {"value": "black"},
                                "text": {"field": "property_label"},
                                "y": {
                                    "scale": "property_scale",
                                    "field": "property_label",
                                    "offset": {"signal" : "-zoom * 20"}
                                }

                            },
                            
                        }
                    }                    
                ],                
                "transform": [
                    {
                        "type": "force",
                        "iterations": 300,
                        "restart": {"signal": "restart"},
                        "static": {"signal": "static"},
                        "signal": "force",
                        "forces": [
                            {"force": "center", "x": {"signal": "cx"}, "y": {"signal": "cy"}},
                            {"force": "collide", "radius": {"signal": "nodeRadius * 2"}}, #, "iterations" : 10},
                            {"force": "nbody", "strength": {"signal": "nodeCharge / 10"}},
                            {"force": "link", "links": "relationships", "distance": {"signal": "linkDistance"}, "id" : "datum.entity_label"}
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
                        "stroke": {"value": "#aaa"},
                        "strokeWidth": {"signal": "zoom * 10"},
                        "tooltip" : {"field" : "relationship_label"}
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
                    },
                    #{"type" : "formula", "as" : "midx", "expr" : "warn(min(datum.sourceX, datum.targetX) + abs(datum.sourceX - datum.targetX))"},
                    #{"type" : "formula", "as" : "midx", "expr" : "warn(datum.source)"},
                    #{"type" : "formula", "as" : "midy", "expr" : "100"},
                ]
            },
            # {
            #     "type": "text",
            #     "zindex": 4,
            #     "from": {"data" : "links"},
            #     "transform" : [
            #         #{"type" : "lookup", "from" : "node_group", "key" : "entity_label", "fields" : ["source_label"], "values" : ["x"], "as" : ["sx"]},
            #         #{"type" : "lookup", "from" : "node_group", "key" : "entity_label", "fields" : ["source_label"], "values" : ["y"], "as" : ["sy"]},
            #         #{"type" : "lookup", "from" : "node_group", "key" : "entity_label", "fields" : ["target_label"], "values" : ["x"], "as" : ["tx"]},
            #         #{"type" : "lookup", "from" : "node_group", "key" : "entity_label", "fields" : ["target_label"], "values" : ["y"], "as" : ["ty"]},
            #         #{"type" : "formula", "expr" : "100", "as" : "sx"},
            #     ],
            #     "encode": {
            #         "enter": {
            #             "fill" : {"value" : "black"},
            #             #"x" : {"signal" : "datum.source.x"},
            #             #"y" : {"signal" : "datum.source.y"},
            #         },
            #         "update": {
            #             "align" : {"value" : "center"},
            #             "fontSize" : {"signal" : "zoom * 10"},
            #             "fontStyle" : {"value" : "bold"},
            #             "fill" : {"value" : "black"},
            #             "text" : {"field" : "relationship_label"},
            #             #"x" : {"field" : "source.x"},
            #             #"y" : {"field" : "source.y"},
            #         }
            #     }
            # }            
        ]



class PrimarySourceDataGraph(CdhVisualization):

    def __init__(self, data, prefix=None):
        self.prefix = prefix
        g = Graph()
        g.parse(data=json.dumps(data), format="application/ld+json")
        entities, relationships, properties = {}, {}, {}
        for subj, pred, obj in g:
            subj = os.path.basename(subj)
            pred = os.path.basename(pred).split("#")[-1]
            obj_ = os.path.basename(obj)
            entities[subj] = entities.get(subj, {})
            properties[subj] = properties.get(subj, {})
            relationships[subj] = relationships.get(subj, {})
            if pred == "contentUrl":                
                entities[subj]["url"] = obj.toPython()
            elif isinstance(obj, rdflib.URIRef):
                # inter-entity
                properties[obj_] = properties.get(obj_, {})
                properties[obj_]["test"] = [""] # HACK
                relationships[subj][obj_] = relationships[subj].get(obj_, []) + [pred]
            elif isinstance(obj, rdflib.Literal):
                properties[subj][pred] = properties[subj].get(pred, []) + [obj_]
        entities = {k : {"entity_label" : k} for k, v in entities.items()}
        self._entities = [{"entity_label" : k} for k, v in entities.items()]
        self._relationships = sum(
            [
                sum(
                    [
                        [{"source_label" : s, "target_label" : o, "relationship_label" : r} for r in rs] for o, rs in os.items()
                    ],
                    []
                ) for s, os in relationships.items()
            ],
            []                    
        )
        self._properties = sum(
            [
                sum(
                    [
                        [{"entity_label" : s, "property_value" : v, "property_label" : p} for v in vs] for p, vs in ps.items()
                    ],
                    []
                ) for s, ps in properties.items()
            ],
            []
        )
        super(PrimarySourceDataGraph, self).__init__()

    @property
    def signals(self):
        return [
            {"name": "width", "value": 800},
            {"name": "height", "value": 350},
            { "name": "cx", "update": "width / 2" },
            { "name": "cy", "update": "height / 2" },
            { "name": "nodeRadius", "update": "zoom * 20"},
            { "name": "nodeCharge", "value": -30},
            { "name": "linkDistance", "update": "zoom * 200"},
            { "name": "static", "value": True},
            {
                "description": "State variable for active node fix status.",
                "name": "fix", "value": False,
                "on": [
                    {
                        "events": "*:mouseout[!event.buttons], window:mouseup",
                        "update": "false"
                    },
                    {
                        "events": "*:mouseover",
                        "update": "fix || true"
                    },
                    {
                        "events": "[symbol:mousedown, window:mouseup] > window:mousemove!",
                        "update": "xy()",
                        "force": True
                    }
                ]
            },
            {
                "description": "Graph node most recently interacted with.",
                "name": "node", "value": None,
                "on": [
                    {
                        "events": "symbol:mouseover",
                        "update": "fix === true ? group() : node"
                    }
                ]
            },
            {
                "description": "Flag to restart Force simulation upon data changes.",
                "name": "restart", "value": False,
                "on": [
                    {"events": {"signal": "fix"}, "update": "fix && fix.length"}
                ]
            },
            {
                "name": "zoom",
                "value": 0.75,
                "on": [{
                    "events": {"type": "wheel", "consume": True},
                    "update": "clamp(zoom * pow(1.0005, -event.deltaY * pow(16, event.deltaMode)), 0.1, 1)"
                }]
            },
            # {
            #     "name": "create_entity",
            #     "on": [{
            #         "events": "window:mouseup!",
            #         "update": "warn(xy())",
            #     }]
            # },            
            # {
            #     "name": "create_relationship_or_property",
            #     "on": [
            #         {
            #             "events" : "@entityBackground:mousedown!",
            #             "update" : "warn('entity')",
            #             #"consume" : True
            #         },
            #         {
            #             "events" : "@entityBackground:mouseup!",
            #             "update" : "warn('entity')",
            #             #"consume" : True                        
            #         },                    
            #     ]
            # },
        ]

    #@property
    #def autosize(self):
    #    return {"type" : "fit", "resize" : True}

    @property
    def data(self):
        return [
            {
                "name": "entities",
                "values" : self._entities,
                #"on" : [
                #    {
                #        "trigger": "create_entity",
                #        "insert" : "{entity_label: 'Unnamed'}"
                #    }
                #]
            },
            {
                "name": "relationships",           
                "values" : [dict(list(x.items()) + [("source", x["source_label"]), ("target", x["target_label"])]) for x in self._relationships],
            },
            {
                "name" : "properties",
                "values" : self._properties,
                #"on" : [
                #    {
                #        "trigger": "create_entity",
                #        "insert" : "warn({entity_label: 'Unnamed', property_label: 'Some property'})"
                #    }
                #]
                
            }
        ]
    
    #@property
    #def height(self):
    #  return 300

    #@property
    #def width(self):
    #  return None
    
    #@property
    #def padding(self):
    #    return 5
    
    @property
    def scales(self):
        return [
            {
                "name": "color",
                "type": "ordinal",
                "domain" : {"data" : "properties", "field" : "source"},
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
                "type" : "group",
                "name" : "node_group",
                "zindex": 1,
                "on" : [
                    {
                        "trigger": "fix",
                        "modify": "node",
                        "values": "fix === true ? {fx: node.x, fy: node.y} : {fx: fix[0], fy: fix[1]}"
                    },
                    {
                        "trigger": "!fix",
                        "modify": "node", "values": "{fx: null, fy: null}"
                    }
                ],
                "scales": [
                    {
                        "name": "property_scale",
                        "type": "band",
                        "domain": {"data": "entity", "field": "property_value"},
                        "range": {"step": {"signal" : "zoom * 10"}}
                    }
                ],
                "encode": {
                    "enter": {
                        #"fill": {"value" : "lightblue"},
                        "stroke": {"value": "blue"}
                    },
                    "update": {
                        "size": {"signal": "25 * nodeRadius * nodeRadius"},
                    }
                },
                "from" : {
                    "facet" : {
                        "data" : "properties",
                        "groupby" : ["entity_label"],
                        "name" : "entity"
                    }
                },
                "marks" : [
                    {
                        "type" : "symbol",
                        "from" : {"data" : "entity"},
                        "name" : "entityBackground",
                        "encode": {
                            "enter": {
                                "fill": {"value" : "lightblue"},
                                "stroke": {"value": "blue"}
                            },
                            "update": {
                                "shape" : {"value" : "M-1.5,-1H1.5V0.5H-1.5Z"},
                                "size": {"signal": "10 * nodeRadius * nodeRadius"},
                                "cursor": {"value": "pointer"},
                                "zindex" : {"value" : 1},                                
                            }
                        }
                    },
                    # {
                    #     "type" : "text",
                    #     "from" : {"data" : "entityBackground"},
                    #     "encode" : {
                    #         "enter": {
                    #             "fill": {"value" : "red"},
                    #             "y":{
                    #                 "offset": {"signal" : "-zoom * 35"}
                    #             }
                    #         },
                    #         "update": {
                    #             "align" : {"value" : "center"},
                    #             "fontSize" : {"signal" : "zoom * 15"},
                    #             "fontStyle" : {"value" : "bold"},
                    #             "fill": {"value" : "red"},
                    #             "text" : {"signal" : "parent.entity_label"},
                    #             "y":{
                    #                 "offset": {"signal" : "-zoom * 35"}
                    #             }
                    #         }                            
                    #     }
                    # },
                    {
                        "type": "text",
                        "zindex": 3,
                        "from": {"data": "entity"},
                        "encode": {
                            "enter": {
                                "fill": {"value": "black"},
                                "y": {
                                    "scale": "property_scale",
                                    "field": "property_value",
                                }
                            },
                            "update": {
                                "align": {"value": "center"},
                                "fontSize": {"signal": "zoom * 10"},
                                "fontStyle": {"value": "bold"},
                                "fill": {"value": "black"},
                                "text": {"field": "property_value"},
                                "y": {
                                    "scale": "property_scale",
                                    "field": "property_label",
                                    "offset": {"signal" : "-zoom * 20"}
                                }

                            },
                            
                        }
                    }                    
                ],                
                "transform": [
                    {
                        "type": "force",
                        "iterations": 300,
                        "restart": {"signal": "restart"},
                        "static": {"signal": "static"},
                        "signal": "force",
                        "forces": [
                            {"force": "center", "x": {"signal": "cx"}, "y": {"signal": "cy"}},
                            {"force": "collide", "radius": {"signal": "nodeRadius * 2"}}, #, "iterations" : 10},
                            {"force": "nbody", "strength": {"signal": "nodeCharge / 10"}},
                            {"force": "link", "links": "relationships", "distance": {"signal": "linkDistance"}, "id" : "datum.entity_label"}
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
                        "stroke": {"value": "#aaa"},
                        "strokeWidth": {"signal": "zoom * 10"},
                        "tooltip" : {"field" : "relationship_label"}
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
                    },
                    #{"type" : "formula", "as" : "midx", "expr" : "warn(min(datum.sourceX, datum.targetX) + abs(datum.sourceX - datum.targetX))"},
                    #{"type" : "formula", "as" : "midx", "expr" : "warn(datum.source)"},
                    #{"type" : "formula", "as" : "midy", "expr" : "100"},
                ]
            },
            # {
            #     "type": "text",
            #     "zindex": 4,
            #     "from": {"data" : "links"},
            #     "transform" : [
            #         #{"type" : "lookup", "from" : "node_group", "key" : "entity_label", "fields" : ["source_label"], "values" : ["x"], "as" : ["sx"]},
            #         #{"type" : "lookup", "from" : "node_group", "key" : "entity_label", "fields" : ["source_label"], "values" : ["y"], "as" : ["sy"]},
            #         #{"type" : "lookup", "from" : "node_group", "key" : "entity_label", "fields" : ["target_label"], "values" : ["x"], "as" : ["tx"]},
            #         #{"type" : "lookup", "from" : "node_group", "key" : "entity_label", "fields" : ["target_label"], "values" : ["y"], "as" : ["ty"]},
            #         #{"type" : "formula", "expr" : "100", "as" : "sx"},
            #     ],
            #     "encode": {
            #         "enter": {
            #             "fill" : {"value" : "black"},
            #             #"x" : {"signal" : "datum.source.x"},
            #             #"y" : {"signal" : "datum.source.y"},
            #         },
            #         "update": {
            #             "align" : {"value" : "center"},
            #             "fontSize" : {"signal" : "zoom * 10"},
            #             "fontStyle" : {"value" : "bold"},
            #             "fill" : {"value" : "black"},
            #             "text" : {"field" : "relationship_label"},
            #             #"x" : {"field" : "source.x"},
            #             #"y" : {"field" : "source.y"},
            #         }
            #     }
            # }            
        ]
    
