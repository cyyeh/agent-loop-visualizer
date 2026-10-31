<img src="app/assets/logo.svg" alt="" width="72">

# Agent Loop 可視化

[English](README.md) | 繁體中文

![上方可以切換到「運作說明」頁，右上角可以切換語言，側欄可以選用什麼跑迴圈（內建 harness 或 pi）、模型和用什麼跑它；左邊是對話，輸入框上方是可以拿來問的範例檔案，右邊是迴圈圖與第 1 步的 token。滑鼠停在 <|tool_call> 這個特殊 token 上，浮窗說明它的用途，並顯示它的機率、排名與前 5 名候選](docs/screenshot-zh.png)

這個專案是學習用的：用更直覺、更視覺化的方式，讓你看懂 agent 迴圈在底層怎麼運作。Agent 的聊天框背後跑著一個迴圈：一步接著一步，模型提出動作、harness 去執行，直到停止。一般的聊天 app 只讓你看到問題和答案；這個網頁在每一步發生的當下把它畫出來，細到模型寫下的每一個 token，整個機制攤開在你眼前。畫面上的每個部分都對應 [Agent Atlas 技術與實戰交流](https://agentic-system-lab.github.io/agent-atlas-learning/) unit 01 導讀的一節，本專案就是它的專案之一；[可以試試看的實驗](#可以試試看的實驗)則把這些概念變成可以自己動手試的實驗。

- **模型**：側欄可以選 [google/gemma-4-E2B-it](https://huggingface.co/google/gemma-4-E2B-it) 或 [Qwen/Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B)，在本機用 Hugging Face `transformers` 推論，或用 [vLLM](https://docs.vllm.ai/) 跑：由側欄在 Docker 裡啟動，或連到你自己的伺服器（「[在 vLLM 上跑模型](docs/vllm.zh-TW.md)」）。兩個模型跑的是同一個 harness，換模型時只有它們的文字格式不同，正好可以對照
- **Harness**：這個專案自己寫的迴圈（`agent/harnesses/simple_harness.py`），或是 [pi](https://pi.dev) 這個 coding agent 的迴圈；pi 可以問這個網頁的模型，每個 token 照樣畫出來，也可以問 Claude、GPT 或其他它登入過的模型，這時照 pi 回報的事件畫出每一步，看不到 token（「[pi 當 harness](docs/pi.zh-TW.md)」）
- **MTP 推測解碼**：一次 forward 產生好幾個 token；用 `transformers` 時 Gemma 4 E2B 搭配它的草稿模型（預設關閉，在側欄打開），在有 GPU 的 vLLM 上兩個模型都可以（「[解碼迴圈與 MTP](docs/decoding.zh-TW.md)」）
- **檔案**：附上圖片和影片（兩個模型都行）、聲音（Gemma 4 E2B，也可以直接用麥克風錄音），或在輸入框上方選一個範例檔案；打開「讓模型寫程式」時，模型多一個 `run_python` 工具，在 Docker 沙箱裡執行，讀得到你附上的資料檔，也能畫圖（「[附件與程式沙箱](docs/files.zh-TW.md)」）
- **兩種語言**：網頁和運作說明都有繁體中文和英文版，預設跟著瀏覽器的語言，右上角可以切換
- **[運作說明](https://agentic-system-lab.github.io/agent-loop-visualizer/zh/)**：把一輪對話的每一步對應到做這件事的程式碼，每段程式片段點一下就能在 GitHub 上看到那幾行；app 上方的「運作說明」會用網頁當下的語言打開它

## 畫面上看得到什麼

| 畫面 | 看得到的東西 | 對應 unit 01 導讀 |
|---|---|---|
| 迴圈圖 | 目前在脈絡、模型、harness、環境、停止哪一格，正在流動的箭頭 | §4 Agent 就是放在迴圈裡的模型 |
| 脈絡 | 每一步模型讀到的完整字串（pi 問 provider 的模型時，改成 pi 送出的請求，寫成 JSON）：system prompt、工具 schema、對話，以及上一步接回來的工具結果。滑過深色的特殊 token 會說明它的用途。附上的圖片、聲音或影片就是它展開成的那一串 token，畫成一個標籤加上個數（`<\|image\|>` ×266） | §1 脈絡有上限、§3 工具定義也是 token |
| 模型 | 每個生成的 token，顏色越深代表被選中的 token 機率越低。滑過 token 看機率、排名、前 5 名候選，以及 top-k / top-p 剃掉了哪些。打開 MTP 時，草稿模型猜中的 token 有底線，step 卡片顯示收下幾個。用 vLLM 時，看得到多少要看伺服器開了哪些參數；pi 問 provider 的模型時，只有一段段傳回來的文字 | §1 LLM 是會抽樣的條件機率分布、解碼設定 |
| Harness | 從模型自己的格式（Gemma 4 或 Qwen3.5）解析出的工具呼叫、schema 驗證結果、重複呼叫警告、你的允許或拒絕 | §3 模型從不直接碰環境 |
| 環境 | 工具實際回傳的結果與耗時；`run_python` 的程式碼寫在上面，印出來的東西或 traceback 寫在下面 | §2 環境與可觀察的狀態 |
| 停止 | 停止原因和停止 token。Gemma 回答完停在 `<turn\|>`（相當於 end_turn）、要工具時停在 `<\|tool_response>`（相當於 tool_use）；Qwen 兩種都停在 `<\|im_end\|>`。另外還有步數上限、token 上限、使用者中斷 | §5 什麼時候停 |
| 模型分頁 | 參數量拆解、層數、注意力頭數和脈絡上限、模型讀得懂什麼、MTP 草稿模型、解碼設定的說明、每一步的 prefill 時間與 tok/s、tokenizer 全部特殊 token（Gemma 24 個、Qwen 33 個），以及 `models/` 裡這個模型資料夾的每個檔案和裡面裝了什麼 | §1、§7 Agent 是系統 |
| 運作說明頁 | 一輪對話的 18 個階段，每段附上做這件事的程式碼，連到 GitHub 上產生頁面時那個 commit 的那幾行，模型、backend 或 harness 做法不同的地方各有頁籤；每次推上 main 都會重新產生，程式改了會跟著更新 | 全部 |

## 快速開始

需求：

- macOS（Apple Silicon）、有 CUDA 的 Linux（`nvidia-smi` 的 CUDA Version 要 13.0 以上），或只用 CPU（很慢）
- 磁碟：Gemma 4 E2B 約 10 GB，Qwen3.5 0.8B 約 1.8 GB。記憶體：Gemma 要 16 GB 以上（只用 CPU 時 24 GB），Qwen 8 GB
- [uv](https://docs.astral.sh/uv/) 0.13.4 以上（用 `uv self update` 更新）、[just](https://github.com/casey/just#installation)（`brew install just`），以及網路
- 選用：[Docker](https://docs.docker.com/get-started/get-docker/)，讓模型寫程式或用 vLLM (Docker) 跑模型時才需要；[pi](https://pi.dev) 和 Node.js 22.19 以上，要把迴圈交給 pi 時才需要

```bash
just sync       # Python 3.12 和鎖定版本的套件
just download   # 照固定的 commit 下載 Gemma 4 E2B（約 10 GB）、Qwen3.5 0.8B（1.8 GB）和 Gemma 的 MTP 草稿模型（190 MB）；跳過的話，模型第一次選到時、草稿模型第一次打開 MTP 時會自動下載
just run        # 啟動 app，預設先載入 Gemma；MODEL_ID=Qwen/Qwen3.5-0.8B just run 先載入 Qwen
just sandbox    # 選用：「讓模型寫程式」用的沙箱（約 400 MB）；agent/sandbox/Dockerfile 改了要再建一次
```

瀏覽器會打開 http://localhost:8501 ；第一次載入 Gemma 大約 10–20 秒，Qwen 幾秒。`just` 會列出全部的指令，`just download Qwen/Qwen3.5-0.8B` 只下載指定的模型。想改用 vLLM 跑模型，可以在側欄的「用什麼跑模型」選 vLLM (Docker)，或用 `VLLM_URL` 連到你自己的伺服器（「[在 vLLM 上跑模型](docs/vllm.zh-TW.md)」）。每個 just 指令背後都只是一兩行你也能自己打的指令，所以 just 只是為了方便：「[安裝與設定](docs/setup.zh-TW.md#用-just-跑這些指令)」列出每個指令背後的那一行，也說明模型放在哪裡、網頁怎麼檢查沙箱，以及下載時出現 401 怎麼辦。

## 可以試試看的實驗

1. **只是聊天機器人**：在側欄關掉「使用工具」，問「台北現在幾點？」。模型看不到任何工具，只能猜或承認不知道。打開工具再問一次，比較兩次的脈絡分頁。
2. **抽樣**：同一個問題，temperature 設 0 和 1.5 各跑一次，看 token 的顏色和浮窗裡「剩下的候選」怎麼變。
3. **停止條件**：步數上限設 1，問一個需要工具的問題，停止原因會變成「達到步數上限」。
4. **人的位置**：打開「執行工具前先問我」，然後按「拒絕」。擋下來的是 harness，模型只會在下一步的脈絡裡看到一則錯誤觀察。對照導讀 §5 郵件刪除事件：寫在 prompt 裡的「先確認」會被壓縮掉，寫在 harness 裡的不會。
5. **推理也是 token**：打開「思考模式」，斜體的思考 token 會出現在工具呼叫之前；脈絡分頁裡 system turn 的開頭會多一個 `<|think|>`。
6. **迴圈會打轉**：問「ReAct 這篇論文是誰提出的？用 Wikipedia 查。」。E2B 常常重複同一個搜尋，harness 會標出「跟之前一模一樣的呼叫」，對照導讀 §4 ReAct 的錯誤分析。
7. **換模型，harness 不變**：同一個問題分別問 Gemma 和 Qwen，打開脈絡分頁比較：回合標記（`<|turn>` 對 `<|im_start|>`）、工具 schema 放的位置、工具呼叫的寫法（`call:名稱{…}` 對 XML）、工具結果接回的位置都不一樣，但 step 卡片裡的 harness、環境、停止判斷完全相同。
8. **MTP：猜得中才會快**：在 Gemma 打開「MTP 推測解碼」，按「台北現在幾點？紐約呢？」，在關著「讓模型寫程式」時輸入「Write a Python function to test for primes.」，再問「用三段話介紹台北。」。比較每一步的 tok/s 和底線：工具呼叫幾乎每個 token 都被草稿猜中，英文程式碼約一半，中文長文只有一成左右。把 temperature 設成 0 再開關 MTP 各跑一次，輸出會一模一樣：草稿模型只決定要跑幾次 forward，不決定寫出什麼。
9. **圖片也是 token**：按收據的範例。在 step 卡片的脈絡段和脈絡分頁裡，這張圖是幾百個 `<|image|>`（Gemma）或 `<|image_pad|>`（Qwen），這就是它在脈絡裡的成本。品項加起來是 360，收據上卻寫 370；看看模型是自己加，還是呼叫工具。
10. **脈絡決定模型聽不聽**：用 Gemma 在中文頁按錄音的範例，它會把那句英文寫下來再翻譯。換到英文頁、開著「使用工具」問「Transcribe this recording.」，它常說自己聽不到聲音，有時還已經把那句話寫進了工具呼叫的參數；關掉「使用工具」再問一次，它就寫出來了。模型和聲音的 token 都一樣，只有脈絡不同。
11. **在沙箱裡寫程式**：打開「讓模型寫程式」（需要 Docker），按銷售資料的範例。你的訊息最後多了一段說明，寫著檔案的路徑和第一行；step 卡片寫出模型的程式碼，沙箱印出來的東西或 traceback 當作觀察接回去，程式出錯的話模型下一步可以改。也換 Qwen 試試：它通常算得出每個月的合計，接著卻把自己的程式寫壞。
12. **圖是給你看的，不是給模型**：打開「讓模型寫程式」，在輸入框上方的範例檔案選 sales.csv，請它畫出每個月的營收。圖出現在聊天區和畫它的那一步底下，模型讀到的觀察卻只有 `{"figures": ["/data/figure-1.png"]}`：它在描述一張自己沒看過的圖。

## 說明文件

| 頁面 | 內容 |
|---|---|
| [安裝與設定](docs/setup.zh-TW.md) | 完整的需求、模型放在哪裡、沙箱 image、用 just 跑指令、疑難排解 |
| [架構](docs/architecture.zh-TW.md) | 兩個套件和它們的檔案、一輪的事件、兩種語言、加入新模型、兩個模型的格式 |
| [解碼迴圈與 MTP](docs/decoding.zh-TW.md) | 為什麼自己寫解碼迴圈、MTP 怎麼猜和驗證、快了多少 |
| [附件與程式沙箱](docs/files.zh-TW.md) | 圖片、聲音和影片怎麼變成 token；`run_python` 的 Docker 沙箱和它畫的圖 |
| [在 vLLM 上跑模型](docs/vllm.zh-TW.md) | 自己的伺服器（`VLLM_URL`）和它的參數讓網頁看得到什麼；由側欄在 Docker 裡啟動的 vLLM |
| [pi 當 harness](docs/pi.zh-TW.md) | 把迴圈交給 pi，問這個網頁的模型或 pi 自己的模型 |
| [測試](docs/testing.zh-TW.md) | 指令、假的模型和假的 pi，以及每個測試檔測什麼 |
| [已知限制](docs/limitations.zh-TW.md) | 實測速度、小模型會犯的錯，以及每個 backend 和 harness 的限制 |

## 授權

本專案的程式碼以 [Apache License 2.0](LICENSE) 授權。Gemma 4 模型權重和它的 MTP 草稿模型由 Google 以 Apache 2.0 釋出（見[模型卡](https://huggingface.co/google/gemma-4-E2B-it)、[草稿模型卡](https://huggingface.co/google/gemma-4-E2B-it-assistant)），Qwen3.5 模型權重由 Alibaba 的 Qwen 團隊以 Apache 2.0 釋出（見[模型卡](https://huggingface.co/Qwen/Qwen3.5-0.8B)），都不包含在本專案裡。`app/assets/examples/speech.flac` 是 [LibriSpeech ASR 語料庫](https://www.openslr.org/12)（Panayotov 等人，2015，取自 LibriVox 的朗讀）的第 1272-128104-0000 句，以 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 授權；其他範例檔（`receipt.png`、`ball.mp4`、`sales.csv`）和 logo 是為本專案製作的。

AI 使用說明：程式碼由 Claude Code 協助撰寫，並在本機用 gemma-4-E2B-it（含 MTP 草稿模型 gemma-4-E2B-it-assistant）和 Qwen3.5-0.8B 實際執行、用瀏覽器檢查過畫面。
