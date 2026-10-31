# Architecture

English | [繁體中文](architecture.zh-TW.md) · [Back to the README](../README.md)

The project has two parts. `agent/` runs a turn: the harness that runs the agent loop, the tools, the model's family and what runs the model. `app/` is what you see: the page and the HTML it draws from the agent's events; `docs/guide/guide.py` builds How it works from them. They depend one way: `app/` builds on `agent/`, and nothing in `agent/` imports `app/` or Streamlit (`test_layout.py` checks), so the loop runs, and is tested, without a page.

```
streamlit_app.py       where Streamlit starts: it runs app/page.py's main() on every rerun
justfile               the commands by name, for just
app/                   what a person sees, built on the agent
  page.py              layout, session state, model menu, language switch, background thread; redraws every 0.5 s while a run is live
  render.py            turns the event list into HTML: the loop diagram, step cards, token heat and popovers, the context view
  assets/              the page's styles, which the guide shares; logo.svg; examples/, the files the examples attach and the sample files above the input box
agent/                 what runs a turn: the harness, the model, what runs the model, the tools; it never imports Streamlit
  harnesses/           what runs the loop
    harness.py         the Harness the page runs a turn through: run, stop, decide, and the events every harness sends
    simple_harness.py  this project's loop: build the prompt → generate → parse → validate → (ask you) → run the tool → back into the context → stop?
    pi_harness.py      pi as the harness: pi in RPC mode, its JSON records turned into the page's events
    pi_extension.ts    the pi extension the page loads: it reports each request pi sends, registers the page's model, and asks you before pi runs a tool
    model_endpoint.py  the page's model as an OpenAI-compatible endpoint on 127.0.0.1, for pi: render, encode, generate, and the tokens back to pi
  model_backends/      what runs the model
    backend.py         the Backend that the harness and the page run the model through: render, encode, generate, and the fields of a token event
    simple_backend.py  local inference with a hand-written decoding loop; MTP's drafting and checking are here too
    vllm_backend.py    the model on a vLLM server (VLLM_URL): the prompt rendered and tokenized here, the token ids to the server, what it can tell about each token back; media, sampling masks and MTP's guesses on a server started with the flags for them
    vllm_docker.py     vLLM in Docker for the sidebar's vLLM (Docker): docker compose up with the picked model, waiting until it answers; docker compose down
  model_families/      everything that goes with the model: how each model family writes turns, thinking and tool calls, which tokens stop it, what each means
    __init__.py        the Family definition, the model menu MODELS, the MTP drafters DRAFTERS, finding a family by config.json's model_type
    gemma4.py          Gemma 4: the output parser and notes on its 24 special tokens
    qwen3_5.py         Qwen3.5: the output parser and notes on its 33 special tokens
  tools.py             tools: the schema (for the model) plus the Python function (for the harness to run); run_python's Docker sandbox
  media.py             attachments: saving them, writing them into the user's message, decoding images, sound and video for the processor
  i18n.py              the two languages: pick() chooses the text for one, from_locale() picks the default from the browser's language; the errors the model reads use it too
  sandbox/             run_python's sandbox: the Dockerfile (Python 3.12 with numpy, pandas, openpyxl, tabulate and matplotlib), and the matplotlib backend and settings that send the charts back
docker-compose/        the vLLM server the page starts in Docker
  compose.yaml         vLLM on the CPU (any machine, a Mac's included), on 127.0.0.1 only, models/ read-only
  compose.gpu.yaml     on top of compose.yaml: vLLM's CUDA image on NVIDIA GPUs
  vllm-cpu/            vLLM 0.32.0's CPU image with the two fixes it lacks (patch_vllm.py)
docs/                  these pages, each in English and in Chinese (.zh-TW.md), and the READMEs' screenshots
  guide/               How it works, the static page on GitHub Pages
    guide.py           its content in both languages, line lookups, and the static HTML; python -m docs.guide builds it
    guide.css          its style, inlined into the page beside the app's palette
    guide.js           its one script, inlined too
tests/                 pytest tests; see Tests
models/                the downloaded models (git ignores it; AGENT_LOOP_MODELS moves it)
```

The agent runs in a background thread and appends an event at every stage; the UI only draws the event list. So when you press Stop or Allow and Streamlit reruns the script, the loop in the background is not interrupted. The page reaches the loop only through a `Harness` (`harnesses/harness.py`): `run()`, `stop()`, `decide()` and the events it sends. `SimpleHarness` is this project's own, and `PiHarness` hands the loop to pi ([pi as the harness](pi.md)).

How it works is a static page: `just guide` (`uv run python -m docs.guide _site`) writes `_site/en/index.html` and `_site/zh/index.html` (styles and a small script inlined, so they open straight in a browser), and `_site/index.html`, which sends a reader to the language they last picked on the page's switch, or else their browser's. On a push to main, `.github/workflows/pages.yml` runs `tests/test_guide.py`, then does the same and publishes it to GitHub Pages; if the tests fail, the page already up stays as it was.

## The events of a turn

The events of one run, in order:

```
run_start
  step_start → context → prefill → token ×N → model_end → parsed                 each step
    tool_call → (approval_request → approval) → (tool_start) → tool_result       a step with a tool call
(error)
run_end
```

- `run_start` says which harness ran the turn (`harness`: `simple` or `pi`).
- `context` carries the prompt as the model reads it, with each attachment expanded into its tokens, and how many tokens each kind of media took (`media_tokens`).
- `token` carries the token and, when the backend knows them, its probability, its rank, the top 5 candidates and what MTP's drafter guessed (`backend.TOKEN_DETAILS`): `simple_backend.py` knows them all, and the page leaves out whatever a backend does not report rather than showing a number nobody measured.
- `model_end`: a backend that learns which tokens were MTP's guesses only when the step ends (a vLLM server) says so in its MTP counts (`kept_at`, `turned_down_at`), and the page marks those tokens then.
- `approval_request` and `approval` come only with Ask me before running a tool on, and `tool_start` only when the tool runs.
- `tool_result` carries the observation the model reads and, apart from it, the images the tool made for you (`images`: the paths of `run_python`'s charts), which the model never reads.
- `error` comes before `run_end` when something failed: its `message` is the exception's, and a backend's error (a vLLM server's, say) also comes in both languages (`text`), so the page shows the one it is in.
- With pi, a step begins with `request`, the request pi sent the model, as JSON. When pi asks the page's model, the model endpoint sends that step's `context`, `prefill`, `token` and `model_end` as the built-in harness does; when pi asks a provider's model, there is no family and none of those four but `delta`, a piece of the model's output and its channel (thinking, reply, tool call) as it streams, and a `model_end` with the token counts the provider reported (`usage`).

## Two languages

Every piece of text on the page is written in both languages side by side in the code: `pick(lang, "中文", "English")` in code, and `{"zh": …, "en": …}` in data (the special token notes, the stop reasons, the paragraphs of How it works). Every function in `render.py` that writes words takes a `lang`, and the events themselves have no language, so switching the language redraws the same events in the other one, finished turns included. The page starts in the language last picked, kept in a cookie, or else in the browser's `navigator.language` (anything starting with `zh` is Chinese, the rest English); picking one writes the cookie with a small script, because Streamlit can read cookies but not write them.

What the model reads from the harness (wrong arguments, a failed tool, your refusal) is worded in the language the page was in when the turn started, because it becomes the observation word for word; the system prompt is the same in both, so the model's behavior does not depend on the page's language.

## Supporting more models

The harness (`harnesses/simple_harness.py`), the decoding loop (`simple_backend.py`) and the page (`render.py`) are written once, without a single "if Gemma" branch. Whatever differs between models is gathered in one `Family` object in `model_families/`:

- Reading the output: `parse` (splits the output into thinking, tool calls and the reply), `thought_prefix`, `channel_switch` (which tokens switch to thinking, a tool call or the reply), `stop_tokens`
- Writing the conversation back: `reasoning_key` (the field the thinking is kept in, so the chat template can read it), `text_with_calls` (whether text in front of a tool call is kept)
- The page: `user_turn`, `byte_level` (whether the vocabulary spells bytes as characters, as Qwen's does, so a token popover shows 如果 instead of `å¦Ĥæŀľ`), a note on each special token, `file_notes` and `drafter_file_notes` (what each file of a checkpoint's folder holds, and the fields whose values the Model tab shows), the help text for the sidebar and the Model tab, and the recommended decoding settings when there is no generation_config.json; each in English and in Chinese
- Media: `processor_kwargs`, settings for the processor (Qwen caps the pixels of each video frame); which kinds a model reads comes from the checkpoint, not the family

To add a model:

1. Another checkpoint of a family that is already here (a bigger Gemma 4 or Qwen3.5, say): add a line to `MODELS` in `agent/model_families/__init__.py`, and one to `REVISIONS` with the commit to download it at. Other Gemma 4 checkpoints have MTP drafters too (`google/gemma-4-*-it-assistant`); add a line to `DRAFTERS` (and the drafter's commit to `REVISIONS`) and the sidebar's MTP switch works for them.
2. A new family: write a module like `agent/model_families/qwen3_5.py` (a parser for the output plus notes on the special tokens, in both languages) and add its `Family` to `FAMILIES`. Loading a model finds it automatically by the `model_type` in the checkpoint's `config.json`. `tests/test_chat_template.py` checks a new family against the real tokenizer and chat template: every special token has a note, tool calls the template writes into the history parse back, and what the step card marks as new is exactly the tool result.

Or ask for it: on a vLLM server, picking a model of a family the page does not know offers a GitHub issue already filled in, and an issue for any other model you would like to watch is welcome too, at https://github.com/Agentic-System-Lab/agent-loop-visualizer/issues.

## The two models' formats

Gemma 4 wraps strings in the special token `<|"|>` and leaves keys unquoted, so it is not JSON, and `agent/model_families/gemma4.py` has its own small parser:

```
<|tool_call>call:get_current_time{timezone:<|"|>Asia/Taipei<|"|>}<tool_call|><|tool_response>
```

After writing a tool call, Gemma stops at `<|tool_response>` to wait for the harness to add the result; after an answer it stops at `<turn|>`. These two stop tokens line up with `stop_reason: tool_use` and `end_turn` in the Anthropic Messages API.

Qwen3.5 uses XML, and every value is plain text, typed by the tool's schema (as vLLM's `qwen3_coder` parser does):

```
<tool_call>
<function=get_current_time>
<parameter=timezone>
Asia/Taipei
</parameter>
</function>
</tool_call><|im_end|>
```

Qwen stops at `<|im_end|>` both after an answer and for a tool, so the harness decides whether to end by whether parsing found a tool call, not by the stop token. The tool result goes into a new `user` message (`<tool_response>…</tool_response>`) instead of the same model turn as with Gemma.
