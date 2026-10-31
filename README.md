<img src="app/assets/logo.svg" alt="" width="72">

# Agent Loop Visualizer

English | [繁體中文](README.zh-TW.md)

![The top bar links to the How it works page, the switch at the top right changes the language, and the sidebar picks what runs the loop (the built-in harness or pi), the model and what runs it; on the left is the chat, with the sample files to ask about above the input box, on the right the loop diagram and the tokens of step 1. The pointer rests on the special token <|tool_call>, whose popover says what it is for and shows its probability, its rank and the top 5 candidates.](docs/screenshot-en.png)

This project is for learning: it shows how an agent loop works underneath, in a way more intuitive and visual than reading about it. Behind an agent's chat box runs a loop: step after step, the model proposes an action and the harness carries it out, until it stops. A chat app shows only the question and the answer; this page draws every step as it happens, down to each token the model writes, so the whole mechanism is laid out in front of you. Each part of the page matches a section of the Unit 01 reading of [Agent Atlas](https://agentic-system-lab.github.io/agent-atlas-learning/) (in Traditional Chinese), the course this project belongs to ([What the page shows](docs/page.md) says which), and [Experiments to try](#experiments-to-try) turns those ideas into things you can try yourself.

- **Models**: [google/gemma-4-E2B-it](https://huggingface.co/google/gemma-4-E2B-it) or [Qwen/Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B), picked in the sidebar, on your machine with Hugging Face `transformers`, or on [vLLM](https://docs.vllm.ai/), in Docker started from the sidebar or on a server of your own ([Running the model on vLLM](docs/vllm.md)). Both run the same harness, so switching models changes only their text formats, which makes them easy to compare
- **The harness**: this project's own loop (`agent/harnesses/simple_harness.py`), or that of [pi](https://pi.dev), a coding agent, asking the page's model, every token still drawn, or Claude, GPT or another model pi has credentials for, drawn from what pi reports, without tokens ([pi as the harness](docs/pi.md))
- **MTP speculative decoding**: several tokens from one forward pass, for Gemma 4 E2B with its drafter on `transformers` (off by default; a switch in the sidebar) and for both models on vLLM with a GPU ([The decoding loop and MTP](docs/decoding.md))
- **Files**: attach images and videos (both models) and sound (Gemma 4 E2B, from the microphone too), or pick a sample file above the input box; with Let the model write code on, the model gets a `run_python` tool that runs in a Docker sandbox, reads your data files and draws charts ([Attachments and the code sandbox](docs/files.md))
- **Two languages**: the page and How it works are in English and Traditional Chinese; they start in your browser's language, and the switch at the top right changes it
- **[How it works](https://agentic-system-lab.github.io/agent-loop-visualizer/en/)**: maps each step of one turn to the code that does it, each excerpt a click away from its lines on GitHub; How it works at the top of the app opens it in the app's language

## Quick start

You need:

- macOS (Apple Silicon), Linux with CUDA (`nvidia-smi` showing CUDA Version 13.0 or newer), or a CPU alone (very slow)
- Disk: about 10 GB for Gemma 4 E2B, 1.8 GB for Qwen3.5 0.8B. Memory: 16 GB or more for Gemma (24 GB on a CPU alone), 8 GB for Qwen
- [uv](https://docs.astral.sh/uv/) 0.13.4 or newer (`uv self update` updates it), [just](https://github.com/casey/just#installation) (`brew install just`), and a network connection
- Optional: [Docker](https://docs.docker.com/get-started/get-docker/) to let the model write code or to run it on vLLM (Docker); [pi](https://pi.dev) with Node.js 22.19 or newer to hand it the loop

```bash
just sync       # Python 3.12 and the pinned packages
just download   # Gemma 4 E2B (about 10 GB), Qwen3.5 0.8B (1.8 GB) and Gemma's MTP drafter (190 MB) at their pinned commits; skipped, a model downloads the first time it is picked, the drafter the first time MTP is switched on
just run        # the app, loading Gemma first; MODEL_ID=Qwen/Qwen3.5-0.8B just run loads Qwen first
just sandbox    # optional: the sandbox for Let the model write code (about 400 MB); again whenever agent/sandbox/Dockerfile changes
```

Your browser opens http://localhost:8501; loading Gemma takes about 10–20 seconds the first time, Qwen a few seconds. `just` lists every recipe, and `just download Qwen/Qwen3.5-0.8B` downloads only the model named. To run the model on vLLM instead, pick vLLM (Docker) under What runs the model in the sidebar, or point the page at a server of your own with `VLLM_URL` ([Running the model on vLLM](docs/vllm.md)). Each recipe runs a command or two you could type yourself, so just is a convenience: [Setup in detail](docs/setup.md#the-commands-by-name) gives the command behind each, and says where the models go, how the page checks the sandbox, and what to do about a 401 while downloading.

## Experiments to try

1. **Just a chatbot**: switch off Use tools in the sidebar and ask "What time is it in Taipei right now?". The model sees no tools, so it can only guess or admit it does not know. Switch tools back on, ask again, and compare the two in the Context tab.
2. **Sampling**: ask the same question with temperature 0 and with 1.5, and watch how the token colors and the candidates left in the popover change.
3. **Stop conditions**: set Max steps to 1 and ask something that needs a tool; the stop reason becomes "step limit reached".
4. **Where the human sits**: switch on Ask me before running a tool, then press Reject. It is the harness that blocks the call; the model only sees an error observation in the next step's context. Compare the mail deletion incident in §5 of the reading: a "confirm first" written in the prompt can get compressed away, one written into the harness cannot.
5. **Reasoning is tokens too**: switch on Thinking mode, and italic thinking tokens appear before the tool call; in the Context tab, the system turn starts with an extra `<|think|>`.
6. **The loop goes in circles**: ask "Who proposed the ReAct paper? Look it up on Wikipedia." E2B often repeats the same search, and the harness flags "exactly the same call as before"; compare the error analysis of ReAct in §4 of the reading.
7. **Switch models, keep the harness**: ask Gemma and Qwen the same question and compare them in the Context tab: the turn markers (`<|turn>` against `<|im_start|>`), where the tool schemas go, how a tool call is written (`call:name{…}` against XML) and where the tool result goes back all differ, yet the harness, environment and stop sections of the step cards are exactly the same.
8. **MTP is fast only when it guesses right**: with Gemma, switch on MTP speculative decoding, press "What time is it in Taipei right now?", type "Write a Python function to test for primes." (with Let the model write code off), then ask "用三段話介紹台北。" (introduce Taipei in three paragraphs, in Chinese). Compare each step's tok/s and underlines: the drafter guesses almost every token of a tool call, about half of English code and only about a tenth of long Chinese text. Set temperature to 0 and run with MTP on and off: the output is exactly the same, because the drafter only decides how many forward passes run, not what gets written.
9. **An image is tokens too**: press the receipt example. In the step card's context section and in the Context tab, the image is a run of a few hundred `<|image|>` (Gemma) or `<|image_pad|>` (Qwen): what it costs in the context. The items add up to 360, but the receipt says 370; see whether the model adds them up itself or calls a tool.
10. **The context decides whether the model listens**: with Gemma, press the recording example on the Chinese page, and it writes the English sentence down and translates it. Ask "Transcribe this recording." on the English page with Use tools on, and it often says it cannot hear audio, sometimes after writing the very words into a tool call; switch Use tools off and ask again, and it transcribes it. The model and the audio tokens are the same; only the context differs.
11. **Code in a sandbox**: switch on Let the model write code (Docker needed) and press the sales data example. The note at the end of your message gives the file's path and first line; the model's code is written out in the step card, and what the sandbox printed, or its traceback, comes back as the observation, so a failing program can be fixed in the next step. Try Qwen too: it usually gets as far as the totals per month, then breaks its own code.
12. **A chart is for you, not the model**: with Let the model write code on, pick sales.csv among the sample files above the input box and ask for a chart of the revenue per month. The chart appears in the chat and under the step that drew it, but the observation the model reads is only `{"figures": ["/data/figure-1.png"]}`: it describes a chart it has never seen.

## Documentation

| Page | What it covers |
|---|---|
| [What the page shows](docs/page.md) | Each part of the page, what it shows, and the section of the Unit 01 reading it goes with |
| [Setup in detail](docs/setup.md) | Every requirement, where the models go, the sandbox image, the commands by name with just, troubleshooting |
| [Architecture](docs/architecture.md) | The two packages and their files, the events of a turn, the two languages, adding a model, the two models' formats |
| [The decoding loop and MTP](docs/decoding.md) | Why the decoding loop is hand-written, how MTP guesses and checks, and how much faster it is |
| [Attachments and the code sandbox](docs/files.md) | How images, sound and video become tokens; `run_python`'s Docker sandbox and its charts |
| [Running the model on vLLM](docs/vllm.md) | A server of your own (`VLLM_URL`) and what its flags let the page see; vLLM in Docker, started from the sidebar |
| [pi as the harness](docs/pi.md) | Handing the loop to pi, on the page's model or one of pi's own |
| [Tests](docs/testing.md) | The commands, the fakes, and what each test file covers |
| [Known limitations](docs/limitations.md) | Measured speeds, what the small models get wrong, and the limits of each backend and harness |

## License

This project's code is licensed under the [Apache License 2.0](LICENSE). The Gemma 4 weights and its MTP drafter are released by Google under Apache 2.0 (see the [model card](https://huggingface.co/google/gemma-4-E2B-it) and the [drafter's card](https://huggingface.co/google/gemma-4-E2B-it-assistant)), and the Qwen3.5 weights by Alibaba's Qwen team under Apache 2.0 (see the [model card](https://huggingface.co/Qwen/Qwen3.5-0.8B)); none of them are included in this project. `app/assets/examples/speech.flac` is utterance 1272-128104-0000 of the [LibriSpeech ASR corpus](https://www.openslr.org/12) (Panayotov et al., 2015), read from LibriVox, under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); the other example files (`receipt.png`, `ball.mp4`, `sales.csv`) and the logo were made for this project.

About the use of AI: the code was written with the help of Claude Code, run on this machine with gemma-4-E2B-it (and its MTP drafter gemma-4-E2B-it-assistant) and Qwen3.5-0.8B, and checked in a browser.
