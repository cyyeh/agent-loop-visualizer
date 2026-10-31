# pi as the harness

English | [繁體中文](pi.zh-TW.md) · [Back to the README](../README.md)

The page can also hand the loop to [pi](https://pi.dev), a coding agent with a loop, a system prompt and tools of its own (read, bash, edit, write, grep, find, ls). Pick pi under What runs the loop at the top of the sidebar, then under The model pi asks which model it asks, and the page draws what pi does in the same diagram, step cards and event list. Each step's context section shows the request pi sent the model (its system prompt, its tools and the conversation, as JSON), with what the step added marked.

- **This page's model** (the default): Gemma 4 E2B or Qwen3.5 0.8B, on transformers or vLLM, picked with the same model menu and What runs the model as for the built-in harness. pi asks models over HTTP alone, so `agent/harnesses/model_endpoint.py` serves the model in memory as an OpenAI-compatible chat completions endpoint on 127.0.0.1, behind a token, and pi's extension registers it as the provider `agent-loop`. Each request is rendered with the model's chat template, encoded and generated as a step of the built-in harness is, and its events go into pi's step: the Context tab shows the string the model read (and, folded under it, the request pi sent), and every token shows with its probability and candidates. The reply streams back to pi, the thinking as `reasoning_content` and the reply as `content`, with the tool calls the family parses out of the model's own format as `tool_calls` at the end. The decoding settings are the sidebar's; Thinking mode reaches the model as pi's thinking level, which the endpoint turns into the chat template's thinking switch.
- **pi's own models**: one pi has credentials for (Claude, GPT, Gemini, or any compatible endpoint in its `models.json`); no model loads here. An API sends back text, not tokens, so there are no token probabilities, candidates or special tokens, and how the API writes the request out for the model nobody says: a step shows pi's request, the text as it streams, the token counts the provider reported (with how many came from the cache) and the cost at pi's prices.

## Installing pi

```bash
nvm install                                      # with nvm: installs the newest Node 22 (.nvmrc) and switches to it; nvm use could pick an older 22 already installed, too old for pi. Install pi under it, since nvm keeps global packages per version
npm install -g @earendil-works/pi-coding-agent   # pi 1.4 needs Node.js 22.19 or newer
pi                                               # then /login, once; or set an API key such as ANTHROPIC_API_KEY before starting the app
PI_COMMAND=/path/to/pi just run                  # if pi is not on the PATH (any command works, npx included)
```

## In detail

- **How the page runs it.** `agent/harnesses/pi_harness.py` starts pi for each question in RPC mode (`pi --mode rpc`): commands go to its stdin and records come from its stdout, one JSON object per line. It picks the model and the thinking level, turns pi's own retries off (a retry would be another step, so a failed request is shown as an error instead) and sends the question, each command only once pi has answered the last; one of pi's turns (one request to the model, and the tools its reply calls) is one step. pi keeps the conversation in a session file in the conversation's folder, so the next question continues it; New chat removes it.
- **What it starts pi without.** The user's own extensions, skills, prompt templates and context files (AGENTS.md, CLAUDE.md) stay out (`--no-extensions` and the like), so the page draws pi's own loop, the same on every machine; the models and the credentials are still the user's, in `~/.pi/agent`.
- **Tools.** The sidebar picks which of pi's tools the model sees (read, bash, edit and write by default, as pi offers). They run on this computer, in the conversation's folder, without a sandbox: unlike `run_python`, bash reaches whatever you can. A file you attach is saved in that folder and named in the question; an image also goes with the question to a model that reads images.
- **The extension.** Every pi the page starts loads `agent/harnesses/pi_extension.ts`. Before each request to the model it sends the request as a notification, which in RPC mode is an `extension_ui_request` on stdout and becomes the step's `request`; it registers the page's model when pi asks it; and it is what asks before a tool call (below).
- **Ask me before running a tool.** pi does not ask by itself; with this on, the extension opens a confirm dialog before every tool call. In RPC mode the dialog comes out on stdout, the page shows it as Allow and Reject, and the answer goes back on stdin; a rejected call does not run, and the model reads the refusal in the turn's language.
- **Stopping.** Stop sends pi `abort`. pi has no step limit of its own, so the page keeps Max steps: when pi starts a turn past it, the page aborts pi. An unanswered confirmation stops pi after 5 minutes, as with the built-in harness.
- **Tested** with pi 1.4.0, through a stand-in that speaks its protocol from a script (`tests/fake_pi.py`, which asks the model endpoint over HTTP as pi does) and, with `RUN_PI_TESTS=1`, the real pi, pointed at a scripted model on 127.0.0.1 and at the model endpoint with the fake model behind it.
