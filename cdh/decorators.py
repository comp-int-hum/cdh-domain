import logging
from django.core.cache import cache

logger = logging.getLogger("django")


def cdh_cache_method(method):
    def cached_method(*argv, **argd):
        obj = argv[0]
        key = "{}_{}_{}_{}".format(obj._meta.app_label, obj._meta.model_name, obj.id, method.__name__)
        timestamp_key = "TIMESTAMP_{}_{}_{}_{}".format(obj._meta.app_label, obj._meta.model_name, obj.id, method.__name__)
        cache_ts = cache.get(timestamp_key)
        obj_ts = obj.modified_at
        if cache_ts == None or cache_ts < obj_ts:
            logger.info("cache miss for key '{}'".format(key))
            retval = method(*argv, **argd)
            cache.set(timestamp_key, obj_ts, timeout=None)
            cache.set(key, retval, timeout=None)
            return retval
        else:
            logger.info("cache hit for key '{}'".format(key))
            return cache.get(key)
    return cached_method


def cdh_action(**argd):
    def set_properties(method):
        setattr(method, "action_properties", argd)
        return method
    return set_properties


def cdh_cache_function(func):
    raise Exception("cdh_cache_function not implemented yet!")
    def cached_func(*argv, **argd):
        return func(*argv, **argd)
    return cached_func
