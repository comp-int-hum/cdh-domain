import sys
import requests
import logging
import os.path


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class User(object):
    def __init__(self, username=None, password=None, headers={"Accept" : "application/json"}):
        self.auth = (username, password) if username else None
        self.headers = headers

    def action(self, action_name, url, data=None, expected=None, files=None):
        resp = getattr(requests, action_name)(url, headers=self.headers, auth=self.auth, data=data, files=files)
        if expected and resp.status_code != expected:
            raise Exception("Expected {} but got {}".format(expected, resp.status_code))
        try:
            return resp.json() if resp.ok == True else {}
        except:
            return {}
    

    def get(self, url, data=None, expected=200):        
        return self.action("get", url, data, expected)

    def post(self, url, data, expected=201, files=None):
        return self.action("post", url=url, data=data, expected=expected, files=files)

    def put(self, url, data, expected=200):
        return self.action("put", url, data, expected)
        
    def patch(self, url, data, expected=200):
        return self.action("patch", url, data, expected)

    def delete(self, url, data=None, expected=200):
        return self.action("delete", url, data, expected)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", dest="host", default="localhost")
    parser.add_argument("--port", dest="port", default=8080, type=int)
    parser.add_argument("--protocol", dest="protocol", default="http")
    parser.add_argument("--primarysource_path", dest="primarysource_path", default="/home/tom/projects/hathitrust/work")
    args = parser.parse_args()

    base_url = "{}://{}:{}/api/".format(args.protocol, args.host, args.port)
    headers = {"Accept" : "application/json"}

    anon = User()
    first = User("user1", "user")
    second = User("user2", "user")
    third = User("user3", "user")

    logging.info("Anonymous model list")
    models = anon.get(base_url)

    for ps in first.get(models["primarysource"])["results"]:
        logger.info("%s", ps)
        logger.info("%s", first.get(ps["schema_url"], expected=200))

    for ml in first.get(models["machinelearningmodel"])["results"]:
        logger.info("%s", ml)
        logger.info("%s", first.get(ml["apply_url"], {"data" : "How many years will it be before "}, expected=200))
    
    for user in first.get(models["user"])["results"]:
        if user["first_name"] == "Bojack":
            first.delete(user["url"])

    first.post(models["user"], {"first_name" : "Bojack", "last_name" : "Fakenamington", "homepage" : "http://www.horsin-around.edu", "title" : "Horse", "photo" : "", "description" : "Happy.", "password" : "herb", "email" : "sugarman@google.com", "username" : "bojack"})
    
    for item in first.get(models["primarysource"])["results"]:
        logger.info("%s", item)
        
    item = first.post(models["query"], {"name" : "test", "sparql" : "test", "primary_source" : item["url"]})
    logger.info("%s", oitem)

    for item in first.get(models["lexicon"])["results"]:
        logger.info("%s", item)        
        first.delete(item["url"])        

    if args.primarysource_path:
        with open(os.path.join(args.primarysource_path, "schema.ttl"), "rb") as schema_fd, open(os.path.join(args.primarysource_path, "data.ttl"), "rb") as data_fd, open(os.path.join(args.primarysource_path, "annotations.ttl"), "rb") as annotations_fd, open(os.path.join(args.primarysource_path, "materials.zip"), "rb") as materials_fd:
            files = [
                ("schema_file", (os.path.join(args.primarysource_path, "schema.ttl"), schema_fd, "text/turtle")),
                ("data_file", (os.path.join(args.primarysource_path, "data.ttl"), data_fd, "text/turtle")),
                ("annotations_file", (os.path.join(args.primarysource_path, "annotations.ttl"), annotations_fd, "text/turtle")),
                ("materials_file", (os.path.join(args.primarysource_path, "materials.zip"), materials_fd, "application/zip")),
            ]
            item = first.post(
                models["primarysource"],
                data={"name" : "test"},
                files=files
            )
        
    logging.info("First user creation")
    item = first.post(models["lexicon"], data={"name" : "test"})

    logging.info("First user retrieval")
    item = first.get(item["url"])

    item["name"] = "new_name"
    logging.info("First user modification")
    first_update = first.put(item["url"], data=item)

    logging.info("Second user retrieval")
    second_view = second.get(item["url"])

    item["name"] = "dsada"

    logging.info("Second user modification")
    second_update = second.put(item["url"], data=item, expected=404)

