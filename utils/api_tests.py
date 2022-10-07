import sys
import requests
import logging
import os.path
import json


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
    

    def get(self, url, data=None, expected=200, follow_next=False):
        if follow_next:
            resp = self.action("get", url, data, expected)
            retval = {k : v for k, v in resp.items()}
            while resp["next"]:
                resp = self.action("get", resp["next"], data, expected)
                for res in resp["results"]:
                    retval["results"].append(res)
            retval["count"] = len(retval["results"])
            retval["next"] = None
            return retval
        else:
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
    parser.add_argument("--file_path", dest="file_path", default="/home/tom/projects/hathitrust/work")
    parser.add_argument("--username", dest="username", default="user1")
    parser.add_argument("--password", dest="password", default="user")
    parser.add_argument("--auth", dest="auth")
    parser.add_argument(
        "--delete",
        dest="delete",
        default=False,
        action="store_true",
        help="Delete all existing objects of a model before creating new ones (except for the authenticated user, if users are to be created)"
    )
    parser.add_argument(dest="fixture_files", nargs="*")
    args = parser.parse_args()

    #openapi_url = "{}://{}:{}/openapi/".format(args.protocol, args.host, args.port)
    base_url = "{}://{}:{}".format(args.protocol, args.host, args.port)
    headers = {"Accept" : "application/json"}

    if args.auth:
        with open(args.auth, "rt") as ifd:
            toks = ifd.read().strip().split(" ")
            username = toks[0]
            password = " ".join(toks[1:])
    elif args.username:
        username = args.username
        if args.password:
            password = args.password
        else:
            raise Exception("Implement getting password interactively")
    user = User(username, password)

    logging.info("Top-level API (model list)")
    models = user.get("{}/api/".format(base_url))
    for model_name, model_url in models.items():
        logging.info("'%s' endpoint is '%s'", model_name, model_url)

    actions = []
    for fixture_file in args.fixture_files:
        logging.info("Processing fixtures in '%s'", fixture_file)
        with open(fixture_file, "rt") as ifd:
            for model, objs in json.loads(ifd.read()).items():
                existing_items = user.get(models[model], follow_next=True)["results"]
                if args.delete:
                    for e in existing_items:
                        user.delete(e["url"])
                for obj in objs:
                    robj = {}
                    files = {}
                    for k, v in obj.items():
                        if isinstance(v, dict):
                            if "model_class" in v:
                                # object-property lookup
                                matches = [
                                    x for x in user.get(models[v["model_class"]], follow_next=True)["results"] if all(
                                        [x[a] == b for a, b in v["match"].items()]
                                    )
                                ]
                                assert len(matches) == 1                            
                                robj[k] = matches[0][v["field"]]
                            elif "filename" in v:
                                # file upload
                                files[k] = (
                                    os.path.basename(v["filename"]),
                                    open(os.path.join(args.file_path, v["filename"]), "rb"),
                                    v["content_type"]
                                )
                        else:
                            # standard key-value
                            robj[k] = v
                    user.post(models[model], robj, files=files)
                
    # for method, subactions in actions:
    #     for subaction in subactions:
    #         for obj in user.get(models[subaction["model"]], follow_next=True)["results"]:
    #             if obj[subaction["filter"][0]] == subaction["filter"][1]:
    #                 objA = obj
    #         for obj in user.get(models[subaction["other_model"]], follow_next=True)["results"]:
    #             if obj[subaction["other_filter"][0]] == subaction["other_filter"][1]:
    #                 objB = obj

    #         subaction_url = objA[subaction["url_field"]]
    #         target_url = objB["url"]
    #         #print(user.post("http://localhost:8080/api/lexicon/38/apply/", {subaction["target_field"] : target_url}, expected=200))
    #         #print(user.post("http://localhost:8080/api/lexicon/38/reapply/", {subaction["target_field"] : target_url}, expected=200))
    #         if method == "POST":                
    #             print(user.post(subaction_url, {subaction["target_field"] : target_url}, expected=200))
    sys.exit()
    
    
    fixtures = json.loads(ifd.read())

    for model, objs in fixtures.items():
        if model == "user":
            continue
        fields = set()
        to_add = {}
        existing = {}
        for obj in objs:
            key = tuple(sorted([(k, v) for k, v in obj.items() if v != None and k not in ["url", "password"] and not k.startswith("@")]))
            for k, _ in key:
                fields.add(k)
            to_add[key] = obj
        for obj in first.get(models[model])["results"]:
            key = tuple(sorted([(k, v) for k, v in obj.items() if k in fields and v != None]))
            existing[key] = obj
        for key, obj in to_add.items():
            if key not in existing:
                files = {k[1:] : open(os.path.join(args.image_path, v), "rb") for k, v in obj.items() if k.startswith("@")}
                non_files = {k : v for k, v in obj.items() if not k.startswith("@")}
                first.post(models[model], non_files, files=files)

    sys.exit()

    
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

