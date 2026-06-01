# vLLM `vllm serve` CLI Reference

Source of truth: `/home/hucong/serve_cli.log` (`vllm serve --help=all` output). This document is a verbatim-preserving, auditable transcription of that log.

## Conventions

- Sections and parameters appear in the same order as the log.
- Each parameter is rendered as one key/value table with exactly five fields: Name, Type, Default, Choices, Description.
- **Description** copies the full help block from the log verbatim; line breaks from the log are rendered as `<br>`. No help block in the log -> `N/A`.
- **Type / Choices** are inferred only from the visible CLI syntax (boolean flag form, enum braces `{...}`, list-literal `['...']`, repeatable `[X ...]`). When a concrete type is not directly inferable from syntax (e.g. a plain `METAVAR`), Type is `N/A`.
- **Default** copies only the explicit `(default: ...)` text from the log. `(default: )` (explicit empty) is shown as `(empty string)`; absence of a default is `N/A`.
- Boolean pairs `--x / --no-x` are split into two separate parameter entries that share the same Type, Default, and Description. Any short alias is kept on the positive entry.
- Source ambiguities are collected in the final **Open Issues** appendix rather than being silently normalized.

---

## Positional Arguments

| Name | Type | Default | Choices | Description |
| --- | --- | --- | --- | --- |
| model_tag | N/A | None | N/A | The model tag to serve (optional if specified in<br>config) |

## Global Options

| Name | Type | Default | Choices | Description |
| --- | --- | --- | --- | --- |
| --aggregate-engine-logging | Boolean flag | False | N/A | Log aggregate rather than per-engine statistics when<br>using data parallelism. |
| --api-server-count | N/A | None | N/A | How many API server processes to run. Defaults to<br>data_parallel_size if not specified. |
| --config | N/A | None | N/A | Read CLI options from a config file. Must be a YAML<br>with the following options: https://docs.vllm.ai/en/la<br>test/configuration/serve_args.html |
| --disable-log-stats | Boolean flag | False | N/A | Disable logging statistics. |
| --enable-log-requests | Boolean flag | False | N/A | Enable logging request information, dependent on log<br>level:<br>- INFO: Request ID, parameters and LoRA request.<br>- DEBUG: Prompt inputs (e.g: text, token IDs). You can<br>set the minimum log level via `VLLM_LOGGING_LEVEL`. |
| --no-enable-log-requests | Boolean flag | False | N/A | Enable logging request information, dependent on log<br>level:<br>- INFO: Request ID, parameters and LoRA request.<br>- DEBUG: Prompt inputs (e.g: text, token IDs). You can<br>set the minimum log level via `VLLM_LOGGING_LEVEL`. |
| --fail-on-environ-validation | Boolean flag | False | N/A | If set, the engine will raise an error if environment<br>validation fails. |
| --no-fail-on-environ-validation | Boolean flag | False | N/A | If set, the engine will raise an error if environment<br>validation fails. |
| --gdn-prefill-backend | Enum | None | flashinfer,triton,cutedsl | Select GDN prefill backend. |
| --grpc | Boolean flag | False | N/A | Launch a gRPC server instead of the HTTP OpenAI-<br>compatible server. Requires: pip install vllm[grpc]. |
| --headless | Boolean flag | False | N/A | Run in headless mode. See multi-node data parallel<br>documentation for more details. |
| --shutdown-timeout | N/A | 0 | N/A | Shutdown timeout in seconds. 0 = abort, >0 = wait. |
| -h, --help | Boolean flag | N/A | N/A | show this help message and exit |

## Frontend

> Section description (from log):

```text
  Arguments for the OpenAI-compatible frontend server.
```

| Name | Type | Default | Choices | Description |
| --- | --- | --- | --- | --- |
| --allow-credentials | Boolean flag | False | N/A | Allow credentials. |
| --no-allow-credentials | Boolean flag | False | N/A | Allow credentials. |
| --allowed-headers | N/A | ['*'] | N/A | Allowed headers. |
| --allowed-methods | N/A | ['*'] | N/A | Allowed methods. |
| --allowed-origins | N/A | ['*'] | N/A | Allowed origins. |
| --api-key | List | None | N/A | If provided, the server will require one of these keys<br>to be presented in the header. |
| --chat-template | N/A | N/A | N/A | N/A |
| --chat-template-content-format | Enum | N/A | auto,openai,string | N/A |
| --data-parallel-supervisor-port | N/A | 9256 | N/A | HTTP port for aggregated health endpoints in multi-<br>port external LB mode. |
| --default-chat-template-kwargs | N/A | None | N/A | Should either be a valid JSON string or JSON keys<br>passed individually. |
| --disable-access-log-for-endpoints | N/A | None | N/A | Comma-separated list of endpoint paths to exclude from<br>uvicorn access logs. This is useful to reduce log<br>noise from high-frequency endpoints like health<br>checks. Example: "/health,/metrics,/ping". When set,<br>access logs for requests to these paths will be<br>suppressed while keeping logs for other endpoints. |
| --disable-fastapi-docs | Boolean flag | False | N/A | Disable FastAPI's OpenAPI schema, Swagger UI, and<br>ReDoc endpoint. |
| --no-disable-fastapi-docs | Boolean flag | False | N/A | Disable FastAPI's OpenAPI schema, Swagger UI, and<br>ReDoc endpoint. |
| --disable-uvicorn-access-log | Boolean flag | False | N/A | Disable uvicorn access log. |
| --no-disable-uvicorn-access-log | Boolean flag | False | N/A | Disable uvicorn access log. |
| --dp-supervisor-probe-failure-threshold | N/A | 3 | N/A | Number of consecutive connection-error retries before<br>a child health probe is declared failed in multi-port<br>external LB mode. |
| --dp-supervisor-probe-interval-s | N/A | 5.0 | N/A | Seconds between aggregated health probes in multi-port<br>external LB mode. |
| --dp-supervisor-probe-timeout-s | N/A | 5.0 | N/A | Seconds to wait between retries when a child health<br>probe fails with a connection error in multi-port<br>external LB mode. |
| --enable-auto-tool-choice | Boolean flag | N/A | N/A | N/A |
| --no-enable-auto-tool-choice | Boolean flag | N/A | N/A | N/A |
| --enable-flash-late-interaction | Boolean flag | True | N/A | If set, run pooling score MaxSim on GPU in the API<br>server process. Can significantly improve late-<br>interaction scoring performance. |
| --no-enable-flash-late-interaction | Boolean flag | True | N/A | If set, run pooling score MaxSim on GPU in the API<br>server process. Can significantly improve late-<br>interaction scoring performance. |
| --enable-force-include-usage | Boolean flag | N/A | N/A | N/A |
| --no-enable-force-include-usage | Boolean flag | N/A | N/A | N/A |
| --enable-log-deltas | Boolean flag | N/A | N/A | N/A |
| --no-enable-log-deltas | Boolean flag | N/A | N/A | N/A |
| --enable-log-outputs | Boolean flag | N/A | N/A | N/A |
| --no-enable-log-outputs | Boolean flag | N/A | N/A | N/A |
| --enable-offline-docs | Boolean flag | False | N/A | Enable offline FastAPI documentation for air-gapped<br>environments. Uses vendored static assets bundled with<br>vLLM. |
| --no-enable-offline-docs | Boolean flag | False | N/A | Enable offline FastAPI documentation for air-gapped<br>environments. Uses vendored static assets bundled with<br>vLLM. |
| --enable-prompt-tokens-details | Boolean flag | N/A | N/A | N/A |
| --no-enable-prompt-tokens-details | Boolean flag | N/A | N/A | N/A |
| --enable-request-id-headers | Boolean flag | False | N/A | If specified, API server will add X-Request-Id header<br>to responses. |
| --no-enable-request-id-headers | Boolean flag | False | N/A | If specified, API server will add X-Request-Id header<br>to responses. |
| --enable-server-load-tracking | Boolean flag | N/A | N/A | N/A |
| --no-enable-server-load-tracking | Boolean flag | N/A | N/A | N/A |
| --enable-ssl-refresh | Boolean flag | False | N/A | Refresh SSL Context when SSL certificate files change |
| --no-enable-ssl-refresh | Boolean flag | False | N/A | Refresh SSL Context when SSL certificate files change |
| --enable-tokenizer-info-endpoint | Boolean flag | N/A | N/A | N/A |
| --no-enable-tokenizer-info-endpoint | Boolean flag | N/A | N/A | N/A |
| --exclude-tools-when-tool-choice-none | Boolean flag | N/A | N/A | N/A |
| --no-exclude-tools-when-tool-choice-none | Boolean flag | N/A | N/A | N/A |
| --fingerprint-mode | Enum | N/A | custom,full,hash,none | N/A |
| --fingerprint-value | N/A | N/A | N/A | N/A |
| --h11-max-header-count | N/A | 256 | N/A | Maximum number of HTTP headers allowed in a request<br>for h11 parser. Helps mitigate header abuse. Default:<br>256. |
| --h11-max-incomplete-event-size | N/A | 4194304 | N/A | Maximum size (bytes) of an incomplete HTTP event<br>(header or body) for h11 parser. Helps mitigate header<br>abuse. Default: 4194304 (4 MB). |
| --host | N/A | None | N/A | Host name. |
| --log-config-file | N/A | N/A | N/A | N/A |
| --log-error-stack | Boolean flag | N/A | N/A | N/A |
| --no-log-error-stack | Boolean flag | N/A | N/A | N/A |
| --lora-modules | List | N/A | N/A | N/A |
| --max-log-len | N/A | N/A | N/A | N/A |
| --middleware | N/A | [] | N/A | Additional ASGI middleware to apply to the app. We<br>accept multiple<br>--middleware arguments. The value should be an import<br>path. If a function is provided, vLLM will add it to<br>the server using `@app.middleware('http')`. If a class<br>is provided, vLLM will add it to the server using<br>`app.add_middleware()`. |
| --port | N/A | 8000 | N/A | Port number. |
| --response-role | N/A | N/A | N/A | N/A |
| --return-tokens-as-token-ids | Boolean flag | N/A | N/A | N/A |
| --no-return-tokens-as-token-ids | Boolean flag | N/A | N/A | N/A |
| --root-path | N/A | None | N/A | FastAPI root_path when app is behind a path based<br>routing proxy. |
| --ssl-ca-certs | N/A | None | N/A | The CA certificates file. |
| --ssl-cert-reqs | N/A | 0 | N/A | Whether client certificate is required (see stdlib ssl<br>module's). |
| --ssl-certfile | N/A | None | N/A | The file path to the SSL cert file. |
| --ssl-ciphers | N/A | None | N/A | SSL cipher suites for HTTPS (TLS 1.2 and below only).<br>Example: 'ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-<br>CHACHA20-POLY1305' |
| --ssl-keyfile | N/A | None | N/A | The file path to the SSL key file. |
| --tokens-only | Boolean flag | N/A | N/A | N/A |
| --no-tokens-only | Boolean flag | N/A | N/A | N/A |
| --tool-call-parser or name registered in --tool-parser-plugin | Enum | N/A | apertus,cohere_command3,cohere_command4,deepseek_v3,deepseek_v31,deepseek_v32,deepseek_v4,ernie45,functiongemma,gemma4,gigachat3,glm45,glm47,granite,granite-20b-fc,granite4,hermes,hunyuan_a13b,hy_v3,internlm,jamba,kimi_k2,lfm2,llama3_json,llama4_json,llama4_pythonic,longcat,mimo,minicpm5,minimax,minimax_m2,mistral,olmo3,openai,phi4_mini_json,poolside_v1,pythonic,qwen3_coder,qwen3_xml,seed_oss,step3,step3p5,xlam | N/A |
| --tool-parser-plugin | N/A | N/A | N/A | N/A |
| --tool-server | N/A | N/A | N/A | N/A |
| --trust-request-chat-template | Boolean flag | N/A | N/A | N/A |
| --no-trust-request-chat-template | Boolean flag | N/A | N/A | N/A |
| --uds | N/A | None | N/A | Unix domain socket path. If set, host and port<br>arguments are ignored. |
| --uvicorn-log-level | Enum | info | critical,debug,error,info,trace,warning | Log level for uvicorn. |

## ModelConfig

> Section description (from log):

```text
  Configuration for the model.
```

| Name | Type | Default | Choices | Description |
| --- | --- | --- | --- | --- |
| --allow-deprecated-quantization | Boolean flag | False | N/A | Whether to allow deprecated quantization methods. |
| --no-allow-deprecated-quantization | Boolean flag | False | N/A | Whether to allow deprecated quantization methods. |
| --allowed-local-media-path | N/A | (empty string) | N/A | Allowing API requests to read local images or videos<br>from directories specified by the server file system.<br>This is a security risk. Should only be enabled in<br>trusted environments. |
| --allowed-media-domains | List | None | N/A | If set, only media URLs that belong to this domain can<br>be used for multi-modal inputs. |
| --code-revision | N/A | None | N/A | The specific revision to use for the model code on the<br>Hugging Face Hub. It can be a branch name, a tag name,<br>or a commit id. If unspecified, will use the default<br>version. |
| --config-format | Enum | auto | 'auto', 'hf', 'mistral' | The format of the model config to load:<br>- "auto" will try to load the config in hf format if<br>available after trying to load in mistral format.<br>- "hf" will load the config in hf format.<br>- "mistral" will load the config in mistral format. |
| --convert | Enum | auto | auto,classify,embed,none | Convert the model using adapters defined in<br>[vllm.model_executor.models.adapters][]. The most<br>common use case is to adapt a text generation model to<br>be used for pooling tasks. |
| --disable-cascade-attn | Boolean flag | True | N/A | Disable cascade attention for V1. While cascade<br>attention does not change the mathematical<br>correctness, disabling it could be useful for<br>preventing potential numerical issues. This defaults<br>to True, so users must opt in to cascade attention by<br>setting this to False. Even when this is set to False,<br>cascade attention will only be used when the heuristic<br>tells that it's beneficial. |
| --no-disable-cascade-attn | Boolean flag | True | N/A | Disable cascade attention for V1. While cascade<br>attention does not change the mathematical<br>correctness, disabling it could be useful for<br>preventing potential numerical issues. This defaults<br>to True, so users must opt in to cascade attention by<br>setting this to False. Even when this is set to False,<br>cascade attention will only be used when the heuristic<br>tells that it's beneficial. |
| --disable-sliding-window | Boolean flag | False | N/A | Whether to disable sliding window. If True, we will<br>disable the sliding window functionality of the model,<br>capping to sliding window size. If the model does not<br>support sliding window, this argument is ignored. |
| --no-disable-sliding-window | Boolean flag | False | N/A | Whether to disable sliding window. If True, we will<br>disable the sliding window functionality of the model,<br>capping to sliding window size. If the model does not<br>support sliding window, this argument is ignored. |
| --dtype | Enum | auto | auto,bfloat16,float,float16,float32,half | Data type for model weights and activations:<br>- "auto" will use FP16 precision for FP32 and FP16<br>models, and BF16 precision for BF16 models.<br>- "half" for FP16. Recommended for AWQ quantization.<br>- "float16" is the same as "half".<br>- "bfloat16" for a balance between precision and<br>range.<br>- "float" is shorthand for FP32 precision.<br>- "float32" for FP32 precision. |
| --enable-cumem-allocator | Boolean flag | False | N/A | Enable the custom cumem allocator to leverage advanced<br>GPU memory allocation features such as multi-node<br>NVLink support.<br>Sleep mode automatically enables this allocator. Only<br>cuda and hip platforms are supported. |
| --no-enable-cumem-allocator | Boolean flag | False | N/A | Enable the custom cumem allocator to leverage advanced<br>GPU memory allocation features such as multi-node<br>NVLink support.<br>Sleep mode automatically enables this allocator. Only<br>cuda and hip platforms are supported. |
| --enable-prompt-embeds | Boolean flag | False | N/A | If `True`, enables passing text embeddings as inputs<br>via the `prompt_embeds` key.<br>WARNING: The vLLM engine may crash if incorrect shape<br>of embeddings is passed. Only enable this flag for<br>trusted users! |
| --no-enable-prompt-embeds | Boolean flag | False | N/A | If `True`, enables passing text embeddings as inputs<br>via the `prompt_embeds` key.<br>WARNING: The vLLM engine may crash if incorrect shape<br>of embeddings is passed. Only enable this flag for<br>trusted users! |
| --enable-return-routed-experts | Boolean flag | False | N/A | Whether to return routed experts. |
| --no-enable-return-routed-experts | Boolean flag | False | N/A | Whether to return routed experts. |
| --enable-sleep-mode | Boolean flag | False | N/A | Enable sleep mode for the engine (only cuda and hip<br>platforms are supported). |
| --no-enable-sleep-mode | Boolean flag | False | N/A | Enable sleep mode for the engine (only cuda and hip<br>platforms are supported). |
| --enforce-eager | Boolean flag | False | N/A | Whether to always use eager-mode PyTorch. If True, we<br>will disable CUDA graph and always execute the model<br>in eager mode. If False, we will use CUDA graph and<br>eager execution in hybrid for maximal performance and<br>flexibility. |
| --no-enforce-eager | Boolean flag | False | N/A | Whether to always use eager-mode PyTorch. If True, we<br>will disable CUDA graph and always execute the model<br>in eager mode. If False, we will use CUDA graph and<br>eager execution in hybrid for maximal performance and<br>flexibility. |
| --generation-config | N/A | auto | N/A | The folder path to the generation config. Defaults to<br>`"auto"`, the generation config will be loaded from<br>model path. If set to `"vllm"`, no generation config<br>is loaded, vLLM defaults will be used. If set to a<br>folder path, the generation config will be loaded from<br>the specified folder path. If `max_new_tokens` is<br>specified in generation config, then it sets a server-<br>wide limit on the number of output tokens for all<br>requests. |
| --hf-config-path | N/A | None | N/A | Name or path of the Hugging Face config to use. If<br>unspecified, model name or path will be used. |
| --hf-overrides | N/A | {} | N/A | If a dictionary, contains arguments to be forwarded to<br>the Hugging Face config. If a callable, it is called<br>to update the HuggingFace config. |
| --hf-token | N/A | None | N/A | The token to use as HTTP bearer authorization for<br>remote files . If `True`, will use the token generated<br>when running `hf auth login` (stored in<br>`~/.cache/huggingface/token`). |
| --io-processor-plugin | N/A | None | N/A | IOProcessor plugin name to load at model startup |
| --logits-processors | List | None | N/A | One or more logits processors' fully-qualified class<br>names or class definitions |
| --logprobs-mode | Enum | raw_logprobs | processed_logits,processed_logprobs,raw_logits,raw_logprobs | Indicates the content returned in the logprobs and<br>prompt_logprobs. Supported mode: 1) raw_logprobs, 2)<br>processed_logprobs, 3) raw_logits, 4)<br>processed_logits. Raw means the values before applying<br>any logit processors, like bad words. Processed means<br>the values after applying all processors, including<br>temperature and top_k/top_p. |
| --max-logprobs | N/A | 20 | N/A | Maximum number of log probabilities to return when<br>`logprobs` is specified in `SamplingParams`. The<br>default value comes the default for the OpenAI Chat<br>Completions API. -1 means no cap, i.e. all<br>(output_length * vocab_size) logprobs are allowed to<br>be returned and it may cause OOM. |
| --max-model-len | N/A | None | N/A | Model context length (prompt and output). If<br>unspecified, will be automatically derived from the<br>model config.<br>When passing via `--max-model-len`, supports<br>k/m/g/K/M/G in human-readable format. Examples:<br>- 1k -> 1000<br>- 1K -> 1024<br>- 25.6k -> 25,600<br>- -1 or 'auto' -> Automatically choose the maximum<br>model length that fits in GPU memory. This will use<br>the model's maximum context length if it fits,<br>otherwise it will find the largest length that can be<br>accommodated.<br>Parse human-readable integers like '1k', '2M', etc.<br>Including decimal values with decimal multipliers.<br>Also accepts -1 or 'auto' as a special value for auto-<br>detection.<br>    Examples:<br>    - '1k' -> 1,000<br>    - '1K' -> 1,024<br>    - '25.6k' -> 25,600<br>    - '-1' or 'auto' -> -1 (special value for auto-<br>detection) |
| --model | N/A | Qwen/Qwen3-0.6B | N/A | Name or path of the Hugging Face model to use. It is<br>also used as the content for `model_name` tag in<br>metrics output when `served_model_name` is not<br>specified. |
| --model-impl | Enum | auto | 'auto', 'terratorch', 'transformers', 'vllm' | Which implementation of the model to use:<br>- "auto" will try to use the vLLM implementation, if<br>it exists, and fall back to the Transformers<br>implementation if no vLLM implementation is available.<br>- "vllm" will use the vLLM model implementation.<br>- "transformers" will use the Transformers model<br>implementation.<br>- "terratorch" will use the TerraTorch model<br>implementation. |
| --override-attention-dtype | N/A | None | N/A | Override dtype for attention |
| --override-generation-config | N/A | {} | N/A | Overrides or sets generation config. e.g.<br>`{"temperature": 0.5}`. If used with `--generation-<br>config auto`, the override parameters will be merged<br>with the default config from the model. If used with<br>`--generation-config vllm`, only the override<br>parameters are used.<br>Should either be a valid JSON string or JSON keys<br>passed individually. |
| --pooler-config | N/A | None | N/A | Pooler config which controls the behaviour of output<br>pooling in pooling models.<br>API docs: https://docs.vllm.ai/en/latest/api/vllm/conf<br>ig/#vllm.config.PoolerConfig<br>Should either be a valid JSON string or JSON keys<br>passed individually. |
| --quantization | N/A | None | N/A | Method used to quantize the weights. If `None`, we<br>first check the `quantization_config` attribute in the<br>model config file. If that is `None`, we assume the<br>model weights are not quantized and use `dtype` to<br>determine the data type of the weights. |
| --quantization-config | N/A | None | N/A | User-facing quantization configuration. Carries per-<br>layer-kind specs (linear, moe) and ignore patterns;<br>see :class:`QuantizationConfigArgs`. Auto-populated<br>from the matching online shorthand when `quantization`<br>is one of the values in<br>`ONLINE_QUANT_SHORTHAND_NAMES`.<br>API docs: https://docs.vllm.ai/en/latest/api/vllm/conf<br>ig/#vllm.config.QuantizationConfigArgs<br>Should either be a valid JSON string or JSON keys<br>passed individually. |
| --renderer-num-workers | N/A | 1 | N/A | Number of worker threads in the renderer thread pool.<br>The pool is consumed by the async renderer path (e.g.<br>the OpenAI-compatible API server started by `vllm<br>serve`) to parallelize tokenization, chat template<br>rendering, and multimodal preprocessing across<br>concurrent requests.<br>The offline `LLM` entrypoint uses the synchronous<br>renderer path and processes prompts (including<br>multimodal preprocessing) serially, so this setting<br>has no effect there. |
| --revision | N/A | None | N/A | The specific model version to use. It can be a branch<br>name, a tag name, or a commit id. If unspecified, will<br>use the default version. |
| --runner | Enum | auto | auto,draft,generate,pooling | The type of model runner to use. Each vLLM instance<br>only supports one model runner, even if the same model<br>can be used for multiple types. |
| --seed | N/A | 0 | N/A | Random seed for reproducibility.<br>We must set the global seed because otherwise,<br>different tensor parallel workers would sample<br>different tokens, leading to inconsistent results. |
| --served-model-name | List | None | N/A | The model name(s) used in the API. If multiple names<br>are provided, the server will respond to any of the<br>provided names. The model name in the model field of a<br>response will be the first name in this list. If not<br>specified, the model name will be the same as the<br>`--model` argument. Noted that this name(s) will also<br>be used in `model_name` tag content of prometheus<br>metrics, if multiple names provided, metrics tag will<br>take the first one. |
| --skip-tokenizer-init | Boolean flag | False | N/A | Skip initialization of tokenizer and detokenizer.<br>Expects valid `prompt_token_ids` and `None` for prompt<br>from the input. The generated output will contain<br>token ids. |
| --no-skip-tokenizer-init | Boolean flag | False | N/A | Skip initialization of tokenizer and detokenizer.<br>Expects valid `prompt_token_ids` and `None` for prompt<br>from the input. The generated output will contain<br>token ids. |
| --tokenizer | N/A | None | N/A | Name or path of the Hugging Face tokenizer to use. If<br>unspecified, model name or path will be used. |
| --tokenizer-mode | Enum | auto | 'auto', 'deepseek_v32', 'deepseek_v4', 'hf', 'mistral', 'slow' | Tokenizer mode:<br>- "auto" will use the tokenizer from `mistral_common`<br>for Mistral models if available, otherwise it will use<br>the "hf" tokenizer.<br>- "hf" will use the fast tokenizer if available.<br>- "slow" will always use the slow tokenizer.<br>- "mistral" will always use the tokenizer from<br>`mistral_common`.<br>- "deepseek_v32" will always use the tokenizer from<br>`deepseek_v32`.<br>- "deepseek_v4" will always use the tokenizer from<br>`deepseek_v4`.<br>- "qwen_vl" will always use the tokenizer from<br>`qwen_vl`.<br>- Other custom values can be supported via plugins.<br>To swap the Rust BPE backend that powers HF fast<br>tokenizers for the<br>[fastokens](https://github.com/crusoecloud/fastokens)<br>implementation, set `VLLM_USE_FASTOKENS=1` instead —<br>that override applies to any mode that loads an HF<br>fast tokenizer (`hf`, `deepseek_v32`, `deepseek_v4`,<br>`qwen_vl`, …). |
| --tokenizer-revision | N/A | None | N/A | The specific revision to use for the tokenizer on the<br>Hugging Face Hub. It can be a branch name, a tag name,<br>or a commit id. If unspecified, will use the default<br>version. |
| --trust-remote-code | Boolean flag | False | N/A | Trust remote code (e.g., from HuggingFace) when<br>downloading the model and tokenizer. |
| --no-trust-remote-code | Boolean flag | False | N/A | Trust remote code (e.g., from HuggingFace) when<br>downloading the model and tokenizer. |
| --use-fp64-gumbel | Boolean flag | False | N/A | Whether to use FP64 (instead of FP32) for the Gumbel<br>noise used by the sampler. FP64 reduces the chance of<br>ties in Gumbel-max sampling at the cost of<br>significantly lower kernel throughput on most GPUs. |
| --no-use-fp64-gumbel | Boolean flag | False | N/A | Whether to use FP64 (instead of FP32) for the Gumbel<br>noise used by the sampler. FP64 reduces the chance of<br>ties in Gumbel-max sampling at the cost of<br>significantly lower kernel throughput on most GPUs. |

**Nested fields (`PoolerConfig`):**

| Sub-field | Type | Default |
| --- | --- | --- |
| `task` | `PoolingTask \| None` | `None` |
| `pooling_type` | `SequencePoolingType \| TokenPoolingType \| None` | `None` |
| `seq_pooling_type` | `SequencePoolingType \| None` | `None` |
| `tok_pooling_type` | `TokenPoolingType \| None` | `None` |
| `use_activation` | `bool \| None` | `None` |
| `dimensions` | `int \| None` | `None` |
| `enable_chunked_processing` | `bool` | `False` |
| `max_embed_len` | `int \| None` | `None` |
| `logit_mean` | `float \| None` | `None` |
| `logit_sigma` | `float \| None` | `None` |
| `step_tag_id` | `int \| None` | `None` |
| `returned_token_ids` | `list[int] \| None` | `None` |

**Nested fields (`QuantizationConfigArgs`):**

| Sub-field | Type | Default |
| --- | --- | --- |
| `linear` | `QuantSpec \| None` | `None` |
| `moe` | `QuantSpec \| None` | `None` |
| `ignore` | `list[str]` | `[]` |

## LoadConfig

> Section description (from log):

```text
  Configuration for loading the model weights.
```

| Name | Type | Default | Choices | Description |
| --- | --- | --- | --- | --- |
| --download-dir | N/A | None | N/A | Directory to download and load the weights, default to<br>the default cache directory of Hugging Face. |
| --ignore-patterns | List | ['original/**/*'] | N/A | The list of patterns to ignore when loading the model.<br>Default to "original/**/*" to avoid repeated loading<br>of llama's checkpoints. |
| --load-format | N/A | auto | N/A | The format of the model weights to load.<br>- "auto" will try to load the weights in the<br>safetensors format and fall back to the pytorch bin<br>format if safetensors format is not available.<br>- "pt" will load the weights in the pytorch bin<br>format.<br>- "safetensors" will load the weights in the<br>safetensors format.<br>- "instanttensor" will load the Safetensors weights on<br>CUDA devices using InstantTensor, which enables<br>distributed loading with pipelined prefetching and<br>fast direct I/O.<br>- "npcache" will load the weights in pytorch format<br>and store a numpy cache to speed up the loading.<br>- "dummy" will initialize the weights with random<br>values, which is mainly for profiling.<br>- "tensorizer" will use CoreWeave's tensorizer library<br>for fast weight loading. See the Tensorize vLLM Model<br>script in the Examples section for more information.<br>- "runai_streamer" will load the Safetensors weights<br>using Run:ai Model Streamer.<br>- "runai_streamer_sharded" will load weights from pre-<br>sharded checkpoint files using Run:ai Model Streamer.<br>- "bitsandbytes" will load the weights using<br>bitsandbytes quantization.<br>- "sharded_state" will load weights from pre-sharded<br>checkpoint files, supporting efficient loading of<br>tensor-parallel models.<br>- "gguf" will load weights from GGUF format files<br>(details specified in https://github.com/ggml-<br>org/ggml/blob/master/docs/gguf.md).<br>- "mistral" will load weights from consolidated<br>safetensors files used by Mistral models.<br>- "modelexpress" will load weights using ModelExpress.<br>- Other custom values can be supported via plugins. |
| --model-loader-extra-config | N/A | {} | N/A | Extra config for model loader. This will be passed to<br>the model loader corresponding to the chosen<br>load_format. |
| --pt-load-map-location | N/A | cpu | N/A | The map location for loading pytorch checkpoint, to<br>support loading checkpoints can only be loaded on<br>certain devices like "cuda", this is equivalent to<br>`{"": "cuda"}`. Another supported format is mapping<br>from different devices like from GPU 1 to GPU 0:<br>`{"cuda:1": "cuda:0"}`. Note that when passed from<br>command line, the strings in dictionary need to be<br>double quoted for json parsing. For more details, see<br>the original doc for `map_location` parameter in<br>[`torch.load`][] parameter. |
| --safetensors-load-strategy | N/A | None | N/A | Specifies the loading strategy for safetensors<br>weights.<br>- None (default): Uses memory-mapped (lazy) loading.<br>When an NFS filesystem is detected and the total<br>checkpoint size fits within 90%% of available RAM,<br>prefetching is enabled automatically.<br>- "lazy": Weights are memory-mapped from the file.<br>This enables on-demand loading and is highly efficient<br>for models on local storage. Unlike the default<br>(None), auto-prefetch on NFS is not performed.<br>- "eager": The entire file is read into CPU memory<br>upfront before loading. This is recommended for models<br>on network filesystems (e.g., Lustre, NFS) as it<br>avoids inefficient random reads, significantly<br>speeding up model initialization. However, it uses<br>more CPU RAM.<br>- "prefetch": Checkpoint files are read into the OS<br>page cache before workers load them, speeding up the<br>model loading phase. Useful on network or high-latency<br>storage.<br>- "torchao": Weights are loaded in upfront and then<br>reconstructed into torchao tensor subclasses. This is<br>used when the checkpoint was quantized using torchao<br>and saved using safetensors. Needs `torchao >=<br>0.14.0`. |
| --safetensors-prefetch-block-size | N/A | 16777216 | N/A | Read size in bytes for each safetensors checkpoint<br>file prefetch.<br>Parse human-readable integers like '1k', '2M', etc.<br>Including decimal values with decimal multipliers.<br>    Examples:<br>    - '1k' -> 1,000<br>    - '1K' -> 1,024<br>    - '25.6k' -> 25,600 |
| --safetensors-prefetch-num-threads | N/A | 8 | N/A | Number of worker threads used to prefetch safetensors<br>checkpoint files into the OS page cache when<br>safetensors prefetching is enabled. |
| --use-tqdm-on-load | Boolean flag | True | N/A | Whether to enable tqdm for showing progress bar when<br>loading model weights. |
| --no-use-tqdm-on-load | Boolean flag | True | N/A | Whether to enable tqdm for showing progress bar when<br>loading model weights. |

## AttentionConfig

> Section description (from log):

```text
  Configuration for attention mechanisms in vLLM.
```

| Name | Type | Default | Choices | Description |
| --- | --- | --- | --- | --- |
| --attention-backend | N/A | None | N/A | Attention backend to use. Use "auto" or None for<br>automatic selection. |

**Nested fields (`AttentionConfig`):**

| Sub-field | Type | Default |
| --- | --- | --- |
| `backend` | `AttentionBackendEnum \| None` | `None` |
| `flash_attn_version` | `Literal[2, 3, 4] \| None` | `None` |
| `use_prefill_decode_attention` | `bool` | `False` |
| `flash_attn_max_num_splits_for_cuda_graph` | `int` | `32` |
| `tq_max_kv_splits_for_cuda_graph` | `int` | `32` |
| `use_trtllm_attention` | `bool \| None` | `None` |
| `disable_flashinfer_q_quantization` | `bool` | `False` |
| `mla_prefill_backend` | `MLAPrefillBackendEnum \| None` | `None` |
| `use_prefill_query_quantization` | `bool` | `False` |
| `use_fp4_indexer_cache` | `bool` | `False` |
| `use_non_causal` | `bool` | `False` |
| `flex_attn_block_m` | `int \| None` | `None` |
| `flex_attn_block_n` | `int \| None` | `None` |
| `flex_attn_q_block_size` | `int \| None` | `None` |
| `flex_attn_kv_block_size` | `int \| None` | `None` |

## MambaConfig

> Section description (from log):

```text
  Configuration for Mamba SSM backends.
```

| Name | Type | Default | Choices | Description |
| --- | --- | --- | --- | --- |
| --enable-mamba-cache-stochastic-rounding | Boolean flag | False | N/A | Enable stochastic rounding when writing SSM state to<br>fp16 cache. Uses random bits to unbias the rounding<br>error, which can improve numerical stability for long<br>sequences. |
| --no-enable-mamba-cache-stochastic-rounding | Boolean flag | False | N/A | Enable stochastic rounding when writing SSM state to<br>fp16 cache. Uses random bits to unbias the rounding<br>error, which can improve numerical stability for long<br>sequences. |
| --mamba-backend | N/A | MambaBackendEnum.TRITON | N/A | Mamba SSU backend to use. |
| --mamba-cache-philox-rounds | N/A | 0 | N/A | Number of Philox PRNG rounds for stochastic rounding<br>random number generation. 0 uses the Triton default.<br>Higher values improve randomness quality at the cost<br>of compute. |

## StructuredOutputsConfig

> Section description (from log):

```text
  Dataclass which contains structured outputs config for the engine.
```

| Name | Type | Default | Choices | Description |
| --- | --- | --- | --- | --- |
| --reasoning-parser | N/A | (empty string) | N/A | Select the reasoning parser depending on the model<br>that you're using. This is used to parse the reasoning<br>content into OpenAI API format. |
| --reasoning-parser-plugin | N/A | (empty string) | N/A | Path to a dynamically reasoning parser plugin that can<br>be dynamically loaded and registered. |

## ParallelConfig

> Section description (from log):

```text
  Configuration for the distributed execution.
```

| Name | Type | Default | Choices | Description |
| --- | --- | --- | --- | --- |
| --all2all-backend | Enum | allgather_reducescatter | allgather_reducescatter,deepep_high_throughput,deepep_low_latency,flashinfer_all2allv,flashinfer_nvlink_one_sided,flashinfer_nvlink_two_sided,mori_high_throughput,mori_low_latency,naive,nixl_ep,pplx | All2All backend for MoE expert parallel communication.<br>Available options:<br>- "allgather_reducescatter": All2all based on<br>allgather and reducescatter<br>- "deepep_high_throughput": Use deepep high-throughput<br>kernels<br>- "deepep_low_latency": Use deepep low-latency kernels<br>- "mori_high_throughput": MoRI EP with InterNodeV1 for<br>multi-node<br>- "mori_low_latency": MoRI EP with InterNodeV1LL for<br>multi-node<br>- "nixl_ep": Use nixl-ep kernels<br>- "flashinfer_nvlink_two_sided": Use flashinfer two-<br>sided kernels for mnnvl<br>- "flashinfer_nvlink_one_sided": Use flashinfer high-<br>throughput a2a kernels |
| --cp-kv-cache-interleave-size | N/A | 1 | N/A | Interleave size of kv_cache storage while using DCP or<br>PCP. For `total_cp_rank = pcp_rank * dcp_world_size +<br>dcp_rank`, and `total_cp_world_size = pcp_world_size *<br>dcp_world_size`. store interleave_size tokens on<br>total_cp_rank i, then store next interleave_size<br>tokens on total_cp_rank i+1. Interleave_size=1: token-<br>level alignment, where token `i` is stored on<br>total_cp_rank `i % total_cp_world_size`.<br>Interleave_size=block_size: block-level alignment,<br>where tokens are first populated to the preceding<br>ranks. Tokens are then stored in (rank i+1, block j)<br>only after (rank i, block j) is fully occupied.<br>Block_size should be greater than or equal to<br>cp_kv_cache_interleave_size. Block_size should be<br>divisible by cp_kv_cache_interleave_size. |
| --cpu-distributed-timeout-seconds | N/A | None | N/A | Timeout (in seconds) for cpu communication groups. If<br>None, PyTorch's default timeout is used (1800s for<br>gloo). |
| --data-parallel-address | N/A | None | N/A | Address of data parallel cluster head-node. |
| --data-parallel-backend | N/A | mp | N/A | Backend for data parallel, either "mp" or "ray". |
| --data-parallel-external-lb | Boolean flag | False | N/A | Whether to use "external" DP LB mode. Applies only to<br>online serving and when data_parallel_size > 0. This<br>is useful for a "one-pod-per-rank" wide-EP setup in<br>Kubernetes. Supported only for MoE deployments; non-<br>MoE models should use independent vLLM instances<br>without --data-parallel-* arguments. Set implicitly<br>when --data-parallel-rank is provided explicitly to<br>vllm serve. |
| --no-data-parallel-external-lb | Boolean flag | False | N/A | Whether to use "external" DP LB mode. Applies only to<br>online serving and when data_parallel_size > 0. This<br>is useful for a "one-pod-per-rank" wide-EP setup in<br>Kubernetes. Supported only for MoE deployments; non-<br>MoE models should use independent vLLM instances<br>without --data-parallel-* arguments. Set implicitly<br>when --data-parallel-rank is provided explicitly to<br>vllm serve. |
| --data-parallel-hybrid-lb | Boolean flag | False | N/A | Whether to use "hybrid" DP LB mode. Applies only to<br>online serving and when data_parallel_size > 0.<br>Enables running an AsyncLLM and API server on a "per-<br>node" basis where vLLM load balances between local<br>data parallel ranks, but an external LB balances<br>between vLLM nodes/replicas. Set explicitly in<br>conjunction with<br>--data-parallel-start-rank. |
| --no-data-parallel-hybrid-lb | Boolean flag | False | N/A | Whether to use "hybrid" DP LB mode. Applies only to<br>online serving and when data_parallel_size > 0.<br>Enables running an AsyncLLM and API server on a "per-<br>node" basis where vLLM load balances between local<br>data parallel ranks, but an external LB balances<br>between vLLM nodes/replicas. Set explicitly in<br>conjunction with<br>--data-parallel-start-rank. |
| --data-parallel-multi-port-external-lb | Boolean flag | False | N/A | Run a node-local supervisor that launches one<br>external-LB API server per local data parallel rank<br>and exposes aggregated health on a supervisor port. |
| --data-parallel-rank | N/A | None | N/A | Data parallel rank of this instance. When set, enables<br>external load balancer mode for MoE data-parallel<br>deployments. Unsupported for non-MoE models; launch<br>independent vLLM instances instead. |
| --data-parallel-rpc-port | N/A | None | N/A | Port for data parallel RPC communication. |
| --data-parallel-size | N/A | 1 | N/A | Number of data parallel groups. MoE layers will be<br>sharded according to the product of the tensor<br>parallel size and data parallel size. |
| --data-parallel-size-local | N/A | None | N/A | Number of data parallel replicas to run on this node. |
| --data-parallel-start-rank | N/A | None | N/A | Starting data parallel rank for secondary nodes. |
| --dbo-decode-token-threshold | N/A | 32 | N/A | The threshold for dual batch overlap for batches only<br>containing decodes. If the number of tokens in the<br>request is greater than this threshold, microbatching<br>will be used. Otherwise, the request will be processed<br>in a single batch. |
| --dbo-prefill-token-threshold | N/A | 512 | N/A | The threshold for dual batch overlap for batches that<br>contain one or more prefills. If the number of tokens<br>in the request is greater than this threshold,<br>microbatching will be used. Otherwise, the request<br>will be processed in a single batch. |
| --dcp-comm-backend | Enum | ag_rs | a2a,ag_rs | Communication backend for Decode Context Parallel<br>(DCP).<br>- "ag_rs": AllGather + ReduceScatter (default,<br>existing behavior)<br>- "a2a": All-to-All exchange of partial outputs + LSE,<br>then combine with Triton kernel. Reduces NCCL calls<br>from 3 to 2 per layer for MLA models. |
| --dcp-kv-cache-interleave-size | N/A | 1 | N/A | Interleave size of kv_cache storage while using DCP.<br>dcp_kv_cache_interleave_size has been replaced by<br>cp_kv_cache_interleave_size, and will be deprecated<br>when PCP is fully supported. |
| --decode-context-parallel-size | N/A | 1 | N/A | Number of decode context parallel groups, because the<br>world size does not change by dcp, it simply reuse the<br>GPUs of TP group, and tp_size needs to be divisible by<br>dcp_size. |
| --disable-custom-all-reduce | Boolean flag | False | N/A | Disable the custom all-reduce kernel and fall back to<br>NCCL. |
| --no-disable-custom-all-reduce | Boolean flag | False | N/A | Disable the custom all-reduce kernel and fall back to<br>NCCL. |
| --disable-nccl-for-dp-synchronization | Boolean flag | None | N/A | Forces the dp synchronization logic in<br>vllm/v1/worker/dp_utils.py  to use Gloo instead of<br>NCCL for its all reduce.<br>Defaults to True when async scheduling is enabled,<br>False otherwise. |
| --no-disable-nccl-for-dp-synchronization | Boolean flag | None | N/A | Forces the dp synchronization logic in<br>vllm/v1/worker/dp_utils.py  to use Gloo instead of<br>NCCL for its all reduce.<br>Defaults to True when async scheduling is enabled,<br>False otherwise. |
| --distributed-executor-backend | Enum | None | 'external_launcher', 'mp', 'ray', 'uni' | Backend to use for distributed model workers, either<br>"ray" or "mp" (multiprocessing). If the product of<br>pipeline_parallel_size and tensor_parallel_size is<br>less than or equal to the number of GPUs available,<br>"mp" will be used to keep processing on a single host.<br>Otherwise, an error will be raised. To use "mp" you<br>must also set nnodes, and to use "ray" you must<br>manually set distributed_executor_backend to "ray".<br>Note:<br>[TPU](https://docs.vllm.ai/projects/tpu/en/latest/)<br>platform only supports Ray for distributed inference. |
| --distributed-timeout-seconds | N/A | None | N/A | Timeout in seconds for distributed operations (e.g.,<br>init_process_group). If set, this value is passed to<br>torch.distributed.init_process_group as the timeout<br>parameter. If None, PyTorch's default timeout is used<br>(600s for NCCL). Increase this for multi-node setups<br>where model downloads may be slow. |
| --enable-dbo | Boolean flag | False | N/A | Enable dual batch overlap for the model executor. |
| --no-enable-dbo | Boolean flag | False | N/A | Enable dual batch overlap for the model executor. |
| --enable-elastic-ep | Boolean flag | False | N/A | Enable elastic expert parallelism with stateless NCCL<br>groups for DP/EP. |
| --no-enable-elastic-ep | Boolean flag | False | N/A | Enable elastic expert parallelism with stateless NCCL<br>groups for DP/EP. |
| --enable-ep-weight-filter | Boolean flag | False | N/A | Skip non-local expert weights during model loading<br>when expert parallelism is active.  Each rank only<br>reads its own expert shard from disk, which can<br>drastically reduce storage I/O for MoE models with<br>per-expert weight tensors (e.g. DeepSeek, Mixtral,<br>Kimi-K2.5).  Has no effect on 3D fused-expert<br>checkpoints (e.g. GPT-OSS) or non-MoE models. |
| --no-enable-ep-weight-filter | Boolean flag | False | N/A | Skip non-local expert weights during model loading<br>when expert parallelism is active.  Each rank only<br>reads its own expert shard from disk, which can<br>drastically reduce storage I/O for MoE models with<br>per-expert weight tensors (e.g. DeepSeek, Mixtral,<br>Kimi-K2.5).  Has no effect on 3D fused-expert<br>checkpoints (e.g. GPT-OSS) or non-MoE models. |
| --enable-eplb | Boolean flag | False | N/A | Enable expert parallelism load balancing for MoE<br>layers. |
| --no-enable-eplb | Boolean flag | False | N/A | Enable expert parallelism load balancing for MoE<br>layers. |
| --enable-expert-parallel | Boolean flag | False | N/A | Use expert parallelism instead of tensor parallelism<br>for MoE layers. |
| --no-enable-expert-parallel | Boolean flag | False | N/A | Use expert parallelism instead of tensor parallelism<br>for MoE layers. |
| --eplb-config | N/A | EPLBConfig(window_size=1000, step_interval=3000,<br>num_redundant_experts=0, log_balancedness=False,<br>log_balancedness_interval=1, use_async=True,<br>policy='default', communicator=None) | N/A | Expert parallelism configuration.<br>API docs: https://docs.vllm.ai/en/latest/api/vllm/conf<br>ig/#vllm.config.EPLBConfig<br>Should either be a valid JSON string or JSON keys<br>passed individually. |
| --expert-placement-strategy | Enum | linear | linear,round_robin | The expert placement strategy for MoE layers:<br>- "linear": Experts are placed in a contiguous manner.<br>For example, with 4 experts and 2 ranks, rank 0 will<br>have experts [0, 1] and rank 1 will have experts [2,<br>3].<br>- "round_robin": Experts are placed in a round-robin<br>manner. For example, with 4 experts and 2 ranks, rank<br>0 will have experts [0, 2] and rank 1 will have<br>experts [1, 3]. This strategy can help improve load<br>balancing for grouped expert models with no redundant<br>experts. |
| --master-addr | N/A | 127.0.0.1 | N/A | distributed master address for multi-node distributed<br>inference when distributed_executor_backend is mp. |
| --master-port | N/A | 29501 | N/A | distributed master port for multi-node distributed<br>inference when distributed_executor_backend is mp. |
| --max-parallel-loading-workers | N/A | None | N/A | Maximum number of parallel loading workers when<br>loading model sequentially in multiple batches. To<br>avoid RAM OOM when using tensor parallel and large<br>models. |
| --nnodes | N/A | 1 | N/A | num of nodes for multi-node distributed inference when<br>distributed_executor_backend is mp. |
| --node-rank | N/A | 0 | N/A | distributed node rank for multi-node distributed<br>inference when distributed_executor_backend is mp. |
| --numa-bind | Boolean flag | False | N/A | Enable NUMA binding for GPU worker subprocesses.<br>By default, workers are pinned to their GPU's NUMA-<br>local CPUs and memory; on PCT-capable Xeons they also<br>auto-bind to the SKU's PCT priority cores. |
| --no-numa-bind | Boolean flag | False | N/A | Enable NUMA binding for GPU worker subprocesses.<br>By default, workers are pinned to their GPU's NUMA-<br>local CPUs and memory; on PCT-capable Xeons they also<br>auto-bind to the SKU's PCT priority cores. |
| --numa-bind-cpus | List | None | N/A | Optional CPU lists to bind each GPU worker to.<br>Specify one CPU list per visible GPU, for example<br>`["0-3", "4-7", "8-11", "12-15"]`. When set, vLLM uses<br>`numactl --physcpubind` instead of `--cpunodebind`.<br>This is useful for custom policies such as binding to<br>PCT or other high-frequency cores. Each entry must use<br>`numactl --physcpubind` CPU-list syntax, for example<br>`"0-3"` or `"0,2,4-7"`. |
| --numa-bind-nodes | List | None | N/A | NUMA node to bind each GPU worker to.<br>Specify one NUMA node per visible GPU, for example<br>`[0, 0, 1, 1]` for a 4-GPU system with GPUs 0-1 on<br>NUMA node 0 and GPUs 2-3 on NUMA node 1. If unset and<br>`numa_bind=True`, vLLM auto-detects the GPU-to-NUMA<br>topology. The values are passed to `numactl --membind`<br>and `--cpunodebind`, so they must be valid `numactl`<br>NUMA node indices. |
| --pipeline-parallel-size | N/A | 1 | N/A | Number of pipeline parallel groups. |
| --prefill-context-parallel-size | N/A | 1 | N/A | Number of prefill context parallel groups. |
| --ray-workers-use-nsight | Boolean flag | False | N/A | Whether to profile Ray workers with nsight, see<br>https://docs.ray.io/en/latest/ray-observability/user-<br>guides/profiling.html#profiling-nsight-profiler. |
| --no-ray-workers-use-nsight | Boolean flag | False | N/A | Whether to profile Ray workers with nsight, see<br>https://docs.ray.io/en/latest/ray-observability/user-<br>guides/profiling.html#profiling-nsight-profiler. |
| --tensor-parallel-size | N/A | 1 | N/A | Number of tensor parallel groups. |
| --ubatch-size | N/A | 0 | N/A | Number of ubatch size. |
| --worker-cls | N/A | auto | N/A | The full name of the worker class to use. If "auto",<br>the worker class will be determined based on the<br>platform. |
| --worker-extension-cls | N/A | (empty string) | N/A | The full name of the worker extension class to use.<br>The worker extension class is dynamically inherited by<br>the worker class. This is used to inject new<br>attributes and methods to the worker class for use in<br>collective_rpc calls. |

**Nested fields (`EPLBConfig`):**

| Sub-field | Type | Default |
| --- | --- | --- |
| `window_size` | `int` | `1000` |
| `step_interval` | `int` | `3000` |
| `num_redundant_experts` | `int` | `0` |
| `log_balancedness` | `bool` | `False` |
| `log_balancedness_interval` | `int` | `1` |
| `use_async` | `bool` | `True` |
| `policy` | `EPLBPolicyOption` | `"default"` |
| `communicator` | `EPLBCommunicatorBackend \| None` | `None` |

## CacheConfig

> Section description (from log):

```text
  Configuration for the KV cache.
```

| Name | Type | Default | Choices | Description |
| --- | --- | --- | --- | --- |
| --block-size | N/A | None | N/A | Size of a contiguous cache block in number of tokens.<br>Accepts None (meaning "use default"). After<br>construction, always int. |
| --calculate-kv-scales | Boolean flag | False | N/A | Deprecated: This option is deprecated and will be<br>removed in v0.19. It enables dynamic calculation of<br>`k_scale` and `v_scale` when kv_cache_dtype is fp8. If<br>`False`, the scales will be loaded from the model<br>checkpoint if available. Otherwise, the scales will<br>default to 1.0. |
| --no-calculate-kv-scales | Boolean flag | False | N/A | Deprecated: This option is deprecated and will be<br>removed in v0.19. It enables dynamic calculation of<br>`k_scale` and `v_scale` when kv_cache_dtype is fp8. If<br>`False`, the scales will be loaded from the model<br>checkpoint if available. Otherwise, the scales will<br>default to 1.0. |
| --enable-prefix-caching | Boolean flag | None | N/A | Whether to enable prefix caching. |
| --no-enable-prefix-caching | Boolean flag | None | N/A | Whether to enable prefix caching. |
| --gpu-memory-utilization | N/A | 0.92 | N/A | The fraction of GPU memory to be used for the model<br>executor, which can range from 0 to 1. For example, a<br>value of 0.5 would imply 50% GPU memory utilization.<br>If unspecified, will use the default value of 0.92.<br>This is a per-instance limit, and only applies to the<br>current vLLM instance. It does not matter if you have<br>another vLLM instance running on the same GPU. For<br>example, if you have two vLLM instances running on the<br>same GPU, you can set the GPU memory utilization to<br>0.5 for each instance. |
| --kv-cache-dtype | Enum | auto | auto,bfloat16,float16,fp8,fp8_ds_mla,fp8_e4m3,fp8_e5m2,fp8_inc,fp8_per_token_head,int8_per_token_head,nvfp4,turboquant_3bit_nc,turboquant_4bit_nc,turboquant_k3v4_nc,turboquant_k8v4 | Data type for kv cache storage. If "auto", will use<br>model data type. CUDA 11.8+ supports fp8 (=fp8_e4m3)<br>and fp8_e5m2. ROCm (AMD GPU) supports fp8 (=fp8_e4m3).<br>Intel Gaudi (HPU) supports fp8 (using fp8_inc). Some<br>models (namely DeepSeekV3.2) default to fp8, set to<br>bfloat16 to use bfloat16 instead, this is an invalid<br>option for models that do not default to fp8. |
| --kv-cache-dtype-skip-layers | List | [] | N/A | Layer patterns to skip KV cache quantization. Accepts<br>layer indices (e.g., '0', '2', '4') or attention type<br>names (e.g., 'sliding_window'). |
| --kv-cache-memory-bytes | N/A | None | N/A | Size of KV Cache per GPU in bytes. By default, this is<br>set to None and vllm can automatically infer the kv<br>cache size based on gpu_memory_utilization. However,<br>users may want to manually specify the kv cache memory<br>size. kv_cache_memory_bytes allows more fine-grain<br>control of how much memory gets used when compared<br>with using gpu_memory_utilization. Note that<br>kv_cache_memory_bytes (when not-None) ignores<br>gpu_memory_utilization<br>Parse human-readable integers like '1k', '2M', etc.<br>Including decimal values with decimal multipliers.<br>    Examples:<br>    - '1k' -> 1,000<br>    - '1K' -> 1,024<br>    - '25.6k' -> 25,600 |
| --kv-offloading-backend | Enum | native | lmcache,native | The backend to use for KV cache offloading. Supported<br>backends include 'native' (vLLM native CPU<br>offloading), 'lmcache'. KV offloading is only<br>activated when kv_offloading_size is set. |
| --kv-offloading-size | N/A | None | N/A | Size of the KV cache offloading buffer in GiB. When TP<br>> 1, this is the total buffer size summed across all<br>TP ranks. By default, this is set to None, which means<br>no KV offloading is enabled. When set, vLLM will<br>enable KV cache offloading to CPU using the<br>kv_offloading_backend. |
| --kv-sharing-fast-prefill | Boolean flag | False | N/A | This feature is work in progress and no prefill<br>optimization takes place with this flag enabled<br>currently.<br>In some KV sharing setups, e.g. YOCO<br>(https://arxiv.org/abs/2405.05254), some layers can<br>skip tokens corresponding to prefill. This flag<br>enables attention metadata for eligible layers to be<br>overridden with metadata necessary for implementing<br>this optimization in some models (e.g. Gemma3n) |
| --no-kv-sharing-fast-prefill | Boolean flag | False | N/A | This feature is work in progress and no prefill<br>optimization takes place with this flag enabled<br>currently.<br>In some KV sharing setups, e.g. YOCO<br>(https://arxiv.org/abs/2405.05254), some layers can<br>skip tokens corresponding to prefill. This flag<br>enables attention metadata for eligible layers to be<br>overridden with metadata necessary for implementing<br>this optimization in some models (e.g. Gemma3n) |
| --mamba-block-size | N/A | None | N/A | Size of a contiguous cache block in number of tokens<br>for mamba cache. Can be set only when prefix caching<br>is enabled. Value must be a multiple of 8 to align<br>with causal_conv1d kernel. |
| --mamba-cache-dtype | Enum | auto | auto,bfloat16,float16,float32 | The data type to use for the Mamba cache (both the<br>conv as well as the ssm state). If set to 'auto', the<br>data type will be inferred from the model config. |
| --mamba-cache-mode | Enum | none | align,all,none | The cache strategy for Mamba layers.<br>- "none": set when prefix caching is disabled.<br>- "all": cache the mamba state of all tokens at<br>position i * block_size. This is the default behavior<br>(for models that support it) when prefix caching is<br>enabled.<br>- "align": only cache the mamba state of the last<br>token of each scheduler step and when the token is at<br>position i * block_size. |
| --mamba-ssm-cache-dtype | Enum | auto | auto,bfloat16,float16,float32 | The data type to use for the Mamba cache (ssm state<br>only, conv state will still be controlled by<br>mamba_cache_dtype). If set to 'auto', the data type<br>for the ssm state will be determined by<br>mamba_cache_dtype. |
| --num-gpu-blocks-override | N/A | None | N/A | Number of GPU blocks to use. This overrides the<br>profiled `num_gpu_blocks` if specified. Does nothing<br>if `None`. Used for testing preemption. |
| --prefix-caching-hash-algo | Enum | sha256 | sha256,sha256_cbor,xxhash,xxhash_cbor | Set the hash algorithm for prefix caching:<br>- "sha256" uses Pickle for object serialization before<br>hashing. This is the current default, as SHA256 is the<br>most secure choice to avoid potential hash collisions.<br>- "sha256_cbor" provides a reproducible, cross-<br>language compatible hash. It serializes objects using<br>canonical CBOR and hashes them with SHA-256.<br>- "xxhash" uses Pickle serialization with xxHash<br>(128-bit) for faster, non-cryptographic hashing.<br>Requires the optional ``xxhash`` package. IMPORTANT:<br>Use of a hashing algorithm that is not considered<br>cryptographically secure theoretically increases the<br>risk of hash collisions, which can cause undefined<br>behavior or even leak private information in multi-<br>tenant environments. Even if collisions are still very<br>unlikely, it is important to consider your security<br>risk tolerance against the performance benefits before<br>turning this on.<br>- "xxhash_cbor" combines canonical CBOR serialization<br>with xxHash for reproducible hashing. Requires the<br>optional ``xxhash`` package. |

## OffloadConfig

> Section description (from log):

```text
  Configuration for model weight offloading to reduce GPU memory usage.
```

| Name | Type | Default | Choices | Description |
| --- | --- | --- | --- | --- |
| --cpu-offload-gb | N/A | 0 | N/A | The space in GiB to offload to CPU, per GPU. Default<br>is 0, which means no offloading. Intuitively, this<br>argument can be seen as a virtual way to increase the<br>GPU memory size. For example, if you have one 24 GB<br>GPU and set this to 10, virtually you can think of it<br>as a 34 GB GPU. Then you can load a 13B model with<br>BF16 weight, which requires at least 26GB GPU memory.<br>Note that this requires fast CPU-GPU interconnect, as<br>part of the model is loaded from CPU memory to GPU<br>memory on the fly in each model forward pass. This<br>uses UVA (Unified Virtual Addressing) for zero-copy<br>access. |
| --cpu-offload-params | List | set() | N/A | The set of parameter name segments to target for CPU<br>offloading. Unmatched parameters are not offloaded. If<br>this set is empty, parameters are offloaded non-<br>selectively until the memory limit defined by<br>`cpu_offload_gb` is reached. Examples:<br>    - For parameter name "mlp.experts.w2_weight":<br>        - "experts" or "experts.w2_weight" will match.<br>        - "expert" or "w2" will NOT match (must be<br>exact segments). This allows distinguishing parameters<br>like "w2_weight" and "w2_weight_scale". |
| --offload-backend | Enum | auto | auto,prefetch,uva | The backend for weight offloading. Options:<br>- "auto": Selects based on which sub-config has non-<br>default values (prefetch if offload_group_size > 0,<br>uva if cpu_offload_gb > 0).<br>- "uva": UVA (Unified Virtual Addressing) zero-copy<br>offloading.<br>- "prefetch": Async prefetch with group-based layer<br>offloading. |
| --offload-group-size | N/A | 0 | N/A | Group every N layers together. Offload last<br>`offload_num_in_group` layers of each group. Default<br>is 0 (disabled). Example: group_size=8, num_in_group=2<br>offloads layers 6,7,14,15,22,23,... Unlike<br>cpu_offload_gb, this uses explicit async prefetching<br>to hide transfer latency. |
| --offload-num-in-group | N/A | 1 | N/A | Number of layers to offload per group. Must be <=<br>offload_group_size. Default is 1. |
| --offload-params | List | set() | N/A | The set of parameter name segments to target for<br>prefetch offloading. Unmatched parameters are not<br>offloaded. If this set is empty, ALL parameters of<br>each offloaded layer are offloaded. Uses segment<br>matching: "w13_weight" matches<br>"mlp.experts.w13_weight" but not<br>"mlp.experts.w13_weight_scale". |
| --offload-prefetch-step | N/A | 1 | N/A | Number of layers to prefetch ahead. Higher values hide<br>more latency but use more GPU memory. Default is 1. |

## MultiModalConfig

> Section description (from log):

```text
  Controls the behavior of multimodal models.
```

| Name | Type | Default | Choices | Description |
| --- | --- | --- | --- | --- |
| --enable-mm-embeds | Boolean flag | False | N/A | If `True`, enables passing multimodal embeddings: for<br>`LLM` class, this refers to tensor inputs under<br>`multi_modal_data`; for the OpenAI-compatible server,<br>this refers to chat messages with content `"type":<br>"*_embeds"`.<br>When enabled with `--limit-mm-per-prompt` set to 0 for<br>a modality, precomputed embeddings skip count<br>validation for that modality,  saving memory by not<br>loading encoder modules while still enabling<br>embeddings as an input. Limits greater than 0 still<br>apply to embeddings.<br>WARNING: The vLLM engine may crash if incorrect shape<br>of embeddings is passed. Only enable this flag for<br>trusted users! |
| --no-enable-mm-embeds | Boolean flag | False | N/A | If `True`, enables passing multimodal embeddings: for<br>`LLM` class, this refers to tensor inputs under<br>`multi_modal_data`; for the OpenAI-compatible server,<br>this refers to chat messages with content `"type":<br>"*_embeds"`.<br>When enabled with `--limit-mm-per-prompt` set to 0 for<br>a modality, precomputed embeddings skip count<br>validation for that modality,  saving memory by not<br>loading encoder modules while still enabling<br>embeddings as an input. Limits greater than 0 still<br>apply to embeddings.<br>WARNING: The vLLM engine may crash if incorrect shape<br>of embeddings is passed. Only enable this flag for<br>trusted users! |
| --interleave-mm-strings | Boolean flag | False | N/A | Enable fully interleaved support for multimodal<br>prompts, while using<br>--chat-template-content-format=string. |
| --no-interleave-mm-strings | Boolean flag | False | N/A | Enable fully interleaved support for multimodal<br>prompts, while using<br>--chat-template-content-format=string. |
| --language-model-only | Boolean flag | False | N/A | If True, disables all multimodal inputs by setting all<br>modality limits to 0. Equivalent to setting `--limit-<br>mm-per-prompt` to 0 for every modality. |
| --no-language-model-only | Boolean flag | False | N/A | If True, disables all multimodal inputs by setting all<br>modality limits to 0. Equivalent to setting `--limit-<br>mm-per-prompt` to 0 for every modality. |
| --limit-mm-per-prompt | N/A | {} | N/A | The maximum number of input items and options allowed<br>per prompt for each modality.<br>Defaults to 999 for each modality.<br>Legacy format (count only): {"image": 16, "video": 2}<br>Configurable format (with options): {"video":<br>{"count": 1, "num_frames": 32, "width": 512, "height":<br>512}, "image": {"count": 5, "width": 512, "height":<br>512}}<br>Mixed format (combining both): {"image": 16, "video":<br>{"count": 1, "num_frames": 32, "width": 512, "height":<br>512}}<br>Should either be a valid JSON string or JSON keys<br>passed individually. |
| --media-io-kwargs | N/A | {} | N/A | Additional args passed to process media inputs, keyed<br>by modalities. For example, to set num_frames for<br>video, set `--media-io-kwargs '{"video":<br>{"num_frames": 40} }'`<br>Should either be a valid JSON string or JSON keys<br>passed individually. |
| --mm-encoder-attn-backend | N/A | None | N/A | Optional override for the multi-modal encoder<br>attention backend when using vision transformers.<br>Accepts any value from `vllm.v1.attention.backends.reg<br>istry.AttentionBackendEnum` (e.g. `FLASH_ATTN`). |
| --mm-encoder-attn-dtype | Enum | None | fp8,None | Optional dtype override for ViT encoder attention. Set<br>to `"fp8"` to enable FP8 quantization via the<br>FlashInfer cuDNN backend. When set to `"fp8"` without<br>a scale file, dynamic scaling is used automatically.<br>See docs/features/quantization/fp8_vit_attn.md for<br>details. |
| --mm-encoder-fp8-scale-path | N/A | None | N/A | Path to a JSON file containing per-layer FP8 Q/K/V<br>scales for ViT encoder attention. When provided (with<br>`mm_encoder_attn_dtype="fp8"`), static scaling is<br>used. When omitted, dynamic scaling is used. |
| --mm-encoder-fp8-scale-save-margin | N/A | 1.5 | N/A | Safety margin multiplied onto scales when auto-saving.<br>A value > 1 leaves headroom so that inputs with larger<br>activations than the calibration set do not overflow<br>FP8 range. Default 1.5. |
| --mm-encoder-fp8-scale-save-path | N/A | None | N/A | When set with dynamic FP8 scaling<br>(`mm_encoder_attn_dtype="fp8"` and no<br>`mm_encoder_fp8_scale_path`), saves the calibrated<br>scales to this file after the amax history buffer is<br>full. The saved file can then be used as<br>`mm_encoder_fp8_scale_path` in subsequent runs. |
| --mm-encoder-only | Boolean flag | False | N/A | When enabled, skips the language component of the<br>model.<br>This is usually only valid in disaggregated Encoder<br>process. |
| --no-mm-encoder-only | Boolean flag | False | N/A | When enabled, skips the language component of the<br>model.<br>This is usually only valid in disaggregated Encoder<br>process. |
| --mm-encoder-tp-mode | Enum | weights | data,weights | Indicates how to optimize multi-modal encoder<br>inference using tensor parallelism (TP).<br>- `"weights"`: Within the same vLLM engine, split the<br>weights of each layer across TP ranks. (default TP<br>behavior)<br>- `"data"`: Within the same vLLM engine, split the<br>batched input data across TP ranks to process the data<br>in parallel, while hosting the full weights on each TP<br>rank. This batch-level DP is not to be confused with<br>API request-level DP (which is controlled by `--data-<br>parallel-size`). This is only supported on a per-model<br>basis and falls back to `"weights"` if the encoder<br>does not support DP. |
| --mm-processor-cache-gb | N/A | 4 | N/A | The size (in GiB) of the multi-modal processor cache,<br>which is used to avoid re-processing past multi-modal<br>inputs.<br>This cache is duplicated for each API process and<br>engine core process, resulting in a total memory usage<br>of `mm_processor_cache_gb * (api_server_count +<br>data_parallel_size)`.<br>Set to `0` to disable this cache completely (not<br>recommended). |
| --mm-processor-cache-type | Enum | lru | lru,shm | Type of cache to use for the multi-modal<br>preprocessor/mapper. If `shm`, use shared memory FIFO<br>cache. If `lru`, use mirrored LRU cache. |
| --mm-processor-kwargs | N/A | None | N/A | Arguments to be forwarded to the model's processor for<br>multi-modal data, e.g., image processor. Overrides for<br>the multi-modal processor obtained from<br>`transformers.AutoProcessor.from_pretrained`.<br>The available overrides depend on the model that is<br>being run.<br>For example, for Phi-3-Vision: `{"num_crops": 4}`.<br>Should either be a valid JSON string or JSON keys<br>passed individually. |
| --mm-shm-cache-max-object-size-mb | N/A | 128 | N/A | Size limit (in MiB) for each object stored in the<br>multi-modal processor shared memory cache. Only<br>effective when `mm_processor_cache_type` is `"shm"`. |
| --mm-tensor-ipc | Enum | direct_rpc | direct_rpc,torch_shm | IPC (inter-process communication) method for<br>multimodal tensors.<br>- "direct_rpc": Use msgspec serialization via RPC<br>- "torch_shm": Use torch.multiprocessing shared memory<br>for zero-copy IPC Defaults to "direct_rpc". |
| --skip-mm-profiling | Boolean flag | False | N/A | When enabled, skips multimodal memory profiling and<br>only profiles with language backbone model during<br>engine initialization.<br>This reduces engine startup time but shifts the<br>responsibility to users for estimating the peak memory<br>usage of the activation of multimodal encoder and<br>embedding cache. |
| --no-skip-mm-profiling | Boolean flag | False | N/A | When enabled, skips multimodal memory profiling and<br>only profiles with language backbone model during<br>engine initialization.<br>This reduces engine startup time but shifts the<br>responsibility to users for estimating the peak memory<br>usage of the activation of multimodal encoder and<br>embedding cache. |
| --video-pruning-rate | N/A | None | N/A | Sets pruning rate for video pruning via Efficient<br>Video Sampling. Value sits in range [0;1) and<br>determines fraction of media tokens from each video to<br>be pruned. |

## LoRAConfig

> Section description (from log):

```text
  Configuration for LoRA.
```

| Name | Type | Default | Choices | Description |
| --- | --- | --- | --- | --- |
| --default-mm-loras | N/A | None | N/A | Dictionary mapping specific modalities to LoRA model<br>paths; this field is only applicable to multimodal<br>models and should be leveraged when a model always<br>expects a LoRA to be active when a given modality is<br>present. Note that currently, if a request provides<br>multiple additional modalities, each of which have<br>their own LoRA, we do NOT apply default_mm_loras<br>because we currently only support one lora adapter per<br>prompt. When run in offline mode, the lora IDs for n<br>modalities will be automatically assigned to 1-n with<br>the names of the modalities in alphabetic order.<br>Should either be a valid JSON string or JSON keys<br>passed individually. |
| --enable-lora | Boolean flag | None | N/A | If True, enable handling of LoRA adapters. |
| --no-enable-lora | Boolean flag | None | N/A | If True, enable handling of LoRA adapters. |
| --enable-mixed-moe-lora-format | Boolean flag | False | N/A | If True, force the engine to use the universal 2D MoE<br>LoRA wrapper (`FusedMoEWithLoRA`) regardless of the<br>model's `is_3d_moe_weight` flag, so that 2D-format and<br>3D-format MoE LoRA adapters can be served in the same<br>deployment. Only meaningful forMoE models; ignored<br>otherwise. Default False  keeps the existing model-<br>driven behavior. |
| --no-enable-mixed-moe-lora-format | Boolean flag | False | N/A | If True, force the engine to use the universal 2D MoE<br>LoRA wrapper (`FusedMoEWithLoRA`) regardless of the<br>model's `is_3d_moe_weight` flag, so that 2D-format and<br>3D-format MoE LoRA adapters can be served in the same<br>deployment. Only meaningful forMoE models; ignored<br>otherwise. Default False  keeps the existing model-<br>driven behavior. |
| --enable-tower-connector-lora | Boolean flag | False | N/A | If `True`, LoRA support for the tower (vision encoder)<br>and connector  of multimodal models will be enabled.<br>This is an experimental feature and  currently only<br>supports some MM models such as the Qwen VL series.<br>The default  is False. |
| --no-enable-tower-connector-lora | Boolean flag | False | N/A | If `True`, LoRA support for the tower (vision encoder)<br>and connector  of multimodal models will be enabled.<br>This is an experimental feature and  currently only<br>supports some MM models such as the Qwen VL series.<br>The default  is False. |
| --fully-sharded-loras | Boolean flag | False | N/A | By default, only half of the LoRA computation is<br>sharded with tensor parallelism. Enabling this will<br>use the fully sharded layers. At high sequence length,<br>max rank or tensor parallel size, this is likely<br>faster. |
| --no-fully-sharded-loras | Boolean flag | False | N/A | By default, only half of the LoRA computation is<br>sharded with tensor parallelism. Enabling this will<br>use the fully sharded layers. At high sequence length,<br>max rank or tensor parallel size, this is likely<br>faster. |
| --lora-dtype | Enum | auto | auto,bfloat16,float16 | Data type for LoRA. If auto, will default to base<br>model dtype. |
| --lora-target-modules | List | None | N/A | Restrict LoRA to specific module suffixes (e.g.,<br>["o_proj", "qkv_proj"]). If None, all supported LoRA<br>modules are used. This allows deployment-time control<br>over which modules have LoRA applied, useful for<br>performance tuning. |
| --max-cpu-loras | N/A | None | N/A | Maximum number of LoRAs to store in CPU memory. Must<br>be >= than `max_loras`. |
| --max-lora-rank | Enum | 16 | 1,8,16,32,64,128,256,320,512 | Max LoRA rank. |
| --max-loras | N/A | 1 | N/A | Max number of LoRAs in a single batch. |
| --specialize-active-lora | Boolean flag | False | N/A | Whether to construct lora kernel grid by the number of<br>active LoRA adapters. When set to True, separate cuda<br>graphs will be captured for different counts of active<br>LoRAs (powers of 2 up to max_loras), which can improve<br>performance for variable LoRA usage patterns at the<br>cost of increased startup time and memory usage. Only<br>takes effect when cudagraph_specialize_lora is True. |
| --no-specialize-active-lora | Boolean flag | False | N/A | Whether to construct lora kernel grid by the number of<br>active LoRA adapters. When set to True, separate cuda<br>graphs will be captured for different counts of active<br>LoRAs (powers of 2 up to max_loras), which can improve<br>performance for variable LoRA usage patterns at the<br>cost of increased startup time and memory usage. Only<br>takes effect when cudagraph_specialize_lora is True. |

## ObservabilityConfig

> Section description (from log):

```text
  Configuration for observability - metrics and tracing.
```

| Name | Type | Default | Choices | Description |
| --- | --- | --- | --- | --- |
| --collect-detailed-traces | List | None | all,model,worker,None | It makes sense to set this only if `--otlp-traces-<br>endpoint` is set. If set, it will collect detailed<br>traces for the specified modules. This involves use of<br>possibly costly and or blocking operations and hence<br>might have a performance impact.<br>Note that collecting detailed timing information for<br>each request can be expensive. |
| --cudagraph-metrics | Boolean flag | False | N/A | Enable CUDA graph metrics (number of padded/unpadded<br>tokens, runtime cudagraph dispatch modes, and their<br>observed frequencies at every logging interval). |
| --no-cudagraph-metrics | Boolean flag | False | N/A | Enable CUDA graph metrics (number of padded/unpadded<br>tokens, runtime cudagraph dispatch modes, and their<br>observed frequencies at every logging interval). |
| --enable-layerwise-nvtx-tracing | Boolean flag | False | N/A | Enable layerwise NVTX tracing. This traces the<br>execution of each layer or module in the model and<br>attach information such as input/output shapes to nvtx<br>range markers. Noted that this doesn't work with CUDA<br>graphs enabled. |
| --no-enable-layerwise-nvtx-tracing | Boolean flag | False | N/A | Enable layerwise NVTX tracing. This traces the<br>execution of each layer or module in the model and<br>attach information such as input/output shapes to nvtx<br>range markers. Noted that this doesn't work with CUDA<br>graphs enabled. |
| --enable-logging-iteration-details | Boolean flag | False | N/A | Enable detailed logging of iteration details. If set,<br>vllm EngineCore will log iteration details This<br>includes number of context/generation requests and<br>tokens and the elapsed cpu time for the iteration. |
| --no-enable-logging-iteration-details | Boolean flag | False | N/A | Enable detailed logging of iteration details. If set,<br>vllm EngineCore will log iteration details This<br>includes number of context/generation requests and<br>tokens and the elapsed cpu time for the iteration. |
| --enable-mfu-metrics | Boolean flag | False | N/A | Enable Model FLOPs Utilization (MFU) metrics. |
| --no-enable-mfu-metrics | Boolean flag | False | N/A | Enable Model FLOPs Utilization (MFU) metrics. |
| --kv-cache-metrics | Boolean flag | False | N/A | Enable KV cache residency metrics (lifetime, idle<br>time, reuse gaps). Uses sampling to minimize overhead.<br>Requires log stats to be enabled (i.e., --disable-log-<br>stats not set). |
| --no-kv-cache-metrics | Boolean flag | False | N/A | Enable KV cache residency metrics (lifetime, idle<br>time, reuse gaps). Uses sampling to minimize overhead.<br>Requires log stats to be enabled (i.e., --disable-log-<br>stats not set). |
| --kv-cache-metrics-sample | N/A | 0.01 | N/A | Sampling rate for KV cache metrics (0.0, 1.0]. Default<br>0.01 = 1% of blocks. |
| --otlp-traces-endpoint | N/A | None | N/A | Target URL to which OpenTelemetry traces will be sent. |
| --show-hidden-metrics-for-version | N/A | None | N/A | Enable deprecated Prometheus metrics that have been<br>hidden since the specified version. For example, if a<br>previously deprecated metric has been hidden since the<br>v0.7.0 release, you use `--show-hidden-metrics-for-<br>version=0.7` as a temporary escape hatch while you<br>migrate to new metrics. The metric is likely to be<br>removed completely in an upcoming release. |

## SchedulerConfig

> Section description (from log):

```text
  Scheduler configuration.
```

| Name | Type | Default | Choices | Description |
| --- | --- | --- | --- | --- |
| --async-scheduling | Boolean flag | None | N/A | If set to False, disable async scheduling. Async<br>scheduling helps to avoid gaps in GPU utilization,<br>leading to better latency and throughput. |
| --no-async-scheduling | Boolean flag | None | N/A | If set to False, disable async scheduling. Async<br>scheduling helps to avoid gaps in GPU utilization,<br>leading to better latency and throughput. |
| --disable-chunked-mm-input | Boolean flag | False | N/A | If set to true and chunked prefill is enabled, we do<br>not want to partially schedule a multimodal item. Only<br>used in V1 This ensures that if a request has a mixed<br>prompt (like text tokens TTTT followed by image tokens<br>IIIIIIIIII) where only some image tokens can be<br>scheduled (like TTTTIIIII, leaving IIIII), it will be<br>scheduled as TTTT in one step and IIIIIIIIII in the<br>next. |
| --no-disable-chunked-mm-input | Boolean flag | False | N/A | If set to true and chunked prefill is enabled, we do<br>not want to partially schedule a multimodal item. Only<br>used in V1 This ensures that if a request has a mixed<br>prompt (like text tokens TTTT followed by image tokens<br>IIIIIIIIII) where only some image tokens can be<br>scheduled (like TTTTIIIII, leaving IIIII), it will be<br>scheduled as TTTT in one step and IIIIIIIIII in the<br>next. |
| --disable-hybrid-kv-cache-manager | Boolean flag | None | N/A | If set to True, KV cache manager will allocate the<br>same size of KV cache for all attention layers even if<br>there are multiple type of attention layers like full<br>attention and sliding window attention. If set to<br>None, the default value will be determined based on<br>the environment and starting configuration. |
| --no-disable-hybrid-kv-cache-manager | Boolean flag | None | N/A | If set to True, KV cache manager will allocate the<br>same size of KV cache for all attention layers even if<br>there are multiple type of attention layers like full<br>attention and sliding window attention. If set to<br>None, the default value will be determined based on<br>the environment and starting configuration. |
| --enable-chunked-prefill | Boolean flag | None | N/A | If True, prefill requests can be chunked based on the<br>remaining `max_num_batched_tokens`.<br>The default value here is mainly for convenience when<br>testing. In real usage, this should be set in<br>`EngineArgs.create_engine_config`. |
| --no-enable-chunked-prefill | Boolean flag | None | N/A | If True, prefill requests can be chunked based on the<br>remaining `max_num_batched_tokens`.<br>The default value here is mainly for convenience when<br>testing. In real usage, this should be set in<br>`EngineArgs.create_engine_config`. |
| --long-prefill-token-threshold | N/A | 0 | N/A | For chunked prefill, a request is considered long if<br>the prompt is longer than this number of tokens. |
| --max-long-partial-prefills | N/A | 1 | N/A | For chunked prefill, the maximum number of prompts<br>longer than long_prefill_token_threshold that will be<br>prefilled concurrently. Setting this less than<br>max_num_partial_prefills will allow shorter prompts to<br>jump the queue in front of longer prompts in some<br>cases, improving latency. |
| --max-num-batched-tokens | N/A | None | N/A | Maximum number of tokens that can be processed in a<br>single iteration.<br>The default value here is mainly for convenience when<br>testing. In real usage, this should be set in<br>`EngineArgs.create_engine_config`.<br>Parse human-readable integers like '1k', '2M', etc.<br>Including decimal values with decimal multipliers.<br>    Examples:<br>    - '1k' -> 1,000<br>    - '1K' -> 1,024<br>    - '25.6k' -> 25,600 |
| --max-num-partial-prefills | N/A | 1 | N/A | For chunked prefill, the maximum number of sequences<br>that can be partially prefilled concurrently. |
| --max-num-seqs | N/A | None | N/A | Maximum number of sequences to be processed in a<br>single iteration.<br>The default value here is mainly for convenience when<br>testing. In real usage, this should be set in<br>`EngineArgs.create_engine_config`. |
| --scheduler-cls | N/A | None | N/A | The scheduler class to use.<br>"vllm.v1.core.sched.scheduler.Scheduler" is the<br>default scheduler. Can be a class directly or the path<br>to a class of form "mod.custom_class". |
| --scheduler-reserve-full-isl | Boolean flag | True | N/A | If True, the scheduler checks whether the full input<br>sequence length fits in the KV cache before admitting<br>a new request, rather than only checking the first<br>chunk. Prevents over-admission and KV cache thrashing<br>with chunked prefill. |
| --no-scheduler-reserve-full-isl | Boolean flag | True | N/A | If True, the scheduler checks whether the full input<br>sequence length fits in the KV cache before admitting<br>a new request, rather than only checking the first<br>chunk. Prevents over-admission and KV cache thrashing<br>with chunked prefill. |
| --scheduling-policy | Enum | fcfs | fcfs,priority | The scheduling policy to use:<br>- "fcfs" means first come first served, i.e. requests<br>are handled in order  of arrival.<br>- "priority" means requests are handled based on given<br>priority (lower value means earlier handling) and time<br>of arrival deciding any ties). |
| --stream-interval | N/A | 1 | N/A | The interval (or buffer size) for streaming in terms<br>of token length. A smaller value (1) makes streaming<br>smoother by sending each token immediately, while a<br>larger value (e.g., 10) reduces host overhead and may<br>increase throughput by batching multiple tokens before<br>sending. |

## CompilationConfig

> Section description (from log):

```text
  Configuration for compilation.
  
      You must pass CompilationConfig to VLLMConfig constructor.
      VLLMConfig's post_init does further initialization. If used outside of the
      VLLMConfig, some fields will be left in an improper state.
  
      It contains PassConfig, which controls the custom fusion/transformation passes.
      The rest has three parts:
  
      - Top-level Compilation control:
          - [`mode`][vllm.config.CompilationConfig.mode]
          - [`debug_dump_path`][vllm.config.CompilationConfig.debug_dump_path]
          - [`cache_dir`][vllm.config.CompilationConfig.cache_dir]
          - [`backend`][vllm.config.CompilationConfig.backend]
          - [`custom_ops`][vllm.config.CompilationConfig.custom_ops]
          - [`splitting_ops`][vllm.config.CompilationConfig.splitting_ops]
          - [`compile_mm_encoder`][vllm.config.CompilationConfig.compile_mm_encoder]
      - CudaGraph capture:
          - [`cudagraph_mode`][vllm.config.CompilationConfig.cudagraph_mode]
          - [`cudagraph_capture_sizes`]
          [vllm.config.CompilationConfig.cudagraph_capture_sizes]
          - [`max_cudagraph_capture_size`]
          [vllm.config.CompilationConfig.max_cudagraph_capture_size]
          - [`cudagraph_num_of_warmups`]
          [vllm.config.CompilationConfig.cudagraph_num_of_warmups]
          - [`cudagraph_copy_inputs`]
          [vllm.config.CompilationConfig.cudagraph_copy_inputs]
      - Inductor compilation:
          - [`compile_sizes`][vllm.config.CompilationConfig.compile_sizes]
          - [`compile_ranges_endpoints`]
              [vllm.config.CompilationConfig.compile_ranges_endpoints]
          - [`inductor_compile_config`]
          [vllm.config.CompilationConfig.inductor_compile_config]
          - [`inductor_passes`][vllm.config.CompilationConfig.inductor_passes]
          - custom inductor passes
  
      Why we have different sizes for cudagraph and inductor:
      - cudagraph: a cudagraph captured for a specific size can only be used
          for the same size. We need to capture all the sizes we want to use.
      - inductor: a graph compiled by inductor for a general shape can be used
          for different sizes. Inductor can also compile for specific sizes,
          where it can have more information to optimize the graph with fully
          static shapes. However, we find the general shape compilation is
          sufficient for most cases. It might be beneficial to compile for
          certain small batchsizes, where inductor is good at optimizing.
```

| Name | Type | Default | Choices | Description |
| --- | --- | --- | --- | --- |
| --cudagraph-capture-sizes | List | None | N/A | Sizes to capture cudagraph.<br>- None (default): capture sizes are inferred from vllm<br>config.<br>- list[int]: capture sizes are specified as given. |
| --max-cudagraph-capture-size | N/A | None | N/A | The maximum cudagraph capture size.<br>If cudagraph_capture_sizes is specified, this will be<br>set to the largest size in that list (or checked for<br>consistency if specified). If cudagraph_capture_sizes<br>is not specified, the list of sizes is generated<br>automatically following the pattern:<br>    [1, 2, 4] + list(range(8, 256, 8)) + list(<br>range(256, max_cudagraph_capture_size + 1, 16))<br>If not specified, max_cudagraph_capture_size is set to<br>min(max_num_seqs*2, 512) by default. This voids OOM in<br>tight memory scenarios with small max_num_seqs, and<br>prevents capture of many large graphs (>512) that<br>would greatly increase startup time with limited<br>performance benefit. |

**Nested fields (`CompilationConfig`):**

| Sub-field | Type | Default |
| --- | --- | --- |
| `mode` | `CompilationMode \| None` | `None` (V1 defaults to 3) |
| `debug_dump_path` | `Path \| None` | `None` |
| `cache_dir` | `str` | `""` |
| `compile_cache_save_format` | `"binary" \| "unpacked"` | `"binary"` |
| `backend` | `str` | `""` |
| `custom_ops` | `list[str]` | `[]` |
| `ir_enable_torch_wrap` | `bool \| None` | `None` |
| `splitting_ops` | `list[str] \| None` | `None` |
| `compile_mm_encoder` | `bool` | `False` |
| `cudagraph_mm_encoder` | `bool` | `False` |
| `encoder_cudagraph_token_budgets` | `list[int]` | `[]` |
| `encoder_cudagraph_max_vision_items_per_batch` | `int` | `0` |
| `encoder_cudagraph_max_frames_per_batch` | `int \| None` | `None` |
| `compile_sizes` | `list[int \| str] \| None` | `None` |
| `compile_ranges_endpoints` | `list[int] \| None` | `None` |
| `inductor_compile_config` | `dict` | `{}` |
| `inductor_passes` | `dict[str, str]` | `{}` |
| `cudagraph_mode` | `CUDAGraphMode \| None` | `None` |
| `cudagraph_num_of_warmups` | `int` | `0` |
| `cudagraph_capture_sizes` | `list[int] \| None` | `None` |
| `cudagraph_copy_inputs` | `bool` | `False` |
| `cudagraph_specialize_lora` | `bool` | `True` |
| `use_inductor_graph_partition` | `bool \| None` | `None` |
| `pass_config` | `PassConfig` | `{}` |
| `max_cudagraph_capture_size` | `int \| None` | `None` |
| `dynamic_shapes_config` | `DynamicShapesConfig` | see below |
| `local_cache_dir` | `str \| None` | `None` |
| `fast_moe_cold_start` | `bool \| None` | `None` |
| `static_all_moe_layers` | `list` | `[]` |

**Nested fields (`PassConfig`, set via `pass_config` key):**

| Sub-field | Type | Default |
| --- | --- | --- |
| `fuse_norm_quant` | `bool \| None` | `None` |
| `fuse_act_quant` | `bool \| None` | `None` |
| `fuse_attn_quant` | `bool \| None` | `None` |
| `eliminate_noops` | `bool` | `True` |
| `enable_sp` | `bool \| None` | `None` |
| `fuse_gemm_comms` | `bool \| None` | `None` |
| `fuse_allreduce_rms` | `bool \| None` | `None` |
| `fuse_minimax_qk_norm` | `bool \| None` | `None` (deprecated, no effect) |
| `enable_qk_norm_rope_fusion` | `bool \| None` | `None` |
| `fuse_rope_kvcache_cat_mla` | `bool \| None` | `None` |
| `fuse_act_padding` | `bool \| None` | `None` (ROCm only) |
| `fuse_mla_dual_rms_norm` | `bool \| None` | `None` (ROCm only) |
| `fuse_rope_kvcache` | `bool \| None` | `None` (ROCm only) |
| `rope_kvcache_fusion_max_token_num` | `int` | `256` |
| `fi_allreduce_fusion_max_size_mb` | `float \| None` | `None` |
| `sp_min_token_num` | `int \| None` | `None` |

**Nested fields (`DynamicShapesConfig`, set via `dynamic_shapes_config` key):**

| Sub-field | Type | Default |
| --- | --- | --- |
| `type` | `"backed" \| "unbacked" \| "backed_size_oblivious"` | `"backed"` |
| `evaluate_guards` | `bool` | `False` |
| `assume_32_bit_indexing` | `bool` | `False` |

## KernelConfig

> Section description (from log):

```text
  Configuration for kernel selection and warmup behavior.
```

| Name | Type | Default | Choices | Description |
| --- | --- | --- | --- | --- |
| --enable-flashinfer-autotune | Boolean flag | None | N/A | If True, run FlashInfer autotuning during kernel<br>warmup. |
| --no-enable-flashinfer-autotune | Boolean flag | None | N/A | If True, run FlashInfer autotuning during kernel<br>warmup. |
| --ir-op-priority | N/A | IrOpPriorityConfig(rms_norm=[],<br>fused_add_rms_norm=[]) | N/A | vLLM IR op priority for dispatching/lowering during<br>the forward pass. Platform defaults appended<br>automatically during VllmConfig.__post_init__.<br>API docs: https://docs.vllm.ai/en/latest/api/vllm/conf<br>ig/#vllm.config.IrOpPriorityConfig<br>Should either be a valid JSON string or JSON keys<br>passed individually. |
| --linear-backend | Enum | auto | aiter,auto,conch,cutlass,deep_gemm,emulation,exllama,fbgemm,flashinfer_cudnn,flashinfer_cutlass,flashinfer_trtllm,machete,marlin,torch,triton | Backend for quantized linear layer GEMM kernels.<br>Available options:<br>- "auto": Automatically select the best backend based<br>on model and hardware<br>- "cutlass": Use CUTLASS-based kernels<br>- "flashinfer_cutlass": Use FlashInfer with CUTLASS<br>kernels<br>- "flashinfer_trtllm": Use FlashInfer with TensorRT-<br>LLM kernels<br>- "flashinfer_cudnn": Use FlashInfer with cuDNN<br>kernels<br>- "marlin": Use Marlin kernels<br>- "triton": Use Triton-based kernels<br>- "deep_gemm": Use DeepGEMM kernels<br>- "torch": Use PyTorch native scaled_mm kernels<br>- "aiter": Use AMD AITer kernels (ROCm only)<br>- "machete": Use Machete kernels (mixed-precision)<br>- "fbgemm": Use FBGEMM kernels<br>- "conch": Use Conch mixed-precision kernels<br>- "exllama": Use Exllama mixed-precision kernels<br>- "emulation": Use slow dequant-to-BF16 emulation (for<br>testing only) |
| --moe-backend | Enum | auto | aiter,auto,cutlass,deep_gemm,deep_gemm_mega_moe,emulation,flashinfer_b12x,flashinfer_cutedsl,flashinfer_cutlass,flashinfer_trtllm,humming,marlin,triton,triton_unfused | Backend for MoE expert computation kernels. Available<br>options:<br>- "auto": Automatically select the best backend based<br>on model and hardware<br>- "triton": Use Triton-based fused MoE kernels<br>- "deep_gemm": Use DeepGEMM kernels (FP8 block-<br>quantized only)<br>- "deep_gemm_mega_moe": Use DeepGEMM mega MoE kernels<br>- "cutlass": Use vLLM CUTLASS kernels<br>- "flashinfer_trtllm": Use FlashInfer with TRTLLM-GEN<br>kernels<br>- "flashinfer_cutlass": Use FlashInfer with CUTLASS<br>kernels<br>- "flashinfer_cutedsl": Use FlashInfer with CuteDSL<br>kernels (FP4 only)<br>- "flashinfer_b12x": Use FlashInfer CuteDSL fused MoE<br>for SM12x (RTX Pro 6000 / DGX Spark)<br>- "marlin": Use Marlin kernels (weight-only<br>quantization)<br>- "humming": Use Humming Mixed Precision kernels<br>- "triton_unfused": Use Triton unfused MoE kernels<br>- "aiter": Use AMD AITer kernels (ROCm only)<br>- "emulation": use BF16/FP16 GEMM, dequantizing<br>weights and running QDQ on activations. |

**Nested fields (`KernelConfig`):**

| Sub-field | Type | Default |
| --- | --- | --- |
| `ir_op_priority` | `IrOpPriorityConfig` | see below |
| `enable_flashinfer_autotune` | `bool \| None` | `None` |
| `moe_backend` | `MoEBackend` | `"auto"` |
| `linear_backend` | `LinearBackend` | `"auto"` |

**Nested fields (`IrOpPriorityConfig`, set via `ir_op_priority` key):**

| Sub-field | Type | Default |
| --- | --- | --- |
| `rms_norm` | `list[str]` | `[]` |
| `fused_add_rms_norm` | `list[str]` | `[]` |

## VllmConfig

> Section description (from log):

```text
  Dataclass which contains all vllm-related configuration. This
      simplifies passing around the distinct configurations in the codebase.
```

| Name | Type | Default | Choices | Description |
| --- | --- | --- | --- | --- |
| --additional-config | N/A | {} | N/A | Additional config for specified platform. Different<br>platforms may support different configs. Make sure the<br>configs are valid for the platform you are using.<br>Contents must be hashable. |
| --attention-config | N/A | AttentionConfig(backend=None, flash_attn_version=None,<br>use_prefill_decode_attention=False,<br>flash_attn_max_num_splits_for_cuda_graph=32,<br>tq_max_kv_splits_for_cuda_graph=32,<br>use_trtllm_attention=None,<br>disable_flashinfer_q_quantization=False,<br>mla_prefill_backend=None,<br>use_prefill_query_quantization=False,<br>use_fp4_indexer_cache=False, use_non_causal=False,<br>flex_attn_block_m=None, flex_attn_block_n=None,<br>flex_attn_q_block_size=None,<br>flex_attn_kv_block_size=None) | N/A | Attention configuration.<br>API docs: https://docs.vllm.ai/en/latest/api/vllm/conf<br>ig/#vllm.config.AttentionConfig<br>Should either be a valid JSON string or JSON keys<br>passed individually. |
| --compilation-config | N/A | {'mode': None,<br>'debug_dump_path': None, 'cache_dir': '',<br>'compile_cache_save_format': 'binary', 'backend': 'vll<br>m_ascend.compilation.compiler_interface.AscendCompiler<br>', 'custom_ops': [], 'ir_enable_torch_wrap': None,<br>'splitting_ops': None, 'compile_mm_encoder': False,<br>'cudagraph_mm_encoder': False,<br>'encoder_cudagraph_token_budgets': [],<br>'encoder_cudagraph_max_vision_items_per_batch': 0,<br>'encoder_cudagraph_max_frames_per_batch': None,<br>'compile_sizes': None, 'compile_ranges_endpoints':<br>None, 'inductor_compile_config':<br>{'enable_auto_functionalized_v2': False,<br>'size_asserts': False, 'alignment_asserts': False,<br>'scalar_asserts': False, 'combo_kernels': True,<br>'benchmark_combo_kernel': True}, 'inductor_passes':<br>{}, 'cudagraph_mode': None,<br>'cudagraph_num_of_warmups': 0,<br>'cudagraph_capture_sizes': None,<br>'cudagraph_copy_inputs': False,<br>'cudagraph_specialize_lora': True,<br>'use_inductor_graph_partition': None, 'pass_config':<br>{}, 'max_cudagraph_capture_size': None,<br>'dynamic_shapes_config': {'type':<br><DynamicShapesType.BACKED: 'backed'>,<br>'evaluate_guards': False, 'assume_32_bit_indexing':<br>False}, 'local_cache_dir': None,<br>'fast_moe_cold_start': None, 'static_all_moe_layers':<br>[]} | N/A | `torch.compile` and cudagraph capture configuration<br>for the model.<br>As a shorthand, one can append compilation arguments<br>via<br>-cc.parameter=argument such as `-cc.mode=3` (same as<br>`-cc='{"mode":3}'`).<br>You can specify the full compilation config like so:<br>`{"mode": 3, "cudagraph_capture_sizes": [1, 2, 4, 8]}`<br>API docs: https://docs.vllm.ai/en/latest/api/vllm/conf<br>ig/#vllm.config.CompilationConfig<br>Should either be a valid JSON string or JSON keys<br>passed individually. |
| --ec-transfer-config | N/A | None | N/A | The configurations for distributed EC cache transfer.<br>API docs: https://docs.vllm.ai/en/latest/api/vllm/conf<br>ig/#vllm.config.ECTransferConfig<br>Should either be a valid JSON string or JSON keys<br>passed individually. |
| --kernel-config | N/A | KernelConfig(ir_op_prio<br>rity=IrOpPriorityConfig(rms_norm=[],<br>fused_add_rms_norm=[]),<br>enable_flashinfer_autotune=None, moe_backend='auto',<br>linear_backend='auto') | N/A | Kernel configuration.<br>API docs: https://docs.vllm.ai/en/latest/api/vllm/conf<br>ig/#vllm.config.KernelConfig<br>Should either be a valid JSON string or JSON keys<br>passed individually. |
| --kv-events-config | N/A | None | N/A | The configurations for event publishing.<br>API docs: https://docs.vllm.ai/en/latest/api/vllm/conf<br>ig/#vllm.config.KVEventsConfig<br>Should either be a valid JSON string or JSON keys<br>passed individually. |
| --kv-transfer-config | N/A | None | N/A | The configurations for distributed KV cache transfer.<br>API docs: https://docs.vllm.ai/en/latest/api/vllm/conf<br>ig/#vllm.config.KVTransferConfig<br>Should either be a valid JSON string or JSON keys<br>passed individually. |
| --optimization-level | N/A | 2 | N/A | The optimization level. These levels trade startup<br>time cost for performance, with -O0 having the best<br>startup time and -O3 having the best performance. -O2<br>is used by default. See OptimizationLevel for full<br>description. |
| --performance-mode | Enum | balanced | balanced,interactivity,throughput | Performance mode for runtime behavior, 'balanced' is<br>the default. 'interactivity' favors low end-to-end<br>per-request latency at small batch sizes (fine-grained<br>CUDA graphs, latency-oriented kernels). 'throughput'<br>favors aggregate tokens/sec at high concurrency<br>(larger CUDA graphs, more aggressive batching,<br>throughput-oriented kernels). |
| --profiler-config | N/A | ProfilerConfig(profiler=None, torch_profiler_dir='',<br>torch_profiler_with_stack=True,<br>torch_profiler_with_flops=False,<br>torch_profiler_use_gzip=True,<br>torch_profiler_dump_cuda_time_total=True,<br>torch_profiler_record_shapes=False,<br>torch_profiler_with_memory=False,<br>ignore_frontend=False, delay_iterations=0,<br>max_iterations=0, warmup_iterations=0,<br>active_iterations=5, wait_iterations=0) | N/A | Profiling configuration.<br>API docs: https://docs.vllm.ai/en/latest/api/vllm/conf<br>ig/#vllm.config.ProfilerConfig<br>Should either be a valid JSON string or JSON keys<br>passed individually. |
| --reasoning-config | N/A | None | N/A | The configurations for reasoning model.<br>API docs: https://docs.vllm.ai/en/latest/api/vllm/conf<br>ig/#vllm.config.ReasoningConfig<br>Should either be a valid JSON string or JSON keys<br>passed individually. |
| --spec-method | Enum | None | custom_class,deepseek_mtp,dflash,draft_model,eagle,eagle3,ernie_mtp,exaone4_5_mtp,exaone_moe_mtp,extract_hidden_states,gemma4_mtp,glm4_moe_lite_mtp,glm4_moe_mtp,glm_ocr_mtp,hy_v3_mtp,longcat_flash_mtp,medusa,mimo_mtp,mimo_v2_mtp,mlp_speculator,mtp,nemotron_h_mtp,ngram,ngram_gpu,pangu_ultra_moe_mtp,qwen3_5_mtp,qwen3_next_mtp,step3p5_mtp,suffix,None | The name of the speculative method to use. If users<br>provide and set the `model` param, the speculative<br>method type will be detected automatically if<br>possible, if `model` param is not provided, the method<br>name must be provided.<br>If using `ngram` method, the related configuration<br>`prompt_lookup_max` and `prompt_lookup_min` should be<br>considered. |
| --spec-model | N/A | None | N/A | The name of the draft model, eagle head, or additional<br>weights, if provided. |
| --spec-tokens | N/A | None | N/A | The number of speculative tokens, if provided. It will<br>default to the number in the draft model config if<br>present, otherwise, it is required. |
| --speculative-config | N/A | None | N/A | Speculative decoding configuration.<br>API docs: https://docs.vllm.ai/en/latest/api/vllm/conf<br>ig/#vllm.config.SpeculativeConfig<br>Should either be a valid JSON string or JSON keys<br>passed individually. |
| --structured-outputs-config | N/A | StructuredOutputsConfig(backend='auto',<br>disable_any_whitespace=False,<br>disable_additional_properties=False,<br>reasoning_parser='', reasoning_parser_plugin='',<br>enable_in_reasoning=False) | N/A | Structured outputs configuration.<br>API docs: https://docs.vllm.ai/en/latest/api/vllm/conf<br>ig/#vllm.config.StructuredOutputsConfig<br>Should either be a valid JSON string or JSON keys<br>passed individually. |
| --weight-transfer-config | N/A | None | N/A | The configurations for weight transfer during RL<br>training.<br>API docs: https://docs.vllm.ai/en/latest/api/vllm/conf<br>ig/#vllm.config.WeightTransferConfig<br>Should either be a valid JSON string or JSON keys<br>passed individually. |

**Nested fields (`ECTransferConfig`):**

| Sub-field | Type | Default |
| --- | --- | --- |
| `ec_connector` | `str \| None` | `None` |
| `ec_buffer_device` | `str \| None` | `"cuda"` |
| `ec_buffer_size` | `float` | `1e9` |
| `ec_role` | `ECRole \| None` | `None` |
| `ec_rank` | `int \| None` | `None` |
| `ec_parallel_size` | `int` | `1` |
| `ec_ip` | `str` | `"127.0.0.1"` |
| `ec_port` | `int` | `14579` |
| `ec_connector_extra_config` | `dict[str, Any]` | `{}` |
| `ec_connector_module_path` | `str \| None` | `None` |

**Nested fields (`KVEventsConfig`):**

| Sub-field | Type | Default |
| --- | --- | --- |
| `enable_kv_cache_events` | `bool` | `False` |
| `publisher` | `"null" \| "zmq"` | `None` (post_init: `"zmq"` if events enabled, else `"null"`) |
| `endpoint` | `str` | `"tcp://*:5557"` |
| `replay_endpoint` | `str \| None` | `None` |
| `buffer_steps` | `int` | `10000` |
| `hwm` | `int` | `100000` |
| `max_queue_size` | `int` | `100000` |
| `topic` | `str` | `""` |

**Nested fields (`KVTransferConfig`):**

| Sub-field | Type | Default |
| --- | --- | --- |
| `kv_connector` | `str \| None` | `None` |
| `kv_buffer_device` | `str` | platform device type |
| `kv_buffer_size` | `float` | `1e9` |
| `kv_role` | `KVRole \| None` | `None` |
| `kv_rank` | `int \| None` | `None` |
| `kv_parallel_size` | `int` | `1` |
| `kv_ip` | `str` | `"127.0.0.1"` |
| `kv_port` | `int` | `14579` |
| `kv_connector_extra_config` | `dict[str, Any]` | `{}` |
| `kv_connector_module_path` | `str \| None` | `None` |
| `enable_permute_local_kv` | `bool` | `False` |
| `kv_load_failure_policy` | `"recompute" \| "fail"` | `"fail"` |

**Nested fields (`ProfilerConfig`):**

| Sub-field | Type | Default |
| --- | --- | --- |
| `profiler` | `ProfilerKind \| None` | `None` |
| `torch_profiler_dir` | `str` | `""` |
| `torch_profiler_with_stack` | `bool` | `True` |
| `torch_profiler_with_flops` | `bool` | `False` |
| `torch_profiler_use_gzip` | `bool` | `True` |
| `torch_profiler_dump_cuda_time_total` | `bool` | `True` |
| `torch_profiler_record_shapes` | `bool` | `False` |
| `torch_profiler_with_memory` | `bool` | `False` |
| `ignore_frontend` | `bool` | `False` |
| `delay_iterations` | `int` | `0` |
| `max_iterations` | `int` | `0` |
| `warmup_iterations` | `int` | `0` |
| `active_iterations` | `int` | `5` |
| `wait_iterations` | `int` | `0` |

**Nested fields (`ReasoningConfig`):**

| Sub-field | Type | Default |
| --- | --- | --- |
| `reasoning_parser` | `str` | `""` |
| `reasoning_start_str` | `str` | `""` |
| `reasoning_end_str` | `str` | `""` |

**Nested fields (`SpeculativeConfig`):**

| Sub-field | Type | Default |
| --- | --- | --- |
| `num_speculative_tokens` | `int` | required |
| `model` | `str \| None` | `None` |
| `method` | `SpeculativeMethod \| None` | `None` |
| `draft_tensor_parallel_size` | `int \| None` | `None` |
| `quantization` | `str \| None` | `None` |
| `moe_backend` | `MoEBackend \| None` | `None` |
| `attention_backend` | `AttentionBackendEnum \| None` | `None` |
| `max_model_len` | `int \| None` | `None` |
| `revision` | `str \| None` | `None` |
| `code_revision` | `str \| None` | `None` |
| `disable_padded_drafter_batch` | `bool` | `False` |
| `use_local_argmax_reduction` | `bool` | `False` |
| `prompt_lookup_max` | `int \| None` | `None` |
| `prompt_lookup_min` | `int \| None` | `None` |
| `parallel_drafting` | `bool` | `False` |
| `rejection_sample_method` | `str` | `"standard"` |
| `synthetic_acceptance_rates` | `list[float] \| None` | `None` |
| `synthetic_acceptance_length` | `float \| None` | `None` |
| `suffix_decoding_max_tree_depth` | `int` | `24` |
| `suffix_decoding_max_cached_requests` | `int` | `10000` |
| `suffix_decoding_max_spec_factor` | `float` | `1.0` |
| `suffix_decoding_min_token_prob` | `float` | `0.1` |

**Nested fields (`StructuredOutputsConfig`):**

| Sub-field | Type | Default |
| --- | --- | --- |
| `backend` | `StructuredOutputsBackend` | `"auto"` |
| `disable_any_whitespace` | `bool` | `False` |
| `disable_additional_properties` | `bool` | `False` |
| `reasoning_parser` | `str` | `""` |
| `reasoning_parser_plugin` | `str` | `""` |
| `enable_in_reasoning` | `bool` | `False` |

**Nested fields (`WeightTransferConfig`):**

| Sub-field | Type | Default |
| --- | --- | --- |
| `backend` | `"nccl" \| "ipc" \| str` | `"nccl"` |


---