from pathlib import Path
import os
import os.path
import json
import argparse
import tempfile
import subprocess
import shutil
import shlex
import logging
import torch
import transformers


if __name__== "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--original_model_name", default="bigscience/bloom-560m")
    parser.add_argument("--model_name", default="bloom")
    parser.add_argument("--model_version", default="1.0")
    parser.add_argument("--mode", default="text_generation")
    parser.add_argument("--do_lower_case", default=False, action="store_true")
    parser.add_argument("--save_mode", default="pretrained")
    parser.add_argument("--max_length", default=150, type=int)
    parser.add_argument("--num_labels", default=2, type=int)
    parser.add_argument("--captum_explanation", default=False, action="store_true")
    parser.add_argument("--embedding_name", default="bert")
    parser.add_argument("--faster_transformer", default=False, action="store_true")
    parser.add_argument("--model_parallel", default=False, action="store_true")
    parser.add_argument("--handler")
    parser.add_argument("--output")
    args = parser.parse_args()


    logging.basicConfig(level=logging.INFO)
    logging.info("Transformers version %s", transformers.__version__)

    
    transformers.set_seed(1)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    
    logging.info("Download model and tokenizer '%s'", args.original_model_name)
    config = transformers.AutoConfig.from_pretrained(args.original_model_name, num_labels=args.num_labels, torchscript=(args.save_mode=="torchscript"))
    model = transformers.AutoModelForCausalLM.from_pretrained(args.original_model_name, config=config)
    tokenizer = transformers.AutoTokenizer.from_pretrained(args.original_model_name, do_lower_case=args.do_lower_case)
        
    path = tempfile.mkdtemp()
    try:
        logging.info("Save model and tokenizer model in '%s'", path)
        model.save_pretrained(path)
        tokenizer.save_pretrained(path)
        cmd = [
            "torch-model-archiver",
            "--model-name", args.model_name,
            "--version", args.model_version,
            "--serialized-file", "{}/pytorch_model.bin".format(path),
            "--handler", args.handler,
            "--extra-files", "{0}/config.json,{0}/special_tokens_map.json,{0}/tokenizer_config.json,{0}/tokenizer.json".format(path),
            "--export-path", path,
        ]
        logging.info("invoking '%s'", shlex.join(cmd))
        pid = subprocess.Popen(cmd)
        pid.communicate()
        shutil.move("{}/{}.mar".format(path, args.model_name), args.output)
    except Exception as e:
        raise e
    finally:
        shutil.rmtree(path)
