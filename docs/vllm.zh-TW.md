# 在 vLLM 上跑模型

[English](vllm.md) | 繁體中文 · [回到 README](../README.zh-TW.md)

模型也可以放在 [vLLM](https://docs.vllm.ai/) 伺服器上跑：可以是網頁在 Docker 裡替你啟動的那台（見[下面](#由網頁在-docker-裡啟動-vllm)），也可以是任何一台，在這台電腦或一台有 GPU 的 Linux 機器都可以，網頁還是在你的電腦上。

## 自己的伺服器

用自己的伺服器時，把 `VLLM_URL` 設成它的位址：

```bash
# 跑 vLLM 的地方（vLLM 0.32 以上，Linux 加 GPU）。--revision 是 REVISIONS 裡的 commit，伺服器和網頁讀的就是同一份
# tokenizer 和 chat template。其他參數讓網頁看得到更多（見下面）。
vllm serve Qwen/Qwen3.5-0.8B --revision 2fc06364715b967f1860aea9cf38778875588b17 --enable-scale-out
# 或是 Gemma 4 E2B 加上它的 MTP 草稿模型，回報哪些 token 是猜中的：
vllm serve google/gemma-4-E2B-it --revision 3e22461f65e89153144f8adb70e3b8c2cc9845a7 --enable-scale-out \
  --speculative-config '{"method": "mtp", "model": "google/gemma-4-E2B-it-assistant", "revision": "2d874ef7d29f9a30599a1e4b3c1cbc9595f005df", "num_speculative_tokens": 6}' \
  --per-request-spec-decode-metrics detailed
# 或是 Qwen3.5 用它自己 checkpoint 裡的 MTP 層（transformers 用不了）：
vllm serve Qwen/Qwen3.5-0.8B --revision 2fc06364715b967f1860aea9cf38778875588b17 --enable-scale-out \
  --speculative-config '{"method": "mtp", "num_speculative_tokens": 2}' --per-request-spec-decode-metrics detailed
# 或是開 sampling mask：看得到剩下幾個候選，但換掉模型自己的機率（見下面）：
vllm serve Qwen/Qwen3.5-0.8B --revision 2fc06364715b967f1860aea9cf38778875588b17 --enable-scale-out \
  --return-sampling-mask --logprobs-mode processed_logprobs

# 跑網頁的地方（沒有 just 的話：VLLM_URL=http://localhost:8000 uv run streamlit run streamlit_app.py）：
VLLM_URL=http://localhost:8000 just run
```

側欄的模型選單會列出伺服器提供的模型。網頁還不支援的家族的模型會標上 ⚠（只看它的 `config.json` 就知道），新開的分頁會先選第一個支援的模型。選了標 ⚠ 的模型，網頁會說明為什麼跑不了，並附上一個到 GitHub 提 issue 的按鈕，標題和內容已經填好：寫的是模型和它的 `model_type`，不會寫伺服器的位址。伺服器用了 `--api-key` 的話，把同一把 key 放在 `VLLM_API_KEY` 給網頁（`vllm serve` 也是從這個變數讀）。伺服器的 KV cache 放不下模型完整的脈絡長度時，用 `--max-model-len` 調低；網頁的脈絡上限會跟著伺服器。

## 網頁看得到什麼

`vllm_backend.py` 是 `simple_backend.py` 之外的第二個 `Backend`（`backend.py`）；harness、工具和網頁都不用改。prompt 一樣精確：網頁把模型的設定檔、tokenizer 和 chat template 下載到 `models/`（不下載權重），自己 render、自己切 token，再把 token id 送給伺服器，所以伺服器讀到的就是脈絡分頁上的那一串。每個 token 回來時帶著它的 id、log 機率，以及那個位置最可能的幾個 token 的 log 機率。vLLM 預設的 `--logprobs-mode raw_logprobs` 下，這些就是模型自己的分布，和 `simple_backend.py` 一樣，由此得到浮窗裡「模型給的機率」和前 5 名候選。網頁還能看到多少，看伺服器加了哪些參數；載入時，網頁用只生成一個 token 的請求問伺服器加了哪些：

| 伺服器參數 | 每一步送到哪裡 | 畫面多了什麼 |
|---|---|---|
| 都沒有 | `/v1/completions` | 機率、前 5 名，token 在前 5 名裡時才有排名；只讀文字 |
| `--enable-scale-out` | `/inference/v1/generate` | 每個 token 的排名，以及伺服器收的圖片、聲音和影片 |
| 再加 `--return-sampling-mask --logprobs-mode processed_logprobs` | 同上 | 剩下的候選和取樣時的機率，但換掉模型給的機率、熱度和前 5 名：vLLM 只在 processed log 機率下送 sampling mask，這時也不接受 temperature 0 和 top-k 0，所以側欄從 0.05 和 1 開始 |
| `--per-request-spec-decode-metrics summary` / `detailed` | 兩條都行 | 每一步 MTP 的統計；`detailed` 的話，step 結束時猜中的 token 也有底線 |

畫面不畫的，就不會自己編（`backend.TOKEN_DETAILS`）。細節：

- **`--logprobs-mode`** 決定這些數字是什麼，但沒有哪條路會說伺服器用的是哪一種，所以載入時網頁要一個 token，temperature 1、top-k 2、要最可能的 5 個：processed 模式下，被 top-k 剃掉的 3 個會回 -9999；log 機率加起來最多是 1，logits 不會。用 `processed_logprobs` 時（`--return-sampling-mask` 一定要它；沒有它，或沒有 vLLM 的 Model Runner V2，伺服器就不啟動，而 V2 在能用的情況下是預設），token 的 log 機率是它在抽樣分布裡的機率，已經套過 temperature、top-k、top-p，所以浮窗把它當成取樣時的機率，加上排名，不顯示模型給的機率、熱度和前 5 名。剩下幾個候選來自 sampling mask；沒有 mask 時，只有在 top-k / top-p 剃掉了列出來的幾個最可能的 token 時才看得到。用 `raw_logits` 或 `processed_logits` 時，這些數字不是機率，畫面不會把它們當成機率顯示。前 5 名裡哪些被 top-k / top-p 剃掉（`simple_backend.py` 的浮窗裡的灰色），除了 greedy 解碼，哪一種模式都看不到：模型自己的機率和取樣器做了什麼，不會一起回來。模型分頁會寫伺服器用的是哪一種。
- **排名**算的是比選中的 token 更可能的有幾個，和 `simple_backend.py` 一樣，所以同分第一的 token（bfloat16 的 logits 常常打平）是 #1。`/inference/v1/generate` 的排名把和它同分的也算進去（vLLM 0.32 比的是 `>=`）；推測解碼時它比的是 logits，列出來的 log 機率卻可能在 logits 沒打平的地方打平。所以只要清單上有一個 token 不比選中的更可能，比它更可能的就一定都列出來了，網頁就照它顯示的 log 機率算排名；排在全部清單之後的 token 則用伺服器的排名，可能還算著伺服器沒列出的同分。
- **greedy 解碼**（temperature 0）不用伺服器說也知道只剩一個候選、抽中的機率是 1，所以只要伺服器接受 greedy，浮窗都會顯示。啟動時加了 `--return-sampling-mask` 的伺服器不接受：vLLM 在每條路上都拒絕 temperature 0 和 top-k 0，所以側欄的滑桿最低到 0.05 和 1：建議的 temperature 低於 0.05 時調到 0.05，top-k 0（不限）改成滑桿最大的 128。沒加 `--enable-scale-out` 時，沒有哪個回應看得到 mask，所以載入時網頁也會向這種伺服器（processed log 機率的）要一個 greedy 的 token，被拒絕就知道了。
- **圖片、聲音和影片**跟著 chat template 寫的佔位 token 一起送過去，放在伺服器的 `content_parts`：圖片照 EXIF 轉正存成 PNG；聲音在這裡解碼成 WAV；影片送原檔，由伺服器挑畫格。伺服器把每個佔位 token 展開成那個檔案的 token。為了讓脈絡分頁顯示伺服器讀到的 prompt，網頁先用一個只生成一個 token 的請求問它怎麼展開；生成時伺服器若展開得不一樣，這一步就算錯誤。載入時網頁送一張很小的圖、一段聲音和一段影片給伺服器，看它收哪幾種；它不收的種類（沒加 `--enable-scale-out` 時就是全部）不能附上，輸入框上方會說明，模型分頁列出原因。
- **MTP** 由伺服器決定（`--speculative-config`），所以側欄的開關關著、不能按。伺服器加上 `--per-request-spec-decode-metrics summary` 的話（vLLM 要和 `--speculative-config` 一起才收），每一步會顯示收下幾個猜測、主模型解碼 forward 幾次。vLLM 是在停止 token 截斷那次驗證之前算收下幾個，所以停止 token 是其中一個猜測時，它後面的猜測也算進去。設成 `detailed` 還會說每一次驗證收下幾個猜測，網頁由此標出猜中的 token：第一個 token 來自 prefill，之後每次驗證是收下的猜測，再加一個主模型自己的 token。vLLM 不記沒有猜測的那幾步，所以只有統計剛好對得上每個 token 時才標，而且要等這一步結束，收下的只算到停止 token 為止，和 `simple_backend.py` 一樣；被退回的猜測原本是什麼，伺服器不說。兩個模型在有 GPU 的 vLLM 伺服器上都能推測解碼，接真的伺服器的測試也全部通過：在 DGX Spark 的 GB10 上，Qwen3.5 0.8B 猜 2 個時從約 113 變成 164 tok/s，Gemma 4 E2B 猜 4 個時從約 41 變成 108 tok/s。vLLM 0.32 的 CPU 版 image 兩個都跑不了：Qwen3.5 的第一個請求會在一個 CPU 版沒有的 Triton kernel 裡讓引擎停掉（讓它的 Gated DeltaNet 狀態跟上猜測的那個），Gemma 4 的草稿模型則是載入時就要建 CUDA graph。
- **prefill** 是等到第一個 token 的時間，包含網路。vLLM 會留著和上一個 prompt 相同開頭的 KV cache（prefix caching），所以從第 2 步開始只讀新加的部分；`simple_backend.py` 則是每一步都讀完整個 prompt。有媒體時，前面那個問展開方式的請求已經讀過 prompt 的大部分了。網頁是在 token 到達時量 prefill 和解碼的時間，所以關掉了 Streamlit 每次執行完腳本後的完整垃圾回收（`.streamlit/config.toml`）：它會佔住 GIL 最多四分之一秒，剛好發生在送出問題時和每次重畫時，這一步的 token 就會一口氣到達網頁，算出每秒幾千個 token。
- **模型分頁**寫出伺服器和它的版本；規格來自 `config.json`，脈絡上限來自伺服器。裝置、精度和參數量是伺服器的，這裡不顯示；模型資料夾卡片把權重列成「只在伺服器上」。
- **和 `generate()` 不一定一樣**：vLLM 會把請求合成一批跑，也有自己的 kernel，所以 greedy 的輸出不一定和 `transformers` 逐 token 相同；`simple_backend.py` 的會。

[運作說明](https://agentic-system-lab.github.io/agent-loop-visualizer/zh/)在兩個 backend 做法不一樣的每一步，從它們各自讀 `models/` 裡的哪些檔案到 MTP，都用頁籤分開說明，另有一段講它們共用的 `Backend` 介面，都附上程式碼。

## 由網頁在 Docker 裡啟動 vLLM

沒設 `VLLM_URL` 時，側欄的「用什麼跑模型」可以在 transformers 和 vLLM (Docker)之間切換。選 vLLM 時，網頁先放掉在這裡載入的模型（`release_model()` 清掉快取、把記憶體還給系統；在 CUDA 上連 cuBLAS 的工作區也放掉，不然整個模型的記憶體都還不回去。Streamlit 的 fast reruns 關掉了，所以模型載入到一半時切換的設定，要等載入完才生效），接著 `agent/model_backends/vllm_docker.py` 把還沒下載的模型下載到 `models/`，用 `docker compose up -d` 啟動 `docker-compose/` 裡的伺服器，等待時顯示 Docker 和 vLLM 印出的內容。換回 transformers 或結束這個程式（Ctrl+C）時執行 `docker compose down`，所以兩邊不會同時佔著模型。「用什麼跑模型」也和記憶體裡的模型一樣，是所有分頁共用的一個選擇：停在 transformers 的分頁，會跟著另一個分頁換到 vLLM 或換回來；新開的分頁或重新整理，也會接上正在跑的伺服器和它的模型，不會在這裡再載入一份。在 vLLM 上換模型會再跑一次 `docker compose up`，它會換掉容器；伺服器已經在跑時，重跑頁面不會再啟動一次。啟動失敗（沒有 Docker、Docker 沒在執行、記憶體不夠）時，頁面用目前的語言說明原因，要按「再試一次」才會重試；換回 transformers 的切換鈕一直留在側欄。

```bash
# 自己啟動同一台伺服器（VLLM_MODEL 和 VLLM_REVISION 預設是 Qwen3.5 0.8B 和它固定的 commit）；權重要先在 models/ 裡（just download Qwen/Qwen3.5-0.8B，或 VLLM_MODEL 指定的模型）：
just vllm-up                              # 在 CPU 上，任何機器都行
just vllm-up gpu                          # 在 NVIDIA GPU 上（Linux，要有 NVIDIA Container Toolkit）
VLLM_URL=http://localhost:8000 just run
just vllm-down                            # 停掉伺服器
```

沒有 just 的話，`just vllm-up` 就是 `docker compose -f docker-compose/compose.yaml up -d`，`just vllm-up gpu` 在第一個檔案後面再加上 `-f docker-compose/compose.gpu.yaml`，`just vllm-down` 則是 `docker compose -p agent-loop-vllm down`。

- **在哪裡跑。** Docker 有 nvidia runtime 時，再疊上 `compose.gpu.yaml`，用 vLLM 官方的 CUDA image（`vllm/vllm-openai:v0.32.0`）在 GPU 上跑；其他情況（Mac 也是）由 `compose.yaml` 在 Docker 的 Linux 虛擬機裡跑 vLLM 的 CPU image。`AGENT_LOOP_VLLM_DEVICE=cpu` 或 `gpu` 可以直接指定，`VLLM_PORT` 可以換埠號（8000）。在 GPU 上 KV cache 和 CPU 上一樣是 2 GiB（`--kv-cache-memory-bytes`、`VLLM_KV_CACHE_MEMORY_BYTES`），不是 GPU 記憶體的 92%；vLLM 啟動時也只要求 30% 的記憶體是空的（`--gpu-memory-utilization`、`VLLM_GPU_MEMORY_UTILIZATION`）：照它預設的 0.92，小張的顯示卡旁邊還有網頁自己的 CUDA context 時會拒絕啟動，和整台電腦共用記憶體的 GPU（例如 DGX Spark）也是。
- **MTP。** 在 GPU 上，伺服器預設會推測解碼：Gemma 4 用它的草稿模型，Qwen3.5 用它自己 checkpoint 裡的 MTP 層（`model_families.VLLM_SPECULATIVE`，用 `VLLM_SPECULATIVE_CONFIG` 交給 Compose），每一步收下的猜測都會加上底線。側欄的 MTP 開關可以關掉或再打開，會用另一種方式重新啟動伺服器，每個分頁也都會跟著。vLLM 0.32 的 CPU 版 image 兩個模型都不能推測解碼，所以在 CPU 上開關不能按，也會說明原因。手動啟動 GPU 版時不開。
- **伺服器讀什麼。** 它自己不下載：`models/` 唯讀掛進去、設了 `HF_HUB_OFFLINE=1`，所以載入的正是 `REVISIONS` 裡的那個 commit，和網頁一樣。它跟網頁一樣只聽 127.0.0.1。啟動時加了 `--enable-scale-out`，所以看得到每個 token 的排名，伺服器也收圖片、聲音和影片；`--logprobs-mode` 維持 vLLM 預設的 `raw_logprobs`，浮窗顯示的是模型自己的機率和前 5 名。vLLM 編譯的結果存在一個 Docker volume，所以一個模型只有第一次啟動要編譯。
- **CPU 版的 image**（`docker-compose/vllm-cpu/`）是 `vllm/vllm-openai-cpu:v0.32.0` 加上兩個修正（`patch_vllm.py`）：vLLM 自己的 #61992，晚了 0.32.0 一天才進去，沒有它的話每個模型在 CPU 上的第一個請求都會失敗；另一個是我們自己的，讓 CPU 上線性層的輸入在記憶體裡是連續的，沒有它的話 Gemma 4 聽的第一段聲音就會讓 engine 當掉。在 CPU 上，`compose.yaml` 把 KV cache 設成 2 GiB（`VLLM_CPU_KVCACHE_SPACE`；不設的話 vLLM 要 Docker 記憶體的 92%），啟動時不量圖片編碼器要多少記憶體（在 CPU 上要超過 10 分鐘），並讓一步最多可以跑 30 分鐘，而不是 vLLM 預設的 5 分鐘就放棄 engine。
- **在 DGX Spark 上**（NVIDIA GB10，GPU 和整台電腦共用 128 GB 記憶體）：在 GPU 上，Qwen3.5 0.8B 啟動約 2 分鐘、解碼約 113 tok/s，Gemma 4 E2B 啟動約 3 分鐘、解碼約 41 tok/s，兩個模型都通過接真的伺服器的測試，包括 Gemma 讀得懂的每種媒體。照 vLLM 預設的 `gpu_memory_utilization`（0.92），伺服器在這台電腦上不肯啟動：vLLM 把整台電腦可用的記憶體當成 GPU 空著的記憶體，大約是 122 GiB 裡的 108 GiB。在同一台電腦的 CPU 上，Qwen3.5 0.8B 啟動約 1.3 分鐘、解碼約 23 tok/s。
- **在 Mac 上**（Apple M5，給 Docker 10 個核心）：Qwen3.5 0.8B 啟動約 1.5 分鐘，佔 Docker 約 9 GB 記憶體，解碼約 10 tok/s。Gemma 4 E2B 要的記憶體比 Docker Desktop 預設的多：16 GB 時載入到一半會被停掉（頁面會說明，也說怎麼給 Docker 更多記憶體），24 GB 時 3 到 5 分鐘啟動、解碼約 4.6 tok/s，但載入時問伺服器收哪些媒體，要在 CPU 上跑它的圖片、聲音和影片編碼器，第一次要花大約 10 分鐘。
