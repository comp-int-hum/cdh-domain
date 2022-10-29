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
    parser.add_argument("--file_paths", dest="file_paths", nargs="*", default=[],
                        help="Paths that will be checked (in order) for files referenced in the fixtures")
    parser.add_argument("--username", dest="username", default="user1")
    parser.add_argument("--password", dest="password", default="user")
    parser.add_argument("--auth", dest="auth")
    parser.add_argument("--skip_objects", dest="skip_objects", nargs="*", default=[], help="Names of objects in the fixture files to skip")
    parser.add_argument(
        "--delete",
        dest="delete",
        default=False,
        action="store_true",
        help="Delete all existing objects of a model before creating new ones (except for the authenticated user, if users are to be created)"
    )
    parser.add_argument(
        "--replace",
        dest="replace",
        default=False,
        action="store_true",
        help="If an object of the given name already exists, replace it (default behavior is to leave it as-is)"
    )
    parser.add_argument(dest="fixture_files", nargs="*", help="One or more JSON files (see the cdh/fixtures/ directory for examples)")
    args = parser.parse_args()

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
                existing_items = {o["name"] : o for o in user.get(models[model], follow_next=True)["results"]}
                for obj in objs:
                    if obj["name"] in args.skip_objects:
                        continue
                    robj = {}
                    files = {}
                    if not args.delete and args.replace and obj["name"] in existing_items:
                        user.delete(existing_items[obj["name"]]["url"])
                    elif not args.delete and obj["name"] in existing_items:
                        continue
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
                                for possible_path in reversed(args.file_paths):
                                    possible_fname = os.path.join(possible_path, v["filename"])
                                    if os.path.exists(possible_fname):
                                        files[k] = (
                                            v["filename"],
                                            open(possible_fname, "rb"),
                                            v["content_type"]
                                        )
                                if k not in files:
                                    raise Exception("Could not find file '{}' in any of the directories {}".format(v["filename"], args.file_paths))
                        else:
                            # standard key-value
                            robj[k] = v
                    user.post(models[model], robj, files=files)
                
