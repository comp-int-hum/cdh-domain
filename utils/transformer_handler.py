from abc import ABC
import json
import logging
import os
import ast
import torch
import transformers
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    AutoModelForQuestionAnswering,
    AutoModelForTokenClassification,
    AutoModelForCausalLM,
)
from transformers import GPT2TokenizerFast

from ts.torch_handler.base_handler import BaseHandler
from captum.attr import LayerIntegratedGradients
from ts.context import Context

logger = logging.getLogger(__name__)
logger.info("Transformers version %s", transformers.__version__)


class GenerativeHandler(BaseHandler, ABC):

    def __init__(self):
        super(GenerativeHandler, self).__init__()
        self.initialized = False

    def initialize(self, ctx):
        """In this initialize function, the BERT model is loaded and
        the Layer Integrated Gradients Algorithm for Captum Explanations
        is initialized here.
        Args:
            ctx (context): It is a JSON Object containing information
            pertaining to the model artefacts parameters.
        """
        self.manifest = ctx.manifest

        if isinstance(ctx.manifest, str) and os.path.exists(ctx.manifest):
            with open(ctx.manifest) as f:
                self.manifest = json.load(f)

        properties = ctx.system_properties
        model_dir = properties.get("model_dir")
        serialized_file = self.manifest["model"]["serializedFile"]
        model_pt_path = os.path.join(model_dir, serialized_file)

        self.device = torch.device(
            "cuda:" + str(properties.get("gpu_id"))
            if torch.cuda.is_available() and properties.get("gpu_id") is not None
            else "cpu"
        )
        self.model = AutoModelForCausalLM.from_pretrained(model_dir)
        self.model.eval()
        logger.info("Transformer model from path %s loaded successfully", model_dir)
        self.tokenizer = AutoTokenizer.from_pretrained(
            "bigscience/bloom-350m",
            do_lower_case=False #self.setup_config["do_lower_case"],
        )

        self.initialized = True

    def preprocess(self, requests):
        """Basic text preprocessing, based on the user's chocie of application mode.
        Args:
            requests (str): The Input data in the form of text is passed on to the preprocess
            function.
        Returns:
            list : The preprocess function returns a list of Tensor for the size of the word tokens.
        """
        input_ids_batch = None
        attention_mask_batch = None
        for idx, data in enumerate(requests):
            input_text = data.get("data")
            if input_text is None:
                input_text = data.get("body")
            if isinstance(input_text, (bytes, bytearray)):
                input_text = input_text.decode("utf-8")
            max_length = 50 #self.setup_config["max_length"]
            logger.info("Received text: '%s'", input_text)
            inputs = self.tokenizer.encode_plus(
                input_text,
                max_length=int(max_length),
                pad_to_max_length=True,
                add_special_tokens=True,
                return_tensors="pt",
            )
            input_ids = inputs["input_ids"].to(self.device)
            attention_mask = inputs["attention_mask"].to(self.device)
            if input_ids.shape is not None:
                if input_ids_batch is None:
                    input_ids_batch = input_ids
                    attention_mask_batch = attention_mask
                else:
                    input_ids_batch = torch.cat((input_ids_batch, input_ids), 0)
                    attention_mask_batch = torch.cat(
                        (attention_mask_batch, attention_mask), 0
                    )
        return (input_ids_batch, attention_mask_batch)

    def inference(self, input_batch):
        """
        """
        input_ids_batch, attention_mask_batch = input_batch
        inferences = []
        outputs = self.model.generate(
            input_ids_batch, max_length=50, do_sample=True, top_p=0.95, top_k=60
        )
        for i, x in enumerate(outputs):
            inferences.append(
                self.tokenizer.decode(outputs[i, -1:], skip_special_tokens=True)
            )
        logger.info("Generated text: '%s'", inferences)
        return inferences

    def handle(self, data, context):
        """Entry point for default handler. It takes the data from the input request and returns
           the predicted outcome for the input.
        Args:
            data (list): The input data that needs to be made a prediction request on.
            context (Context): It is a JSON Object containing information pertaining to
                               the model artefacts parameters.
        Returns:
            list : Returns a list of dictionary with the predicted response.
        """

        # It can be used for pre or post processing if needed as additional request
        # information is available in context
        #start_time = time.time()

        self.context = context
        metrics = self.context.metrics

        is_profiler_enabled = os.environ.get("ENABLE_TORCH_PROFILER", None)
        if is_profiler_enabled:
            if PROFILER_AVAILABLE:
                output, _ = self._infer_with_profiler(data=data)
            else:
                raise RuntimeError(
                    "Profiler is enabled but current version of torch does not support."
                    "Install torch>=1.8.1 to use profiler."
                )
        else:
            if self._is_describe():
                output = [self.describe_handle()]
            else:
                data_preprocess = self.preprocess(data)

                if not self._is_explain():
                    output = self.inference(data_preprocess)
                    output = self.postprocess(output)
                else:
                    output = self.explain_handle(data_preprocess, data)

        #stop_time = time.time()
        #metrics.add_time(
        #    "HandlerTime", round((stop_time - start_time) * 1000, 2), None, "ms"
        #)
        return output

    def postprocess(self, inference_output):
        """Post Process Function converts the predicted response into Torchserve readable format.
        Args:
            inference_output (list): It contains the predicted response of the input text.
        Returns:
            (list): Returns a list of the Predictions and Explanations.
        """
        return inference_output

    def get_insights(self, input_batch, text, target):
        """This function initialize and calls the layer integrated gradient to get word importance
        of the input text if captum explanation has been selected through setup_config
        Args:
            input_batch (int): Batches of tokens IDs of text
            text (str): The Text specified in the input request
            target (int): The Target can be set to any acceptable label under the user's discretion.
        Returns:
            (list): Returns a list of importances and words.
        """
        return []
    
        if self.setup_config["captum_explanation"]:
            embedding_layer = getattr(self.model, self.setup_config["embedding_name"])
            embeddings = embedding_layer.embeddings
            self.lig = LayerIntegratedGradients(captum_sequence_forward, embeddings)
        else:
            logger.warning("Captum Explanation is not chosen and will not be available")

        if isinstance(text, (bytes, bytearray)):
            text = text.decode("utf-8")
        text_target = ast.literal_eval(text)

        if not self.setup_config["mode"] == "question_answering":
            text = text_target["text"]
        self.target = text_target["target"]

        input_ids, ref_input_ids, attention_mask = construct_input_ref(
            text, self.tokenizer, self.device, self.setup_config["mode"]
        )
        all_tokens = get_word_token(input_ids, self.tokenizer)
        response = {}
        response["words"] = all_tokens
        if (
            self.setup_config["mode"] == "sequence_classification"
            or self.setup_config["mode"] == "token_classification"
        ):

            attributions, delta = self.lig.attribute(
                inputs=input_ids,
                baselines=ref_input_ids,
                target=self.target,
                additional_forward_args=(attention_mask, 0, self.model),
                return_convergence_delta=True,
            )

            attributions_sum = summarize_attributions(attributions)
            response["importances"] = attributions_sum.tolist()
            response["delta"] = delta[0].tolist()

        elif self.setup_config["mode"] == "question_answering":
            attributions_start, delta_start = self.lig.attribute(
                inputs=input_ids,
                baselines=ref_input_ids,
                target=self.target,
                additional_forward_args=(attention_mask, 0, self.model),
                return_convergence_delta=True,
            )
            attributions_end, delta_end = self.lig.attribute(
                inputs=input_ids,
                baselines=ref_input_ids,
                target=self.target,
                additional_forward_args=(attention_mask, 1, self.model),
                return_convergence_delta=True,
            )
            attributions_sum_start = summarize_attributions(attributions_start)
            attributions_sum_end = summarize_attributions(attributions_end)
            response["importances_answer_start"] = attributions_sum_start.tolist()
            response["importances_answer_end"] = attributions_sum_end.tolist()
            response["delta_start"] = delta_start[0].tolist()
            response["delta_end"] = delta_end[0].tolist()

        return [response]


def construct_input_ref(text, tokenizer, device, mode):
    """For a given text, this function creates token id, reference id and
    attention mask based on encode which is faster for captum insights
    Args:
        text (str): The text specified in the input request
        tokenizer (AutoTokenizer Class Object): To word tokenize the input text
        device (cpu or gpu): Type of the Environment the server runs on.
    Returns:
        input_id(Tensor): It attributes to the tensor of the input tokenized words
        ref_input_ids(Tensor): Ref Input IDs are used as baseline for the attributions
        attention mask() :  The attention mask is a binary tensor indicating the position
         of the padded indices so that the model does not attend to them.
    """
    if mode == "question_answering":
        question_context = ast.literal_eval(text)
        question = question_context["question"]
        context = question_context["context"]
        text_ids = tokenizer.encode(question, context, add_special_tokens=False)

    text_ids = tokenizer.encode(text, add_special_tokens=False)
    # construct input token ids
    logger.info("text_ids %s", text_ids)
    logger.info("[tokenizer.cls_token_id] %s", [tokenizer.cls_token_id])
    input_ids = [tokenizer.cls_token_id] + text_ids + [tokenizer.sep_token_id]
    logger.info("input_ids %s", input_ids)

    input_ids = torch.tensor([input_ids], device=device)
    # construct reference token ids
    ref_input_ids = (
        [tokenizer.cls_token_id]
        + [tokenizer.pad_token_id] * len(text_ids)
        + [tokenizer.sep_token_id]
    )
    ref_input_ids = torch.tensor([ref_input_ids], device=device)
    # construct attention mask
    attention_mask = torch.ones_like(input_ids)
    return input_ids, ref_input_ids, attention_mask


def captum_sequence_forward(inputs, attention_mask=None, position=0, model=None):
    """This function is used to get the predictions from the model and this function
    can be used independent of the type of the BERT Task.
    Args:
        inputs (list): Input for Predictions
        attention_mask (list, optional): The attention mask is a binary tensor indicating the position
         of the padded indices so that the model does not attend to them, it defaults to None.
        position (int, optional): Position depends on the BERT Task.
        model ([type], optional): Name of the model, it defaults to None.
    Returns:
        list: Prediction Outcome
    """
    model.eval()
    model.zero_grad()
    pred = model(inputs, attention_mask=attention_mask)
    pred = pred[position]
    return pred


def summarize_attributions(attributions):
    """Summarises the attribution across multiple runs
    Args:
        attributions ([list): attributions from the Layer Integrated Gradients
    Returns:
        list : Returns the attributions after normalizing them.
    """
    attributions = attributions.sum(dim=-1).squeeze(0)
    attributions = attributions / torch.norm(attributions)
    return attributions


def get_word_token(input_ids, tokenizer):
    """constructs word tokens from token id using the BERT's
    Auto Tokenizer
    Args:
        input_ids (list): Input IDs from construct_input_ref method
        tokenizer (class): The Auto Tokenizer Pre-Trained model object
    Returns:
        (list): Returns the word tokens
    """
    indices = input_ids[0].detach().tolist()
    tokens = tokenizer.convert_ids_to_tokens(indices)
    # Remove unicode space character from BPE Tokeniser
    tokens = [token.replace("Ġ", "") for token in tokens]
    return tokens


from ts.model_loader import ModelLoader
from ts.metrics.metrics_store import MetricsStore
from ts.service import Service
import uuid
#from .utils.util import list_classes_from_module



if __name__ =="__main__":

    class TsModelLoader(ModelLoader):
        """
        TorchServe 1.0 Model Loader
        """

        def load(
            self,
            model_name,
            model_dir,
            handler,
            gpu_id,
            batch_size,
            envelope=None,
            limit_max_image_pixels=True,
        ):
            """
            Load TorchServe 1.0 model from file.
            :param model_name:
            :param model_dir:
            :param handler:
            :param gpu_id:
            :param batch_size:
            :param envelope:
            :param limit_max_image_pixels:
            :return:
            """
            logging.debug("Loading model - working dir: %s", os.getcwd())
            # TODO: Request ID is not given. UUID is a temp UUID.
            metrics = MetricsStore(uuid.uuid4(), model_name)
            manifest_file = os.path.join(model_dir, "MAR-INF/MANIFEST.json")
            manifest = None
            if os.path.exists(manifest_file):
                with open(manifest_file) as f:
                    manifest = json.load(f)

            # function_name = None
            # try:
            #     module, function_name = self._load_handler_file(handler)
            # except ImportError:
            #     module = self._load_default_handler(handler)

            # if module is None:
            #     raise ValueError(
            #         "Unable to load module {}, make sure it is added to python path".format(
            #             handler
            #         )
            #     )
            # if function_name is None:
            #     function_name = "handle"

            # if hasattr(module, function_name):
            #     entry_point = getattr(module, function_name)
            #     service = Service(
            #         model_name,
            #         model_dir,
            #         manifest,
            #         entry_point,
            #         gpu_id,
            #         batch_size,
            #         limit_max_image_pixels,
            #     )

            envelope_class = None
            if envelope is not None:
                envelope_class = self._load_default_envelope(envelope)

            entry_point, initialize_fn = self._get_class_entry_point()

            if envelope_class is not None:
                envelope_instance = envelope_class(entry_point)
                entry_point = envelope_instance.handle

            service = Service(
                model_name,
                model_dir,
                manifest,
                entry_point,
                gpu_id,
                batch_size,
                limit_max_image_pixels,
            )
            service.context.metrics = metrics
            initialize_fn(service.context)

            return service

        def _load_handler_file(self, handler):
            temp = handler.split(":", 1)
            module_name = temp[0]
            function_name = None if len(temp) == 1 else temp[1]
            if module_name.endswith(".py"):
                module_name = module_name[:-3]
            module_name = module_name.split("/")[-1]
            module = importlib.import_module(module_name)
            return module, function_name

        def _load_default_handler(self, handler):
            module_name = ".{0}".format(handler)
            module = importlib.import_module(module_name, "ts.torch_handler")
            return module

        def _load_default_envelope(self, envelope):
            module_name = ".{0}".format(envelope)
            module = importlib.import_module(
                module_name, "ts.torch_handler.request_envelope"
            )
            envelope_class = list_classes_from_module(module)[0]
            return envelope_class


        def _get_class_entry_point(self):
            # model_class_definitions = list_classes_from_module(module)
            # if len(model_class_definitions) != 1:
            #     raise ValueError(
            #         "Expected only one class in custom service code or a function entry point {}".format(
            #             model_class_definitions
            #         )
            #     )
            model_class = GenerativeHandler
            #model_class = model_class_definitions[0]
            model_service = model_class()

            if not hasattr(model_service, "handle"):
                raise ValueError(
                    "Expect handle method in class {}".format(str(model_class))
                )

            return model_service.handle, model_service.initialize



    ctx = Context(model_name="bloom", model_dir="temp2", manifest="temp2/MAR-INF/MANIFEST.json", batch_size=1, gpu=False, mms_version=1.0)
    handler = GenerativeHandler()    
    handler.initialize(ctx)
    ctx.get_request_header = lambda x, y : False
    initial_prompt = "It was a sunny day and so we went to the"
    prompt = initial_prompt
    #for i in range(40):
    prompt = handler.handle([{"data" : prompt}], ctx)[0]
    #print(initial_prompt)
    #print(prompt)
