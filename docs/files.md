# Attachments and the code sandbox

English | [繁體中文](files.zh-TW.md) · [Back to the README](../README.md)

## Images, sound and video

Which of them a model reads is found out from the checkpoint when it loads: an encoder in its config and a part of its processor to feed it. Gemma 4 E2B reads images, sound and video; Qwen3.5 0.8B reads images and video. The input box takes only what the model reads:

| Kind | Formats | Gemma 4 E2B | Qwen3.5 0.8B |
|---|---|---|---|
| Image | png, jpg, jpeg, webp, gif, bmp | up to 280 tokens | depends on the size (about 300 for 640×480) |
| Sound | wav, mp3, m4a, flac, ogg | one token per 40 ms, the first 30 seconds | — (with Let the model write code, a file for `run_python`) |
| Video | mp4, mov, webm, mkv | 32 frames (all of a shorter video), each after its time as `mm:ss`, up to 70 tokens each | 2 frames a second, in pairs, each pair after its time |
| Data | csv, tsv, json, txt, md, xlsx | with Let the model write code, for `run_python` | the same |

The chat template writes one placeholder where each file goes (`<|image|>` for Gemma, `<|vision_start|><|image_pad|><|vision_end|>` for Qwen), and `SimpleBackend.encode()` hands the processor every file in the conversation, which expands each placeholder into the file's tokens; the Context tab shows that expanded string, since it is what the model reads. `media.py` decodes the files first: images to RGB, turned upright by their EXIF; sound with PyAV to mono at the feature extractor's 16 kHz; video to at most 64 evenly spaced frames, 768 pixels on the longer side (transformers' own video loading needs torchcodec). Each file is decoded once. In the prefill, images and videos go through the vision encoder first, as `generate()` does it (handed to the forward pass as they are, videos lose their frame counts in transformers 5.20's Gemma 4), and Qwen3.5's position offset for images is cleared before every prefill. After the prefill decoding is the same as for text, and `tests/test_real_model.py` checks that greedy output with an image, a video and a recording matches `generate()`.

## Writing code in a Docker sandbox

With Let the model write code on and Docker ready ([setup](setup.md#let-the-model-write-code)), the model gets one more tool, `run_python`. Each call starts a new container from the image `agent/sandbox/Dockerfile` builds: no network, a read-only file system except a small `/tmp`, 512 MB of memory, one CPU, at most 64 processes, no Linux capabilities and your own user, never root (on Linux the mounted folder keeps its permissions, which might not let another user in), with the conversation's folder read-only at `/data`; the code goes in on stdin, and the container is deleted afterwards. Code that runs past 30 seconds is stopped; a nonzero exit, using too much memory or printing nothing (and drawing nothing) comes back to the model as an error, in the turn's language, with the traceback, so it can fix the code in the next step.

matplotlib's charts come back too, although the container cannot write anywhere the page can read: the image sets matplotlib's backend to `agent/sandbox/agent_loop_figures.py`, which turns each figure into a PNG at `plt.show()` or when the program ends and, as it exits, writes them after what the code printed, behind a marker line that `run_python` passes in. `run_python` cuts them off what the model reads (at most four), saves them in the conversation's folder as `figure-1.png`, `figure-2.png`… and returns them apart from the observation: the model reads only `{"stdout": …, "figures": ["/data/figure-1.png"]}`, and the page shows the images in the chat and under the step. A label in Chinese is drawn with WenQuanYi Micro Hei, the font the image installs for it. Importing matplotlib makes a call about half a second slower (0.8 s against 0.2 s for plain Python).

The image installs pip 26.2.2 first, from its wheel by hash, and everything else with it: an older pip also trusts its own copy of certifi, which still has the compromised emSign certificates. The page reads the `agent-loop-sandbox.version` label of the image, and when it is older than `agent/sandbox/Dockerfile` the sidebar asks for a rebuild instead of offering `run_python`.

The model cannot see into a data file, so the harness adds a note to the user's message: where `run_python` finds each file, and the first line of a text file (for a CSV, its column names). Without that line a small model guesses columns in its code, a `Date` that is not there, and fails; with a few rows of data as well, Gemma copied the rows into its code and answered from them alone. `tabulate` is in the image because `DataFrame.to_markdown()`, which small models like to print tables with, needs it.
