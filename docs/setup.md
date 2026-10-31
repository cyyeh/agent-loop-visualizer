# Setup in detail

English | [繁體中文](setup.zh-TW.md) · [Back to the README](../README.md)

The README's [Quick start](../README.md#quick-start) runs the recipes in the `justfile`; this page says what they need, what happens when they run, and [the command behind each](#the-commands-by-name), for a machine without just.

## Requirements

- macOS (Apple Silicon, using MPS), Linux with CUDA, or a CPU alone (very slow)
- Disk space for the weights: about 10 GB for Gemma 4 E2B, 1.8 GB for Qwen3.5 0.8B, and about 190 MB more for Gemma's drafter if you want MTP
- Memory: with MPS or CUDA, 16 GB or more for Gemma (the bfloat16 weights take about 10 GB); on a CPU it loads in float32, about 20.5 GB, so 24 GB or more. Qwen3.5 0.8B is much smaller and runs on an 8 GB machine. Only one model is loaded at a time; switching models lets the old one go
- Linux + CUDA: the pinned torch is built for CUDA 13, so the CUDA Version at the top right of `nvidia-smi` must be 13.0 or newer. With an older driver torch does not see the GPU and runs on the CPU; the top of the sidebar shows the device in use
- [uv](https://docs.astral.sh/uv/) 0.13.4 or newer (it installs Python 3.12 for you). Older versions still trust eMudhra's compromised emSign certificates ([the announcement](https://discuss.python.org/t/109576)), so `uv sync` refuses to run with them; `uv self update` (or `brew upgrade uv`) updates it
- [just](https://github.com/casey/just#installation) (`brew install just`, or the package manager its installation page names for your system), to run the commands by name. Each recipe runs a command or two, so without just you can type those instead ([below](#the-commands-by-name))
- A network connection: to download the models the first time, and for the Wikipedia tools
- Optional: [Docker](https://docs.docker.com/get-started/get-docker/) (Docker Desktop, OrbStack or Colima), only to let the model write code or to run it on vLLM (Docker)
- Optional: [pi](https://pi.dev) and Node.js 22.19 or newer, only to hand the loop to pi ([pi as the harness](pi.md))

## When the app starts

Your browser opens http://localhost:8501, in its own language (English unless the browser is set to Chinese); the 中文 | English switch at the top right changes it, and the next visit starts in the one you picked. Loading Gemma and warming it up takes about 10–20 seconds the first time, Qwen a few seconds; reloading the page does not load it again. The Model menu at the top of the sidebar switches models; switching starts a new conversation, resets the decoding settings to the new model's recommendations and turns MTP off. MTP speculative decoding in the sidebar loads the drafter the first time it is switched on (in under a second), and it stays in memory after that.

## Where the models go

The models download into `models/` in the project folder, which git ignores, not into the `~/.cache/huggingface/hub` other projects share; deleting the folder frees the space. Each downloads at a fixed revision, the commit in `REVISIONS` in `agent/model_families/__init__.py` (the `--revision` of the `hf download` lines [below](#the-commands-by-name)), so whenever you download it you get the files the app was written and tested against, the same on every operating system. To keep them somewhere else, set `AGENT_LOOP_MODELS` to that folder (`just download` downloads there too; give `hf download` the same `--cache-dir`); `AGENT_LOOP_MODELS=$HOME/.cache/huggingface/hub` uses the models already downloaded there. `HF_HUB_CACHE` does not move them, since it is often set once for every project on a machine.

## Let the model write code

Let the model write code in the sidebar is off by default, and while it is off (and vLLM (Docker) is not picked) the page never looks for Docker. Switched on, it checks for Docker and the `agent-loop-sandbox` image, and if either is missing, or the image was built from an older `agent/sandbox/Dockerfile`, it says in the sidebar how to install Docker or build the image; the model gets `run_python` only once both are there, and the examples that need Python, which appear once it is on, can be pressed only then. Files you attach are saved in a folder per conversation under `~/.cache/agent-loop-visualizer/uploads/` (New chat removes it), which the sandbox sees, read-only, as `/data`. How the sandbox works is in [Attachments and the code sandbox](files.md#writing-code-in-a-docker-sandbox).

## The commands by name

The `justfile` gives names to the commands in the README and in these pages, for [just](https://github.com/casey/just): `just` lists them, and `just <name>` runs one from the project's folder, wherever you are in it. Each runs a command or two, given beside it or right after the block, so without just you can type those instead. The environment reaches them as it reaches those commands, and what follows a name goes to the command:

```bash
just sync                            # uv sync
just download                        # every model and drafter in REVISIONS at its pinned commit, into models/ (or AGENT_LOOP_MODELS): about 12 GB
just download Qwen/Qwen3.5-0.8B      # only the ones named
just run                             # uv run streamlit run streamlit_app.py; MODEL_ID=Qwen/Qwen3.5-0.8B just run loads Qwen first, VLLM_URL=http://localhost:8000 just run asks that server
just sandbox                         # docker build -t agent-loop-sandbox agent/sandbox
just check                           # what checks.yml runs on a pull request: just lint, just types, just test, then just guide-check (in Tests)
just guide                           # uv run python -m docs.guide _site: How it works, built into _site/
just vllm-up                         # vLLM in Docker by hand, on the CPU (just vllm-up gpu on NVIDIA GPUs); just vllm-down stops it; their docker compose commands are in vLLM in Docker
```

The tests' recipes are in [Tests](testing.md), and the `docker compose` commands behind `just vllm-up` and `just vllm-down` in [vLLM in Docker](vllm.md#vllm-in-docker-started-by-the-page). `just download` reads the commits from `REVISIONS` in `agent/model_families/__init__.py`, so it keeps downloading the files the app was tested against when a model moves to a newer commit. Without just, it is, at the commits pinned today:

```bash
uv run hf download google/gemma-4-E2B-it --revision 3e22461f65e89153144f8adb70e3b8c2cc9845a7 --cache-dir models   # about 10 GB
uv run hf download Qwen/Qwen3.5-0.8B --revision 2fc06364715b967f1860aea9cf38778875588b17 --cache-dir models       # about 1.8 GB
uv run hf download google/gemma-4-E2B-it-assistant --revision 2d874ef7d29f9a30599a1e4b3c1cbc9595f005df --cache-dir models   # Gemma's MTP drafter, about 190 MB
```

A model left undownloaded downloads the first time it is picked, and the drafter the first time MTP is switched on.

## Troubleshooting

A 401 while downloading, though the model is public? Most likely the Hugging Face token saved on your machine has expired. Log in again (`uv run hf auth login`), or add `HF_HUB_DISABLE_IMPLICIT_TOKEN=1` to send no token.
