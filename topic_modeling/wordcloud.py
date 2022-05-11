from .base_visualization import BaseVisualization


class WordCloud(BaseVisualization):
    def __init__(self, topic):
        self.values = []  # spec was word/prob pairs
        for index, probword in enumerate(topic):
            self.values.append(probword[1])
        #uvals = {v: i for i, v in enumerate(set([x["topic"] for x in spec]))}
        self.num_topics = 1
        #for index, prob in topic:
            #v["topic"] = uvals[v["topic"]]
            #self.values.append(v)
        super(WordCloud, self).__init__(topic)

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
                    }
                },
                # "title" : {"text" : {"signal" : "parent.topic"}},
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
                        ]
                    }
                ]
            },
        ]
