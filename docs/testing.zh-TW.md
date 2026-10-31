# 測試

[English](testing.md) | 繁體中文 · [回到 README](../README.zh-TW.md)

```bash
just test               # uv run pytest：約 40 秒，不載入模型權重、不連網路
just lint               # uv run ruff check：lint，可能的 bug、沒用到的 import、import 的順序（just lint --fix 會排好）
just types              # uv run mypy：型別，agent/、app/ 和 docs/ 每個函式都檢查，tests/ 只檢查有標型別的地方
just guide-check        # 像 checks.yml 和 pages.yml 那樣，只裝 pygments 跑運作說明的測試、產生運作說明：就是下面那兩行
just check              # checks.yml 跑的：just lint、just types、just test，再跑 just guide-check
just test-models        # RUN_MODEL_TESTS=1 uv run pytest tests/test_real_model.py：載入真的 Gemma（含 MTP 草稿模型）和 Qwen，約 4 分鐘
just test-vllm          # VLLM_TEST_URL=http://localhost:8000 uv run pytest tests/test_vllm_backend.py -k real_server：問一台正在跑的 vLLM 伺服器
just test-vllm-docker   # RUN_VLLM_DOCKER_TESTS=1 uv run pytest tests/test_vllm_docker.py -k real：用 Qwen3.5 在 Docker 裡啟動 vLLM，問它一個問題
just test-pi            # RUN_PI_TESTS=1 uv run pytest tests/test_pi_harness.py -k real：啟動真的 pi（PATH 上的，或 PI_COMMAND），對上 127.0.0.1 上照劇本回答的模型，以及模型端點
```

每個名字跑的就是它後面那一行指令，所以沒有 [just](setup.zh-TW.md#用-just-跑這些指令) 也可以自己打那一行；`just guide-check` 跑的是兩行：

```bash
uv run --isolated --no-project --with pygments --with pytest pytest tests/test_guide.py
uv run --isolated --no-project --with pygments python -m docs.guide _site
```

名字後面接的參數會交給指令（`just test -k render`，`just test-models -k Qwen` 只跑 Qwen）；伺服器不在 localhost:8000 時，`just test-vllm` 後面接它的位址。

大部分測試用 `tests/fakes.py` 的假模型：它照劇本一個 token 一個 token 吐出預先寫好的輸出，和 `SimpleBackend` 一樣是一個 `Backend`（`backend.py`），所以 harness 和網頁可以從頭跑到尾。需要 pi 的地方，測試啟動的是 `tests/fake_pi.py`，它照劇本說 pi 1.4 的 RPC 協定，所以不需要 Node，也不需要模型。

網頁收的每一種檔案格式都有測試：`tests/samples.py` 用範例的檔案做出每種格式的小檔案（收據的每種圖片格式、錄音的每種聲音格式、滾動的球的每種影片格式、銷售資料的每種資料格式）。`media.py` 多收了一種格式卻沒有對應的範例檔，`test_media.py` 就會失敗；`test_real_model.py` 拿每一種格式問兩個模型。需要 Docker 的測試只在 Docker 和沙箱 image 都在時才跑。

每個 pull request 和每次推上 main，`.github/workflows/checks.yml` 都會在 Ubuntu 上跑 `ruff check`、`mypy` 和 `uv run pytest`；需要模型、沙箱 image、vLLM 伺服器或 pi 的測試在那裡會跳過。同時它也像 `pages.yml` 在 main 上那樣，只裝 pygments 跑 `tests/test_guide.py` 並產生運作說明，所以 pull request 讓這個頁面的程式 import 了 torch 或 app 其他的套件，合併前就會失敗，不會等到發佈頁面時才發現。

運作說明會引用程式碼，`tests/guide_excerpts.txt` 存著它引用的每一段程式，不含行號。改到被引用的程式時，`test_guide.py` 會失敗，並列出引用它的段落：重讀那幾段，把不再正確的說明改掉，再用 `just guide-snapshot`（`UPDATE_GUIDE_SNAPSHOT=1 uv run pytest tests/test_guide.py`）重寫這個檔案。

## 每個檔案測什麼

測試的名字都是描述行為的句子，所以一個檔案的測試名字就完整說明了它檢查什麼。

| 檔案 | 測什麼 |
|---|---|
| `test_gemma4.py` | Gemma 4 的 parser：思考、工具呼叫、回覆的切分；`<\|"\|>` 字串、巢狀參數、各種格式錯誤，兩種語言都有 |
| `test_qwen3_5.py` | Qwen3.5 的 parser：XML 工具呼叫、照 schema 轉型別、思考、各種格式錯誤；用 Qwen 格式跑完整個 harness |
| `test_model_families.py` | 每個家族都說明了它的特殊 token 和 checkpoint 裡的檔案，中英文說的一樣；`model_type` 找得到家族；token 顯示成它代表的文字；每個模型和草稿模型都照固定的 commit 下載；vLLM 推測解碼時用的是 checkpoint 裡的 MTP 層，或 transformers 用的那個草稿模型 |
| `test_tools.py` | schema 驗證、計算機的 AST 白名單、時區、Wikipedia（HTTP 用假的）；`run_python` 鎖住的 `docker run`、它的錯誤和圖，都有中英文；有 Docker 時，真的沙箱：`/data` 唯讀、沒有網路、讀得了每一種資料格式、畫得出中文標籤的圖 |
| `test_simple_backend.py` | 自己寫的解碼迴圈：KV cache、停止 token、上限、中斷、channel 切換、被拆開的中文字元、和 `generate()` 一樣處理打平、temperature / top-k / top-p；媒體經過 processor 和視覺編碼器；MTP 用照劇本猜的假草稿模型，抽樣時不改變分布；模型照固定的 revision 放在 `models/`；在 CUDA 上，先放掉 cuBLAS 的工作區再清 CUDA 的快取 |
| `test_simple_harness.py` | harness：事件順序、工具結果接回脈絡、驗證錯誤、重複呼叫、每一種停止原因、允許 / 拒絕 / 停止；錯誤用這一輪的語言；附件和給 `run_python` 的說明；圖給頁面，不給模型 |
| `test_pi_harness.py` | pi 當 harness，用 `tests/fake_pi.py` 代替 pi：一輪變成網頁的事件；pi 在這段對話的資料夾啟動、帶著側欄的工具、不帶你自己的 extension；透過 extension 先問；停止和步數上限；失敗都用兩種語言說明；透過端點問這個網頁的模型；`RUN_PI_TESTS=1` 時用真的 pi |
| `test_model_endpoint.py` | 這個網頁的模型透過 HTTP 提供給 pi：只聽 127.0.0.1、只認它的 token、一次一個請求；回覆、思考和工具呼叫照 OpenAI 的格式；每個請求畫成它的那一步；對話和 `SimpleHarness` 存的一樣 |
| `test_render.py` | 一次執行的每一個事件前綴都能用兩種語言畫出來（執行中會重畫）、HTML 標籤成對、迴圈圖是合法 SVG、模型輸出一律跳脫；token 浮窗、MTP 的標記、媒體標籤、圖、模型資料夾卡片；回報得比較少的 backend；pi 跑的一輪；英文畫面上沒有中文 |
| `test_app.py` | 用 Streamlit `AppTest` 操作整個網頁：問問題、範例、側欄設定、各個分頁、允許 / 拒絕 / 停止、新對話、換模型、分頁之間一次只跑一個、語言切換、附件和沙箱；設了 `VLLM_URL` 時，伺服器的模型、參數、媒體和錯誤；Docker 裡的 vLLM 的啟動、接上、切換和停止；pi 問兩種模型 |
| `test_chat_template.py` | 用每個模型真的 tokenizer 和 chat template（已經下載到 `models/` 才跑）：每個特殊 token 都是單一 token 而且有說明、歷史裡的工具呼叫讀得回來、step 卡片標成「新加入」的剛好是工具結果，附上媒體時也一樣；模型資料夾裡的每個檔案都有說明 |
| `test_vllm_backend.py` | vLLM backend 對上一個說 vLLM 0.32 串流格式的假伺服器：prompt 一模一樣的 token id 和設定；兩條路上的機率、排名和前 5 名；載入時判斷 sampling mask 和 `--logprobs-mode`；媒體和它的展開；MTP 的統計和標記；兩種語言的錯誤；伺服器提供的模型屬於哪個家族；用真的 tokenizer 時 prompt 一模一樣；設了 `VLLM_TEST_URL` 時問真的伺服器 |
| `test_vllm_docker.py` | 在 Docker 裡啟動 vLLM，Docker 在 `subprocess` 這一層換成假的：先下載權重、用對的檔案 `docker compose up`、伺服器沿用或換掉、每一種失敗都用兩種語言說明、切換時和結束時 `docker compose down`、只在 GPU 上開 MTP；compose 檔只聽 127.0.0.1、唯讀又離線；`RUN_VLLM_DOCKER_TESTS=1` 時用真的伺服器 |
| `test_media.py` | 網頁收的每一種格式都有範例檔、被當成正確的種類（聲音對 Qwen 是一般檔案）、解碼得出來；存檔的名字不重複也不含奇怪字元；問題的 part 和寫出文字檔欄位名稱的說明；照片轉正、聲音改成模型的取樣率、影片畫格平均取 |
| `test_guide.py` | 運作說明頁的每個程式片段和行號都找得到，並連到 GitHub 上頁面那個 commit 的那幾行；事件表指向真的送出事件的那一行；引用的程式和 `tests/guide_excerpts.txt` 一致；中英文指向同樣的程式；沒有 script 也切換得了頁籤；產生的頁面有亮色和暗色兩套配色，並把讀者送到他們的語言 |
| `test_layout.py` | `agent/` 裡沒有任何檔案 import `app` 或 Streamlit，不論寫在檔案開頭還是函式裡，從每個檔案的語法樹讀出來：agent 不認識網頁 |
| `test_real_model.py` | 預設跳過。每個模型：greedy 解碼和 `model.generate()` 一致，純文字和附上媒體都一樣；真的模型會呼叫工具、讀得出收據、聽得懂錄音（Gemma）、看得出球往哪邊滾、打得開每一種資料格式；Gemma 開 MTP 時 greedy 輸出不變；在 CUDA 上 GPU 記憶體全部還回去；裝了 pi 的話，真的 pi 透過端點問這個模型 |
