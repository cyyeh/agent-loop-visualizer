# 安裝與設定

[English](setup.md) | 繁體中文 · [回到 README](../README.zh-TW.md)

README 的「[快速開始](../README.zh-TW.md#快速開始)」跑的是 `justfile` 裡的指令；這一頁說明它們需要什麼、跑起來會發生什麼事，也列出[每個指令背後的那一行](#用-just-跑這些指令)，給沒有 just 的電腦用。

## 需求

- macOS（Apple Silicon，用 MPS）、有 CUDA 的 Linux，或只用 CPU（很慢）
- 磁碟空間放模型權重：Gemma 4 E2B 約 10 GB，Qwen3.5 0.8B 約 1.8 GB；要用 MTP 再加上 Gemma 的草稿模型約 190 MB
- 記憶體：Gemma 用 MPS 或 CUDA 時建議 16 GB 以上（bfloat16 權重約 10 GB），只用 CPU 時會以 float32 載入，約 20.5 GB，建議 24 GB 以上；Qwen3.5 0.8B 小得多，8 GB 的機器也跑得動。同一時間只會載入一個模型，換模型時舊的會被放掉
- Linux + CUDA：鎖定的 torch 是 CUDA 13 版本，`nvidia-smi` 右上角的 CUDA Version 要 13.0 以上。驅動太舊時 torch 會偵測不到 GPU，改用 CPU 執行；側欄上方會顯示目前用的裝置
- [uv](https://docs.astral.sh/uv/) 0.13.4 以上（會自動裝好 Python 3.12）。更舊的版本還信任 eMudhra 那批外洩的 emSign 憑證（[公告](https://discuss.python.org/t/109576)），所以 `uv sync` 會拒絕執行；用 `uv self update`（或 `brew upgrade uv`）更新
- [just](https://github.com/casey/just#installation)（`brew install just`，或它的安裝頁面為你的系統列出的套件管理工具），用名字跑這些指令。每個名字背後都只是一兩行指令，所以沒有 just 也可以自己打（見[下面](#用-just-跑這些指令)）
- 網路：第一次下載模型，以及 Wikipedia 工具
- 選用：[Docker](https://docs.docker.com/get-started/get-docker/)（Docker Desktop、OrbStack 或 Colima），只有讓模型寫程式、或用 vLLM (Docker) 跑模型時才需要
- 選用：[pi](https://pi.dev) 和 Node.js 22.19 以上，只有要把迴圈交給 pi 時才需要（「[pi 當 harness](pi.zh-TW.md)」）

## 啟動之後

瀏覽器會打開 http://localhost:8501 ，語言跟著瀏覽器（中文的瀏覽器看到中文，其他看到英文），右上角的「中文 | English」可以切換，下次打開會用你選過的那個。第一次載入 Gemma 加暖機大約 10–20 秒，Qwen 幾秒；之後重新整理頁面不會再載入。側欄最上面的「模型」選單可以換模型，換了會開新對話，解碼設定也換成新模型的建議值，MTP 回到關閉。側欄的「MTP 推測解碼」第一次打開時才載入草稿模型（不到 1 秒），之後一直留在記憶體裡。

## 模型放在哪裡

模型下載到專案資料夾裡的 `models/`（git 會忽略它），不是其他專案共用的 `~/.cache/huggingface/hub`；刪掉這個資料夾就能把空間拿回來。每個模型都照固定的 revision 下載，也就是 `agent/model_families/__init__.py` 裡 `REVISIONS` 的 commit（[下面](#用-just-跑這些指令)那幾行 `hf download` 的 `--revision`），所以不管什麼時候下載，拿到的都是這個網頁寫作和測試時用的檔案，在每種作業系統上都一樣。想放在別的地方，就把 `AGENT_LOOP_MODELS` 設成那個資料夾（`just download` 也會下載到那裡；`hf download` 的 `--cache-dir` 也改成它）；`AGENT_LOOP_MODELS=$HOME/.cache/huggingface/hub` 會用之前已經下載在那裡的模型。`HF_HUB_CACHE` 不會改變位置，因為它常是整台電腦所有專案共用的設定。

## 讓模型寫程式

側欄的「讓模型寫程式」預設關閉，關著的時候（也沒選 vLLM (Docker)）網頁完全不會去找 Docker。打開之後才檢查 Docker 和 `agent-loop-sandbox` image，缺了哪一個，或 image 是用舊版的 `agent/sandbox/Dockerfile` 建的，就在側欄說明怎麼安裝 Docker 或建 image；兩個都在，模型才拿得到 `run_python`，要寫 Python 的範例（打開就會出現）也才按得下去。你附上的檔案存在 `~/.cache/agent-loop-visualizer/uploads/` 底下，每段對話一個資料夾（按「新對話」就刪掉），沙箱裡看到的是唯讀的 `/data`。沙箱怎麼運作，見「[附件與程式沙箱](files.zh-TW.md#在-docker-沙箱裡寫程式)」。

## 用 just 跑這些指令

`justfile` 替 README 和這些頁面裡的指令取了名字，給 [just](https://github.com/casey/just) 用：`just` 會列出全部，`just <名字>` 會在專案資料夾裡跑其中一個，不管你在專案的哪一層。每個名字背後都只是一兩行指令，寫在它旁邊或區塊後面，所以沒有 just 也可以自己打。環境變數照樣傳給指令，名字後面接的參數也會交給指令：

```bash
just sync                            # uv sync
just download                        # REVISIONS 裡的每個模型和草稿模型，照固定的 commit 下載到 models/（或 AGENT_LOOP_MODELS）：約 12 GB
just download Qwen/Qwen3.5-0.8B      # 只下載指定的
just run                             # uv run streamlit run streamlit_app.py；MODEL_ID=Qwen/Qwen3.5-0.8B just run 先載入 Qwen，VLLM_URL=http://localhost:8000 just run 改問那台伺服器
just sandbox                         # docker build -t agent-loop-sandbox agent/sandbox
just check                           # checks.yml 在 pull request 上跑的：just lint、just types、just test，再跑 just guide-check（見「測試」）
just guide                           # uv run python -m docs.guide _site：把運作說明產生到 _site/
just vllm-up                         # 自己在 Docker 裡啟動 vLLM，在 CPU 上（NVIDIA GPU 用 just vllm-up gpu）；just vllm-down 停掉它；背後的 docker compose 指令見「由網頁在 Docker 裡啟動 vLLM」
```

測試的指令在「[測試](testing.zh-TW.md)」，`just vllm-up` 和 `just vllm-down` 背後的 `docker compose` 指令在「[由網頁在 Docker 裡啟動 vLLM](vllm.zh-TW.md#由網頁在-docker-裡啟動-vllm)」。`just download` 從 `agent/model_families/__init__.py` 的 `REVISIONS` 讀 commit，所以模型換到較新的 commit 之後，下載的仍是這個網頁測試時用的檔案。沒有 just 的話，照今天固定的 commit，它就是：

```bash
uv run hf download google/gemma-4-E2B-it --revision 3e22461f65e89153144f8adb70e3b8c2cc9845a7 --cache-dir models   # 約 10 GB
uv run hf download Qwen/Qwen3.5-0.8B --revision 2fc06364715b967f1860aea9cf38778875588b17 --cache-dir models       # 約 1.8 GB
uv run hf download google/gemma-4-E2B-it-assistant --revision 2d874ef7d29f9a30599a1e4b3c1cbc9595f005df --cache-dir models   # Gemma 的 MTP 草稿模型，約 190 MB
```

沒下載的模型，第一次選到時會自動下載；草稿模型則是第一次打開 MTP 時。

## 疑難排解

下載時出現 401，可是模型明明是公開的？多半是本機存的 Hugging Face token 過期了。重新登入（`uv run hf auth login`），或加上 `HF_HUB_DISABLE_IMPLICIT_TOKEN=1` 不送 token。
