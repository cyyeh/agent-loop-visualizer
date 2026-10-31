# What the page shows

English | [繁體中文](page.zh-TW.md) · [Back to the README](../README.md)

Each part of the page, what it shows, and the section of the Unit 01 reading of [Agent Atlas](https://agentic-system-lab.github.io/agent-atlas-learning/) (in Traditional Chinese) it goes with.

| On the page | What you see | Unit 01 reading (in Chinese) |
|---|---|---|
| Loop diagram | Which box you are in (context, model, harness, environment, stop) and the arrow that is flowing | §4 An agent is a model in a loop |
| Context | The whole string the model reads in each step (with pi on a provider's model, the request pi sent instead, as JSON): the system prompt, the tool schemas, the conversation and the tool result added after the last step. Hovering over a dark special token says what it is for. An attached image, clip or video is the run of tokens it expands into, drawn as one chip with its count (`<\|image\|>` ×266) | §1 The context has a limit, §3 Tool definitions are tokens too |
| Model | Every generated token, darker the less likely the chosen token was. Hovering over a token shows its probability, its rank, the top 5 candidates and which ones top-k / top-p cut. With MTP on, tokens the drafter guessed right are underlined, and the step card shows how many were kept. On vLLM, as much of this as the server's flags let it send; with pi on a provider's model, only the text as it streams | §1 An LLM samples from a conditional probability distribution; decoding settings |
| Harness | The tool calls parsed from the model's own format (Gemma 4 or Qwen3.5), the schema check, warnings about repeated calls, and your Allow or Reject | §3 The model never touches the environment |
| Environment | What the tool really returned and how long it took; for `run_python`, the code is written out above and what it printed, or its traceback, below | §2 The environment and observable state |
| Stop | Why it stopped and at which token. Gemma stops at `<turn\|>` after an answer (like end_turn) and at `<\|tool_response>` when it wants a tool (like tool_use); Qwen stops at `<\|im_end\|>` either way. Then there are the step limit, the token limit and the user pressing stop | §5 When to stop |
| Model tab | The parameter breakdown, the layers, attention heads and context limit, what the model reads, the MTP drafter, what each decoding setting does, each step's prefill time and tok/s, every special token of the tokenizer (24 for Gemma, 33 for Qwen), and every file in the model's folder in `models/` with what it holds | §1, §7 An agent is a system |
| How it works | The 18 stages of one turn, each with the code that does it, linked to its lines on GitHub at the commit the page was built from, with tabs where the models, backends or harnesses differ; rebuilt on every push to main, so it follows the code | All of it |
