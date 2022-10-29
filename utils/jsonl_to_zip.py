import gzip
import rdflib



if __name__ == "__main__":
    import argparse
    from glob import glob
    import os.path
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--riverside_path", dest="riverside_path", default="/home/tom/data/chaucer/gcme")
