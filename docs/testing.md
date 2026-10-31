# Tests

English | [繁體中文](testing.zh-TW.md) · [Back to the README](../README.md)

```bash
just test               # uv run pytest: about 40 s; loads no weights and touches no network
just lint               # uv run ruff check: likely bugs, unused imports and the order of imports (just lint --fix sorts them)
just types              # uv run mypy: agent/, app/ and docs/ inside every function, tests/ where annotated
just guide-check        # How it works' tests and build with pygments alone, as checks.yml and pages.yml run them: the two commands below
just check              # what checks.yml runs: just lint, just types, just test, then just guide-check
just test-models        # RUN_MODEL_TESTS=1 uv run pytest tests/test_real_model.py: the real Gemma (with its MTP drafter) and Qwen, about 4 minutes
just test-vllm          # VLLM_TEST_URL=http://localhost:8000 uv run pytest tests/test_vllm_backend.py -k real_server: asks a running vLLM server
just test-vllm-docker   # RUN_VLLM_DOCKER_TESTS=1 uv run pytest tests/test_vllm_docker.py -k real: starts vLLM in Docker with Qwen3.5 and asks it
just test-pi            # RUN_PI_TESTS=1 uv run pytest tests/test_pi_harness.py -k real: the real pi (on the PATH, or PI_COMMAND) against a scripted model on 127.0.0.1, and against the model endpoint
```

Each recipe runs the command after it, so without [just](setup.md#the-commands-by-name) you can type that instead; `just guide-check` runs two:

```bash
uv run --isolated --no-project --with pygments --with pytest pytest tests/test_guide.py
uv run --isolated --no-project --with pygments python -m docs.guide _site
```

What follows a name goes to the command (`just test -k render`, `just test-models -k Qwen` for Qwen alone); `just test-vllm` takes another server's address, if not localhost:8000.

Most tests use the fake model in `tests/fakes.py`: it replays scripted output one token at a time and is a `Backend` (`backend.py`) like `SimpleBackend`, so the harness and the page run from start to finish. In pi's place they start `tests/fake_pi.py`, which speaks pi 1.4's RPC protocol from a script, so they need neither Node nor a model.

Every file format the page accepts has a test: `tests/samples.py` makes a small file of each one from the examples' files (the receipt in every image format, the recording in every audio format, the rolling ball in every video container, the sales data in every data format). `test_media.py` fails if `media.py` accepts a format without a sample, and `test_real_model.py` asks both models about each one. The tests that need Docker run only when Docker and the sandbox image are there.

On every pull request and every push to main, `.github/workflows/checks.yml` runs `ruff check`, `mypy` and `uv run pytest` on Ubuntu; the tests that need the models, the sandbox image, a vLLM server or pi skip there. Beside them it runs `tests/test_guide.py` and builds How it works with pygments alone, as `pages.yml` does on main, so a pull request that has the page's code import torch or the rest of the app fails before it is merged, not when the page is published.

How it works quotes code, and `tests/guide_excerpts.txt` keeps everything it quotes, without line numbers. When a change touches quoted code, `test_guide.py` fails and names the sections that quote it: reread them, fix what they say if it is no longer true, then rewrite the file with `just guide-snapshot` (`UPDATE_GUIDE_SNAPSHOT=1 uv run pytest tests/test_guide.py`).

## What each file covers

The test names are sentences about behavior, so a file's test names say in full what it checks.

| File | What it tests |
|---|---|
| `test_gemma4.py` | Gemma 4's parser: splitting thinking, tool calls and the reply; `<\|"\|>` strings, nested arguments, all kinds of format errors, in both languages |
| `test_qwen3_5.py` | Qwen3.5's parser: XML tool calls, types from the schema, thinking, all kinds of format errors; a whole harness run in Qwen's format |
| `test_model_families.py` | Every family explains its special tokens and the files of its checkpoints, the same in both languages; `model_type` finds the family; tokens show as the text they stand for; every model and drafter downloads at a pinned commit; vLLM drafts with the MTP layer in a checkpoint or the drafter transformers uses |
| `test_tools.py` | Schema validation, the calculator's AST allowlist, timezones, Wikipedia (faked); `run_python`'s locked-down `docker run`, its errors and its charts, in both languages; with Docker, the real sandbox: `/data` read-only, no network, every data format, charts with Chinese labels |
| `test_simple_backend.py` | The hand-written decoding loop: KV cache, stop tokens, limits, interruption, channel switches, characters split across tokens, ties broken as `generate()` does, temperature / top-k / top-p; media through the processor and the vision encoder; MTP with a scripted drafter, keeping the distribution when sampling; models at their pinned revision in `models/`; on CUDA, cuBLAS's workspaces freed before CUDA's cache is emptied |
| `test_simple_harness.py` | The harness: event order, tool results back in the context, validation errors, repeated calls, every stop reason, Allow / Reject / Stop; errors in the turn's language; attachments and the note for `run_python`; charts for the page, not the model |
| `test_pi_harness.py` | pi as the harness, with `tests/fake_pi.py` in its place: a turn becomes the page's events; pi started in the conversation's folder, with the sidebar's tools and without the user's extensions; asking first through the extension; Stop and the step limit; failures said in both languages; the page's model through the endpoint; with `RUN_PI_TESTS=1`, the real pi |
| `test_model_endpoint.py` | The page's model served to pi over HTTP: only on 127.0.0.1, only with its token, one request at a time; replies, thinking and tool calls in the OpenAI format; each request drawn as its step; the conversation kept as `SimpleHarness` keeps it |
| `test_render.py` | Every prefix of a run's events renders in both languages (the page redraws mid-run), HTML tags pair up, the diagram is valid SVG, model output is always escaped; token popovers, MTP's marks, media chips, charts, the model folder card; backends that report less; runs pi ran; no Chinese on an English page |
| `test_app.py` | The whole page through Streamlit's `AppTest`: questions, examples, the sidebar's settings, the tabs, Allow / Reject / Stop, new chats, model switches, one run at a time across tabs, the language switch, attachments and the sandbox; with `VLLM_URL`, a server's models, flags, media and errors; vLLM in Docker started, joined, switched and stopped; pi on either kind of model |
| `test_chat_template.py` | With each model's real tokenizer and chat template (only when downloaded into `models/`): every special token is a single token with a note, tool calls in the history parse back, and what the step card marks as new is exactly the tool result, with media too; every file in a model's folder has a note |
| `test_vllm_backend.py` | The vLLM backend against a fake server that speaks vLLM 0.32's streams: the prompt's exact token ids and settings; probabilities, ranks and the top 5 on each route; sampling masks and the `--logprobs-mode` found at load; media and their expansion; MTP's counts and marks; errors in both languages; which family a served model is of; with the real tokenizers, the exact prompt; with `VLLM_TEST_URL`, a real server |
| `test_vllm_docker.py` | vLLM in Docker, with Docker faked at the level of `subprocess`: weights downloaded first, `docker compose up` with the right files, a server reused or replaced, every failure said in both languages, `docker compose down` on a switch and at exit, MTP on a GPU only; the compose files on 127.0.0.1, read-only and offline; with `RUN_VLLM_DOCKER_TESTS=1`, the real server |
| `test_media.py` | Every format the page accepts has a sample and is read as what it is (sound is a file for Qwen) and decodes; names saved distinct and plain; the question's parts and the note naming a text file's columns; photos turned upright, sound at the model's rate, a video's frames evenly spaced |
| `test_guide.py` | Every excerpt and line number on How it works resolves and links to its lines on GitHub at the page's commit; the event table points at the line that sends each event; the quoted code matches `tests/guide_excerpts.txt`; both languages point at the same code; tabs switch without a script; the built pages have both palettes and send readers to their language |
| `test_layout.py` | No file in `agent/` imports `app` or Streamlit, at the top or inside a function, read from each file's syntax tree: the agent never knows the app |
| `test_real_model.py` | Skipped by default. For each model: greedy decoding matches `model.generate()`, with text and with media; the real model calls a tool, reads the receipt, hears the recording (Gemma), sees which way the ball rolls and opens every data format; Gemma's MTP keeps greedy output the same; on CUDA all GPU memory comes back; with pi installed, the real pi asks the model through the endpoint |
