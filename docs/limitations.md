# Known limitations

English | [繁體中文](limitations.zh-TW.md) · [Back to the README](../README.md)

## Speed and MTP

- Speed: on an Apple M5 (32 GB), Gemma runs at about 7–13 tok/s and Qwen3.5 0.8B at about 20–25 tok/s. In thinking mode a step often has two or three hundred thinking tokens, about 30 seconds of waiting. With MTP on, easily guessed steps such as tool calls are about 3× faster, and long Chinese text barely changes (see [the table under MTP speculative decoding](decoding.md#mtp-speculative-decoding)).
- With long replies in the page, MTP speeds things up much less than in `simple_backend.py` alone (English code: 8 → 29 tok/s alone, 9 → 12 tok/s in the page), for reasons not yet pinned down. Perhaps the page redrawing every 0.5 s and the browser competing with the model for the same machine slow MTP down more than plain decoding, since each MTP round has several small drafter forward passes.
- With transformers only Gemma 4 E2B can use MTP: `transformers` supports a drafter reading the model's KV cache this way only for Gemma 4, and Qwen3.5 has no matching drafter. On a vLLM server with a GPU, Qwen3.5 can too, with the MTP layer in its own checkpoint (see [Running the model on vLLM](vllm.md)).
- With MTP on, the model computes 7 positions at once, which gives very slightly different numbers from computing 1; when two tokens are almost equally likely, greedy decoding may now and then pick the other one.
- 18 of Qwen3.5's 24 layers are Gated DeltaNet. transformers has two kernels to speed them up, `flash-linear-attention` (Triton) and `causal-conv1d` (CUDA). Both need a CUDA GPU, so neither is a dependency: the PyTorch reference implementation runs instead, with the same results, only slower, and `simple_backend.py` silences transformers' notice about that fallback on every device. With a GPU the difference is small for a 0.8B model. On an NVIDIA GB10 (DGX Spark), flash-linear-attention made prefill about 4× faster (3,571 tokens in 93 ms instead of 368 ms) but decoding barely changed (56 → 60 tok/s), and both paths stayed equally close to float32. causal-conv1d has no wheel for that machine and would have to be compiled. Don't install flash-linear-attention on a Linux machine without a GPU: transformers still picks it, and the first forward pass fails.
- On MPS, transformers hangs loading Qwen3.5's weights with several threads, so on MPS `simple_backend.py` loads with one thread (`HF_DEACTIVATE_ASYNC_LOAD=1`), which does not make either model load slower.

## The models

- Qwen3.5 0.8B has thinking off by default; on, it easily keeps thinking without stopping, and lowering Max tokens per step helps. It ships no generation_config.json, so its recommended decoding settings are in `agent/model_families/qwen3_5.py` (the presence penalty it recommends is not implemented here).
- Both models are small: they may answer in Simplified Chinese, repeat the same search, answer half the question or get their sums wrong while thinking. Asked in English about two cities' times at once, Gemma calls the tool twice and then usually answers in Chinese, or stops right after the tool results without a reply; asked about one city, it answers in English. All of that is material to look at.
- Only Gemma 4 E2B hears, and only the first 30 seconds of a clip. Neither model hears a video's sound: a video is frames. Each frame costs tokens: Gemma takes 32 frames of any video, about 2,000 tokens of prefill; Qwen two a second, so its count grows with the video's length (640 tokens for the 8-second example).
- In English with Use tools on, Gemma 4 E2B often says it cannot hear an attached recording, sometimes after writing its words into a tool call; asked in Chinese, or with Use tools off, it transcribes it. So the English recording example asks about what is said rather than for a transcription, which works about two times in three.
- Qwen3.5 0.8B opens every data format with `run_python` but rarely gets multi-step pandas code right; Gemma 4 E2B answers the sales example.
- The `MODEL_ID` environment variable picks the model selected at first; it may also name a checkpoint the menu does not list, as long as it belongs to a supported family (Gemma 4 or Qwen3.5); another family needs one added first, as in [Supporting more models](architecture.md#supporting-more-models).

## The page

- Only one model is kept in memory. If two tabs pick different models, using them in turn keeps reloading; it is best for every tab to use the same model.
- There is one copy of the model, so only one agent runs at a time and other tabs wait. Reloading or closing the tab during a run does not stop the agent; other tabs (including the reloaded one) show it is still running and offer a Stop that agent button.
- With Ask me before running a tool on, if no one answers within 5 minutes the harness takes it as a rejection and stops the loop, with "confirmation timed out" as the stop reason.
- Token popovers appear only once the step finishes generating; while it generates there are only the heat colors (special tokens still explain themselves), so each redraw does not send a lot of HTML. The popovers are pure CSS, and one for a token too near the bottom of the timeline may be cut off.
- Special token popovers are placed next to the token with CSS anchor positioning, so a scrolling box does not cut them off; browsers without it open them right under the token, where they may be cut off near the bottom of the box.
- In the chat, a clip plays back in the browser's own player; Safari cannot play an MKV video, so for one the chat shows four of the frames the model reads instead.
- Attachments are up to 50 MB each. They stay under `~/.cache/agent-loop-visualizer/uploads/` until New chat or a model switch; a closed tab leaves its folder behind.
- The Wikipedia tools need the network.

## The sandbox

- The sandbox has no network, so the model cannot `pip install`; it has numpy, pandas, openpyxl, tabulate and matplotlib. Each call is a new container, so nothing (variables, files in `/tmp`) carries over to the next call; only its charts, saved in the conversation's folder.
- The model never sees the charts it draws: they reach the page, not the context, so what it says about one comes from its own code and numbers. A chart saved with `plt.savefig()` and then closed is not sent; one shown or left open is.

## vLLM

- On a vLLM server (`VLLM_URL`) greedy output may differ from `generate()`'s, and what the page shows depends on the server's flags (see [What the page sees](vllm.md#what-the-page-sees)): without `--enable-scale-out` the model reads text only, and a token's popover has either the model's own probabilities and the top 5 (the default) or, with `--logprobs-mode processed_logprobs` (which `--return-sampling-mask` needs), the sampling probability and how many candidates were left, never both; which of the top 5 were cut never shows outside greedy decoding, and a server with sampling masks takes no greedy decoding or unlimited top-k. MTP's guesses are underlined only once the step is done, only when the server's counts account for every token, and without what a turned-down guess was. With media, each step asks the server for the expansion first, a second request that reads the prompt. The page cannot see which revision the server loaded, so start it with the `--revision` in [A server of your own](vllm.md#a-server-of-your-own).
- `vllm_backend.py` follows the protocols of vLLM 0.32, read from its source, and is tested against a fake server that speaks them, with the real tokenizers and in the real page; `/inference/v1/generate` and its sampling masks and per-step counts are marked experimental in vLLM and may change. Its tests against a real server (`VLLM_TEST_URL`) have been run on one GPU only, a DGX Spark's GB10.
- vLLM in Docker runs on the CPU on a Mac, and slowly: Gemma 4 E2B decodes about 4.6 tok/s, needs Docker to have about 20 GB of memory or more, and its first load spends about 10 minutes running its media encoders to see which kinds the server takes. `compose.gpu.yaml` has been run on one NVIDIA GPU only, a DGX Spark's GB10. The CPU image patches vLLM 0.32.0 (`docker-compose/vllm-cpu/patch_vllm.py`); a newer vLLM may need neither fix, and the build stops if the code it patches is not the one it was written for.
- The app stops vLLM's container when it quits with Ctrl+C or a SIGTERM. Stopped any other way (its terminal closed, `kill -9`), it leaves the container running and holding the model; `docker compose -p agent-loop-vllm down` (`just vllm-down`) stops it.

## pi

- With pi on its own models, the page sees only what pi reports: no tokens, probabilities or special tokens, and not the string the model reads, only the request pi sends. The token counts are the provider's, tok/s is measured as the reply arrives (the network included), and the cost is at the prices in pi's catalog, an estimate. pi's own models are a provider's: they cost money, and the conversation goes to that provider.
- With pi on the page's model, a tool call the family cannot parse is not sent to pi, and pi's turn ends there: unlike the built-in harness, nothing tells the model what it wrote wrong. pi's system prompt and tool schemas are written for large models; Gemma 4 E2B and Qwen3.5 0.8B follow them less well than the built-in harness's prompt. pi sends images alone of the media, so audio and video attached for pi are plain files in its folder. A request that comes outside every step (pi compacting a long conversation, say) waits up to 10 seconds for one, then is answered without being drawn.
- pi's tools run on this computer, without a sandbox; with bash on, the model can do whatever you can. Ask me before running a tool shows each call first.
- `pi_harness.py` follows pi 1.4's RPC protocol, from its documentation and the records pi 1.4.0 sends; the real-pi tests have been run with pi 1.4.0 only. pi 1.4 needs Node.js 22.19 or newer: under an older Node it does not start, and the page shows what it said. The page asks pi which models it has at most once a minute; after logging in to a provider in pi, Try again lists them.
