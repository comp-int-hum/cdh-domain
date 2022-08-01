import transformers
from pathlib import Path
import os
import os.path
import json
import torch
from transformers import (AutoModelForSequenceClassification, AutoTokenizer, AutoModelForQuestionAnswering,
 AutoModelForTokenClassification, AutoModelForCausalLM, AutoConfig)
from transformers import set_seed
import argparse
import tempfile
import subprocess
import shutil
import shlex



print('Transformers version',transformers.__version__)
set_seed(1)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

#def transformers_model_dowloader(mode,pretrained_model_name,num_labels,do_lower_case,max_length,torchscript):
def transformers_model_dowloader(args):
    print("Download model and tokenizer", args.original_model_name)

    #loading pre-trained model and tokenizer
    if args.mode == "sequence_classification":
        config = AutoConfig.from_pretrained(args.original_model_name,num_labels=num_labels,torchscript=torchscript)
        model = AutoModelForSequenceClassification.from_pretrained(args.original_model_name, config=config)
        tokenizer = AutoTokenizer.from_pretrained(args.original_model_name,do_lower_case=do_lower_case)
    elif args.mode == "question_answering":
        config = AutoConfig.from_pretrained(args.original_model_name,torchscript=torchscript)
        model = AutoModelForQuestionAnswering.from_pretrained(args.original_model_name,config=config)
        tokenizer = AutoTokenizer.from_pretrained(args.original_model_name,do_lower_case=do_lower_case)
    elif args.mode == "token_classification":
        config= AutoConfig.from_pretrained(args.original_model_name,num_labels=num_labels,torchscript=torchscript)
        model = AutoModelForTokenClassification.from_pretrained(args.original_model_name, config=config)
        tokenizer = AutoTokenizer.from_pretrained(args.original_model_name,do_lower_case=do_lower_case)
    elif args.mode == "text_generation":
        config= AutoConfig.from_pretrained(args.original_model_name, num_labels=args.num_labels, torchscript=args.save_mode == "torchscript")
        model = AutoModelForCausalLM.from_pretrained(args.original_model_name, config=config)
        tokenizer = AutoTokenizer.from_pretrained(args.original_model_name, do_lower_case=args.do_lower_case)
        
    path = tempfile.mkdtemp()
    try:
        print("Save model and tokenizer model in {}".format(path))
        if args.save_mode == "pretrained":
            model.save_pretrained(path)
            tokenizer.save_pretrained(path)
        elif args.save_mode == "torchscript":
            dummy_input = "This is a dummy input for torch jit trace"
            inputs = tokenizer.encode_plus(dummy_input,max_length = int(max_length),pad_to_max_length = True, add_special_tokens = True, return_tensors = 'pt')
            input_ids = inputs["input_ids"].to(device)
            attention_mask = inputs["attention_mask"].to(device)
            model.to(device).eval()
            traced_model = torch.jit.trace(model, (input_ids, attention_mask))
            torch.jit.save(traced_model,os.path.join(NEW_DIR, "traced_model.pt"))

        cmd = [
            "torch-model-archiver",
            "--model-name", args.model_name,
            "--version", args.model_version,
            "--serialized-file", "{}/pytorch_model.bin".format(path),
            "--handler", args.handler,
            "--extra-files", "{}/config.json".format(path),
            "--export-path", path,
        ]
        print("invoking {}".format(shlex.join(cmd)))
        pid = subprocess.Popen(cmd)
        pid.communicate()
        shutil.move("{}/{}.mar".format(path, args.model_name), args.output)
    except Exception as e:
        raise e
    finally:
        shutil.rmtree(path)


if __name__== "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--original_model_name", default="bigscience/bloom-350m")
    parser.add_argument("--model_name", default="bloom-350m")
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

    transformers_model_dowloader(args)
