from .base_visualization import BaseVisualization
import re

def make_values(model, name="", path=[0]):
    parent_path = path[:-1]
    parent_id = None if parent_path == [] else " ".join([str(x) for x in parent_path])
    this_id = " ".join([str(x) for x in path])
    this_type = "starcoder" if parent_id == None else "module"
    return [
        {
            "id" : this_id,
            "name" : name,
            "type" : this_type,
            "parent" : parent_id,
        }
    ] + sum([make_values(c, n, path + [i]) for i, (n, c) in enumerate(model.items()) if n not in ["dropout"] and not n.startswith("_") and len(path) < 3 and not re.match(r"^\d+$", n)], [])
        
    

        

class DatasetOntologyGraph(BaseVisualization):

    def __init__(self, hierarchy):
        self.hierarchy = []
        #for k, v in hierarchy.items():
        #    print(k, v)
        for node in set(list(hierarchy.keys()) + sum(hierarchy.values(), [])):
            self.hierarchy.append({"id" : node, "name" : node.split("#")[-1]})
            self.hierarchy[-1]["parents"] = hierarchy.get(node, [])
        #for item in spec:
        #    point = {k : v for k, v in item.items() if k != "liwc_features"}
        # #   for k, v in item["liwc_features"].items():
        # #       point["liwc_feature"] = k
        #        point["liwc_value"] = v
        #        self.values.append({k : v for k, v in point.items()})
        super(DatasetOntologyGraph, self).__init__(hierarchy)


    @property
    def signals(self):
        return [
            { "name": "cx", "update": "width / 2" },
            { "name": "cy", "update": "height / 2" },
            { "name": "nodeRadius", "value": 8,
              "bind": {"input": "range", "min": 1, "max": 50, "step": 1} },
            { "name": "nodeCharge", "value": -30,
              "bind": {"input": "range", "min":-100, "max": 10, "step": 1} },
            { "name": "linkDistance", "value": 30,
              "bind": {"input": "range", "min": 5, "max": 100, "step": 1} },
            { "name": "static", "value": True,
              "bind": {"input": "checkbox"} },
            {
                "description": "State variable for active node fix status.",
                "name": "fix", "value": False,
                "on": [
                    {
                        "events": "symbol:mouseout[!event.buttons], window:mouseup",
                        "update": "false"
                    },
                    {
                        "events": "symbol:mouseover",
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
                        "update": "fix === true ? item() : node"
                    }
                ]
            },
            {
                "description": "Flag to restart Force simulation upon data changes.",
                "name": "restart", "value": False,
                "on": [
                    {"events": {"signal": "fix"}, "update": "fix && fix.length"}
                ]
            }
        ]

    @property
    def autosize(self):
        return "fit"

    @property
    def data(self):
        print(self.hierarchy)
        nodes = {n["id"] : {"name" : n["name"], "group" : "x", "index" : i, "parents" : n["parents"]} for i, n in enumerate(self.hierarchy)}
        edges = sum([[{"source" : nodes[o]["index"], "target" : n["index"], "value" : 1} for o in nodes[nid]["parents"]] for nid, n in nodes.items()], [])
        return [
            {
                "name": "node-data",
                "values" : list(nodes.values()),
            },
            {
                "name": "link-data",
                "values" : edges,
            }
        ]
    
    @property
    def height(self):
      return 300

    @property
    def width(self):
      return 1024 #800

    #@property
    #def title(self):
    #    return "Schema"
    
    @property
    def padding(self):
        return 5
    
    @property
    def scales(self):
        return [
            {
                "name": "color",
                "type": "ordinal",
                "domain" : {"data" : "node-data", "field" : "group"},
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
                "name": "nodes",
                "type": "symbol",
                "zindex": 1,
                "from": {"data": "node-data"},
                "on": [
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
                
                "encode": {
                    "enter": {
                        "fill": {"scale": "color", "field": "group"},
                        "stroke": {"value": "white"}
                    },
                    "update": {
                        "size": {"signal": "10 * nodeRadius * nodeRadius"},
                        "cursor": {"value": "pointer"},
                        "tooltip" : {"signal" : "datum.name"},
                    }
                },

                "transform": [
                    {
                        "type": "force",
                        "iterations": 300,
                        "restart": {"signal": "restart"},
                        "static": {"signal": "static"},
                        "signal": "force",
                        "forces": [
                            {"force": "center", "x": {"signal": "cx"}, "y": {"signal": "cy"}},
                            {"force": "collide", "radius": {"signal": "nodeRadius"}},
                            {"force": "nbody", "strength": {"signal": "nodeCharge"}},
                            {"force": "link", "links": "link-data", "distance": {"signal": "linkDistance"}}
                        ]
                    }
                ]
            },
            {
                "type": "path",
                "from": {"data": "link-data"},
                "interactive": False,
                "encode": {
                    "update": {
                        "stroke": {"value": "#ccc"},
                        "strokeWidth": {"value": 3}
                    }
                },
                "transform": [
                    {
                        "type": "linkpath",
                        "require": {"signal": "force"},
                        "shape": "line",
                        "sourceX": "datum.source.x", "sourceY": "datum.source.y",
                        "targetX": "datum.target.x", "targetY": "datum.target.y"
                    }
                ]
            }
        ]

#   "data": [
#     {
#       "name": "node-data",
#       "url": "data/miserables.json",
#       "format": {"type": "json", "property": "nodes"}
#     },
#     {
#       "name": "link-data",
#       "url": "data/miserables.json",
#       "format": {"type": "json", "property": "links"}
#     }
#   ],

#   "scales": [
#     {
#       "name": "color",
#       "type": "ordinal",
#       "domain": {"data": "node-data", "field": "group"},
#       "range": {"scheme": "category20c"}
#     }
#   ],

#   "marks": [
#     {
#       "name": "nodes",
#       "type": "symbol",
#       "zindex": 1,

#       "from": {"data": "node-data"},
#       "on": [
#         {
#           "trigger": "fix",
#           "modify": "node",
#           "values": "fix === true ? {fx: node.x, fy: node.y} : {fx: fix[0], fy: fix[1]}"
#         },
#         {
#           "trigger": "!fix",
#           "modify": "node", "values": "{fx: null, fy: null}"
#         }
#       ],

#       "encode": {
#         "enter": {
#           "fill": {"scale": "color", "field": "group"},
#           "stroke": {"value": "white"}
#         },
#         "update": {
#           "size": {"signal": "2 * nodeRadius * nodeRadius"},
#           "cursor": {"value": "pointer"}
#         }
#       },

#       "transform": [
#         {
#           "type": "force",
#           "iterations": 300,
#           "restart": {"signal": "restart"},
#           "static": {"signal": "static"},
#           "signal": "force",
#           "forces": [
#             {"force": "center", "x": {"signal": "cx"}, "y": {"signal": "cy"}},
#             {"force": "collide", "radius": {"signal": "nodeRadius"}},
#             {"force": "nbody", "strength": {"signal": "nodeCharge"}},
#             {"force": "link", "links": "link-data", "distance": {"signal": "linkDistance"}}
#           ]
#         }
#       ]
#     },
#     {
#       "type": "path",
#       "from": {"data": "link-data"},
#       "interactive": False,
#       "encode": {
#         "update": {
#           "stroke": {"value": "#ccc"},
#           "strokeWidth": {"value": 0.5}
#         }
#       },
#       "transform": [
#         {
#           "type": "linkpath",
#           "require": {"signal": "force"},
#           "shape": "line",
#           "sourceX": "datum.source.x", "sourceY": "datum.source.y",
#           "targetX": "datum.target.x", "targetY": "datum.target.y"
#         }
#       ]
#     }
#   ]
# }



















    
        #     {
        #         "type": "path",
        #         "from": {"data": "relationships"},
        #         "interactive": True,
        #         "encode": {
        #             "update": {
        #                 "stroke": {"value": "black"}, ##ccc"},
        #                 "strokeWidth": {"value": 15},
        #                 "tooltip" : {"signal" : "datum.name"},
        #             }
        #         },
        #         "transform": [
        #             {
        #                 "type": "linkpath",
        #                 #"require": {"signal": "force"},
        #                 "shape": "curve",
        #                 "sourceX": "datum.source.x", "sourceY": "datum.source.y",
        #                 "targetX": "datum.target.x", "targetY": "datum.target.y"
        #             }
        #         ]
        #     },
        #     {
        #         "name" : "nodes",
        #         "type" : "rect",
        #         "from" : {"data" : "entities"},
        #         "encode": {
        #             "enter": {
        #                 "cornerRadius" : {"value" : 4},
        #                 "x" : {"signal" : "datum.x - 100"},
        #                 "y" : {"signal" : "datum.y - 50"},                        
        #                 "fill": {"value" : "lightblue"},
        #                 "stroke": {"value": "white"},
        #                 "width" : {"value" : 200},
        #                 "height" : {"signal" : "35 + 10 * datum.field_count"}, #100},
        #             },
        #         },
        #     },
        #     {
        #         "name" : "entity_labels",
        #         "type" : "text",
        #         "from" : {"data" : "entities"},
        #         "encode": {
        #             "enter": {
        #                 "text" : {"field" : "name"},
        #                 "fontSize" : {"value" : 20},
        #                 "x" : {"field" : "x"},
        #                 "y" : {"signal" : "datum.y - 45"},                        
        #                 "fill": {"value" : "black"},
        #                 "stroke": {"value": "black"},
        #                 "align" : {"value" : "center"},
        #                 "baseline" : {"value" : "top"},
        #             },
        #         },
        #     },
        #     {
        #         "name" : "field_labels",
        #         "type" : "text",
        #         "from" : {"data" : "fields"},
        #         "encode": {
        #             "enter": {
        #                 "text" : {"field" : "field"},
        #                 "fontSize" : {"value" : 10},
        #                 "x" : {"field" : "entity.x"},
        #                 "y" : {"signal" : "datum.entity.y + datum.order * 10 + 20 - 40"},
        #                 "fill": {"value" : "black"},
        #                 "stroke": {"value": "black"},
        #                 "align" : {"value" : "center"},
        #                 "baseline" : {"value" : "top"},
        #             },
        #         },
        #     },
        # ]
