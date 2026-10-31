# 已知限制

[English](limitations.md) | 繁體中文 · [回到 README](../README.zh-TW.md)

## 速度與 MTP

- 速度：Apple M5（32 GB）上 Gemma 大約 7–13 tok/s，Qwen3.5 0.8B 大約 20–25 tok/s。思考模式一步常有兩、三百個思考 token，要等 30 秒左右。打開 MTP 後，工具呼叫這類好猜的步驟大約快 3 倍，中文長文幾乎沒有差別（見「[MTP 推測解碼](decoding.zh-TW.md#mtp-推測解碼)」的表）。
- MTP 在網頁裡跑長回覆時，加速比單獨跑 `simple_backend.py` 少很多（英文程式碼：單獨跑 8 → 29 tok/s，網頁裡 9 → 12 tok/s），原因還沒查清楚。可能是網頁每 0.5 秒重畫一次、瀏覽器和模型搶同一台機器，而 MTP 每一輪有好幾個很小的草稿 forward，比一般解碼更容易被這些干擾拖慢。
- 用 transformers 時 MTP 只有 Gemma 4 E2B 能開：`transformers` 目前只支援 Gemma 4 的草稿模型讀主模型 KV cache 的這種做法，Qwen3.5 沒有對應的草稿模型。在有 GPU 的 vLLM 伺服器上，Qwen3.5 也可以，用的是它自己 checkpoint 裡的 MTP 層（見「[在 vLLM 上跑模型](vllm.zh-TW.md)」）。
- 開 MTP 時，主模型一次算 7 個位置，數值和一次算 1 個會有極小的差異；greedy 遇到兩個 token 機率幾乎一樣時，偶爾會選到不同的那個。
- Qwen3.5 的 24 層裡有 18 層是 Gated DeltaNet。transformers 有兩個加速 kernel：`flash-linear-attention`（Triton）和 `causal-conv1d`（CUDA），都要有 CUDA GPU 才能用，所以都不列為依賴：改用 PyTorch 參考實作，結果一樣，只是比較慢；`simple_backend.py` 在所有裝置上都把 transformers 這個「改用參考實作」的提示關掉了。有 GPU 時，對 0.8B 的模型差別不大：在 NVIDIA GB10（DGX Spark）上，裝了 flash-linear-attention 後 prefill 快了約 4 倍（3,571 個 token 從 368 ms 變成 93 ms），decode 幾乎沒變（56 → 60 tok/s），兩種寫法和 float32 的差距也一樣小。causal-conv1d 在那台機器上沒有 wheel，得自己編譯。沒有 GPU 的 Linux 不要裝 flash-linear-attention：transformers 還是會選它，第一次 forward 就會失敗。
- 在 MPS 上，transformers 用多條 thread 載入 Qwen3.5 的權重會卡住，所以 `simple_backend.py` 在 MPS 上改成單一 thread 載入（`HF_DEACTIVATE_ASYNC_LOAD=1`），兩個模型的載入時間都沒有變慢。

## 模型

- Qwen3.5 0.8B 官方預設不開思考模式；開了容易一直想下去停不下來，可以把「每步 token 上限」調低。它沒附 generation_config.json，建議的解碼設定寫在 `agent/model_families/qwen3_5.py`（官方建議的 presence penalty 這裡沒有實作）。
- 兩個模型都很小：可能用簡體中文回答、重複同一個搜尋、只回答一半的問題，或在思考裡算錯。用英文一次問兩個城市的時間時，Gemma 會呼叫兩次工具，然後多半改用中文回答，或在工具結果之後直接停下、沒有回覆；只問一個城市就會用英文回答。這些剛好是可以觀察的材料。
- 只有 Gemma 4 E2B 聽得到聲音，而且只聽前 30 秒。兩個模型都聽不到影片的聲音：影片就是一張張畫格。每張畫格都要 token：Gemma 不管影片多長都取 32 張，約 2,000 個 token 的 prefill；Qwen 每秒取 2 張，token 數跟著影片長度增加（8 秒的範例影片是 640 個）。
- 用英文問、又開著「使用工具」時，Gemma 4 E2B 常說它聽不到附上的錄音，有時還已經把那句話寫進了工具呼叫；用中文問，或關掉「使用工具」，它就寫得出來。所以英文的錄音範例問的是「說了什麼」而不是要它逐字寫下，大約三次成功兩次。
- Qwen3.5 0.8B 用 `run_python` 打得開每一種資料格式，但很少寫對好幾步的 pandas 程式；銷售資料的範例 Gemma 4 E2B 答得出來。
- `MODEL_ID` 環境變數決定一開始選哪個模型，也可以指定選單裡沒有的 checkpoint，只要它屬於已經支援的家族（Gemma 4 或 Qwen3.5）；其他家族要先照「[支援更多模型](architecture.zh-TW.md#支援更多模型)」加一個 family。

## 網頁

- 記憶體裡同時只放一個模型。兩個分頁選了不同的模型時，輪流在兩邊操作會一直重新載入，最好所有分頁用同一個模型。
- 只有一份模型，一次只能跑一個 agent，其他分頁要等。執行中重新整理或關掉分頁，agent 不會跟著停；其他分頁（包括重新整理後的同一頁）會顯示它還在跑，並提供「停止那個 agent」按鈕。
- 開著「執行工具前先問我」時，等確認超過 5 分鐘沒有回應，harness 會當作拒絕並停止迴圈，停止原因顯示「等待確認逾時」。
- token 浮窗要等那一步生成完才會出現，生成中只有熱度顏色（特殊 token 的用途說明除外），避免每次重畫都送出大量 HTML。浮窗是純 CSS，太靠近時間軸底部的 token，浮窗可能被切到。
- 特殊 token 的說明浮窗用 CSS anchor positioning 貼在 token 旁邊，不會被捲動框切到；不支援的瀏覽器會改成直接開在 token 下方，靠近框的底部時可能被切到。
- 對話裡的聲音和影片用瀏覽器自己的播放器播放；Safari 播不了 MKV 影片，所以 MKV 改成顯示模型讀到的其中 4 張畫格。
- 每個附件最大 50 MB。附件留在 `~/.cache/agent-loop-visualizer/uploads/`，直到按「新對話」或換模型；直接關掉分頁的話，資料夾會留著。
- Wikipedia 工具需要網路。

## 沙箱

- 沙箱沒有網路，模型沒辦法 `pip install`；裡面有 numpy、pandas、openpyxl、tabulate 和 matplotlib。每次呼叫都是新的容器，變數和 `/tmp` 裡的檔案都不會留到下一次，只有畫的圖存在這段對話的資料夾。
- 模型看不到自己畫的圖：圖送到頁面，不進脈絡，所以它對圖的描述來自自己的程式和數字。用 `plt.savefig()` 存檔後又關掉的圖不會送回來；`plt.show()` 過或留著沒關的才會。

## vLLM

- 在 vLLM 伺服器上（`VLLM_URL`）greedy 的輸出可能和 `generate()` 不同，畫面看得到多少要看伺服器加了哪些參數（見「[網頁看得到什麼](vllm.zh-TW.md#網頁看得到什麼)」）：沒加 `--enable-scale-out` 時模型只讀文字，token 浮窗要嘛有模型自己的機率和前 5 名（預設），要嘛在 `--logprobs-mode processed_logprobs` 下（`--return-sampling-mask` 一定要它）有取樣時的機率和剩下幾個候選，兩者不會同時有；前 5 名哪些被剃掉，除了 greedy 解碼都看不到；開了 sampling mask 的伺服器不接受 greedy 和不限的 top-k。MTP 猜中的 token 要等這一步結束、而且伺服器的統計對得上每個 token 才有底線，被退回的猜測原本是什麼也看不到。有媒體時，每一步都先問伺服器怎麼展開，多一個讀 prompt 的請求。網頁看不到伺服器載入的是哪個 revision，所以啟動時要照「[自己的伺服器](vllm.zh-TW.md#自己的伺服器)」加上 `--revision`。
- `vllm_backend.py` 照 vLLM 0.32 原始碼裡的協定寫，測試用的是說這些協定的假伺服器、真的 tokenizer 和真的網頁；`/inference/v1/generate`、它的 sampling mask 和每一步的統計在 vLLM 裡標示為實驗性功能，之後可能會改。對真伺服器的測試（`VLLM_TEST_URL`）只在一種 GPU 上跑過：DGX Spark 的 GB10。
- 在 Mac 上，Docker 裡的 vLLM 是用 CPU 跑，而且慢：Gemma 4 E2B 解碼約 4.6 tok/s，Docker 要有大約 20 GB 以上的記憶體，第一次載入還要花大約 10 分鐘跑它的媒體編碼器，看伺服器收哪些媒體。`compose.gpu.yaml` 只在一種 NVIDIA GPU 上跑過：DGX Spark 的 GB10。CPU 版的 image 修改了 vLLM 0.32.0（`docker-compose/vllm-cpu/patch_vllm.py`）；新版的 vLLM 可能兩個修正都不需要，要修改的程式和寫它時不一樣的話，建 image 時會停下來。
- 用 Ctrl+C 或 SIGTERM 結束程式時，會停掉 vLLM 的容器。用別的方式結束（關掉終端機、`kill -9`）的話，容器會繼續跑、佔著模型，要用 `docker compose -p agent-loop-vllm down`（`just vllm-down`）停掉。

## pi

- pi 問它自己的模型時，網頁只看得到 pi 回報的東西：沒有 token、機率和特殊 token，也看不到模型讀到的字串，只有 pi 送出的請求。token 數是 provider 報的，tok/s 是回覆傳回來時量的（含網路），費用是照 pi 目錄裡的價格估的。pi 自己的模型是 provider 的：要花錢，對話也會送到那個 provider。
- pi 問這個網頁的模型時，family 解析不出來的工具呼叫不會送給 pi，pi 的這一輪就停在那裡：不像內建 harness，沒有人告訴模型哪裡寫錯。pi 的 system prompt 和工具 schema 是寫給大模型的，Gemma 4 E2B 和 Qwen3.5 0.8B 照著做的程度比不上內建 harness 的 prompt。pi 只送圖片這一種媒體，所以給 pi 的聲音和影片只是它資料夾裡的一般檔案。不屬於任何一步的請求（例如 pi 壓縮很長的對話）最多等 10 秒，之後照樣回答，但不畫出來。
- pi 的工具在這台電腦上執行，沒有沙箱；打開 bash 的話，你做得到的事模型都做得到。打開「執行工具前先問我」，每個呼叫都會先給你看。
- `pi_harness.py` 照 pi 1.4 的 RPC 協定寫，根據它的文件和 pi 1.4.0 實際送出的紀錄；真 pi 的測試只用 pi 1.4.0 跑過。pi 1.4 需要 Node.js 22.19 以上：Node 太舊的話它啟動不了，網頁會顯示它說了什麼。網頁最多每分鐘問一次 pi 有哪些模型；在 pi 裡登入 provider 之後，按「再試一次」就會列出來。
