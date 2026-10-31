# The decoding loop and MTP

English | [繁體中文](decoding.zh-TW.md) · [Back to the README](../README.md)

## Why a hand-written decoding loop

`model.generate()` does not hand out the probability distribution at each step, so `simple_backend.py` runs the loop itself: one forward pass per token (with a KV cache), then temperature, top-k and top-p in turn, then a sample. So every token can report its probability and rank in the model's own distribution, its probability when sampled, how many candidates were left after top-k / top-p, and the top 5 candidates. In greedy mode the output matches `generate()`, as measured; of two equally likely tokens (in bfloat16, logits tie more often than one would think) it takes the lower id, as `generate()`'s argmax does.

## MTP speculative decoding

Decoding runs a full forward pass for every token, and the time goes mostly into reading the weights from memory; computing a few more positions in the same pass is hardly slower (Gemma 4 E2B on an Apple M5: about 56 ms for 1 position, about 70 ms for 7). So if the next few tokens are guessed cheaply first, the model can check them all in one forward pass. Google trained such a drafter for Gemma 4 (MTP, multi-token prediction), and `transformers`' `generate(assistant_model=…)` uses it, but that again hides the distribution at each step, so `simple_backend.py` wires it into its own decoding loop:

1. **Guess** (`_draft`): the drafter `gemma-4-E2B-it-assistant` has about 78M parameters and 4 layers. It has no KV cache of its own and reads the model's keys and values directly (the last 20 layers of Gemma 4 E2B already share those two earlier layers computed); its input is the last token's embedding next to the model's last-layer hidden state. It makes 6 greedy guesses at a time (the checkpoint's `num_assistant_tokens`).
2. **Check** (`_drafted`): the model runs one forward pass over the token just settled plus the 6 guesses, gets back the distributions at 7 positions and hands them to `_sample()` in order. A kept guess needs no forward pass of its own; the first guess turned down is replaced by the model's own pick at that position, everything after it is dropped, and the KV cache is cut back with `crop()`; when all 6 hold, the last position gives one more token.
3. **Same output**: in greedy decoding a guess is kept only when it is the top token, so the output is the same as without MTP (`tests/test_real_model.py` compares them with the real model). When sampling, a guess is kept with its probability after temperature, top-k and top-p, and otherwise the token is drawn from the other candidates, so every token comes out exactly as often as without MTP (speculative sampling; `tests/test_simple_backend.py` checks it over twenty thousand samples).

How many guesses are kept depends a lot on the content. Measured in the page with Gemma's default decoding settings (Apple M5):

| What the step writes | Without MTP | With MTP | Guesses kept |
|---|---|---|---|
| A tool call (step 1 of "台北現在幾點？紐約呢？", "What time is it in Taipei now? And New York?") | 12.6 tok/s | 40.9 tok/s | 34 / 35 |
| The answer from the tool result (step 2 of the same question) | 13.0 tok/s | 22.6 tok/s | 42 / 106 |
| English code, about 750 tokens | 8.8 tok/s | 11.6 tok/s (`simple_backend.py` alone: 8.1 → 29.0) | 51% |
| Long Chinese text ("用三段話介紹台北。") | 10.3 tok/s | 10.3 tok/s | 7% |

With transformers only Gemma 4 E2B has a drafter. On a vLLM server with a GPU both models can decode speculatively, Gemma 4 E2B with the same drafter and Qwen3.5 with the MTP layer in its own checkpoint: vLLM in Docker does so by default on a GPU, and a server of your own needs `--speculative-config` ([Running the model on vLLM](vllm.md)).
