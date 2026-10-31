# 架構

[English](architecture.md) | 繁體中文 · [回到 README](../README.zh-TW.md)

專案分成兩塊。`agent/` 跑一輪：跑 agent 迴圈的 harness、工具、模型家族，以及跑模型的那一層。`app/` 是你看到的東西：網頁，以及它從 agent 的事件畫出來的 HTML；`docs/guide/guide.py` 再用它們產生運作說明。兩塊的依賴只有一個方向：`app/` 建在 `agent/` 上面，`agent/` 裡沒有任何東西 import `app/` 或 Streamlit（`test_layout.py` 會檢查），所以迴圈不需要網頁就能跑、也能測。

```
streamlit_app.py       Streamlit 從這裡開始：每次重跑都執行 app/page.py 的 main()
justfile               替這些指令取的名字，給 just 用
app/                   你看到的東西，站在 agent 上面
  page.py              版面、session state、模型選單、語言切換、背景 thread；執行中每 0.5 秒重畫一次
  render.py            把事件列表轉成 HTML：迴圈圖、step 卡片、token 熱度與浮窗、脈絡檢視
  assets/              網頁的樣式，運作說明也用；logo.svg；examples/ 是範例附上的檔案，也是輸入框上方的範例檔案
agent/                 跑一輪的東西：harness、模型、跑模型的那一層、工具；從不 import Streamlit
  harnesses/           跑迴圈的那一層
    harness.py         網頁透過它跑一輪的 Harness：run、stop、decide，以及每個 harness 送出的事件
    simple_harness.py  這個專案的迴圈：組 prompt → 生成 → 解析 → 驗證 →（先問你）→ 執行工具 → 接回脈絡 → 判斷要不要停
    pi_harness.py      pi 當 harness：用 RPC 模式跑 pi，把它的 JSON 紀錄翻成網頁的事件
    pi_extension.ts    網頁讓 pi 載入的 extension：回報 pi 送出的每個請求、註冊這個網頁的模型、在 pi 執行工具前先問你
    model_endpoint.py  把這個網頁的模型當成 127.0.0.1 上相容 OpenAI 的端點提供給 pi：render、encode、生成，再把 token 傳回 pi
  model_backends/      跑模型的那一層
    backend.py         harness 和畫面透過它使用模型的 Backend：render、encode、generate，以及 token 事件的欄位
    simple_backend.py  本機推論，自己寫的解碼迴圈；MTP 的草稿與驗證也在這裡
    vllm_backend.py    在 vLLM 伺服器上跑模型（VLLM_URL）：prompt 在這裡 render、切 token，token id 送給伺服器，它對每個 token 說得出的都傳回來；伺服器加了對應的參數時，還有媒體、sampling mask 和 MTP 的猜測
    vllm_docker.py     側欄選 vLLM (Docker)時在 Docker 裡跑 vLLM：用選的模型 docker compose up、等它能回應；換回時 docker compose down
  model_families/      跟著模型走的東西：每個模型家族怎麼寫回合、思考、工具呼叫，哪些 token 會停、各是什麼意思
    __init__.py        Family 的定義、模型選單 MODELS、MTP 草稿模型 DRAFTERS、依 config.json 的 model_type 找家族
    gemma4.py          Gemma 4：輸出的 parser 與 24 個特殊 token 的說明
    qwen3_5.py         Qwen3.5：輸出的 parser 與 33 個特殊 token 的說明
  tools.py             工具：schema（給模型看）加上 Python 函式（給 harness 執行）；run_python 的 Docker 沙箱
  media.py             附件：存檔、寫進使用者訊息，把圖片、聲音、影片解碼給 processor
  i18n.py              兩種語言：pick() 依語言挑文字，from_locale() 從瀏覽器語言決定預設；模型讀到的錯誤訊息也用它
  sandbox/             run_python 的沙箱：Dockerfile（Python 3.12 加上 numpy、pandas、openpyxl、tabulate、matplotlib），以及把圖送回來的 matplotlib backend 和設定
docker-compose/        網頁在 Docker 裡啟動的 vLLM 伺服器
  compose.yaml         在 CPU 上跑 vLLM（任何機器，Mac 也行），只聽 127.0.0.1，models/ 唯讀
  compose.gpu.yaml     疊在 compose.yaml 上：用 vLLM 的 CUDA image 在 NVIDIA GPU 上跑
  vllm-cpu/            vLLM 0.32.0 的 CPU image，補上它缺的兩個修正（patch_vllm.py）
docs/                  這些說明頁，每頁都有英文版和中文版（.zh-TW.md），以及 README 的截圖
  guide/               「運作說明」，放上 GitHub Pages 的靜態頁
    guide.py           中英文內容、行號查詢，以及產生靜態 HTML；python -m docs.guide 產生它
    guide.css          它的樣式，和 app 的配色一起內嵌在頁面裡
    guide.js           它唯一的 script，也內嵌在頁面裡
tests/                 pytest 測試，見「測試」
models/                下載的模型（git 會忽略它；AGENT_LOOP_MODELS 可以換位置）
```

agent 在背景 thread 執行，每走到一個階段就 append 一個事件；UI 只負責把事件列表畫出來。所以按「停止」或「允許」時 Streamlit 重跑 script，背景的迴圈不會被打斷。網頁只透過 `Harness`（`harnesses/harness.py`）跑迴圈：`run()`、`stop()`、`decide()`，以及它送出的事件。`SimpleHarness` 是這個專案自己的，`PiHarness` 則把迴圈交給 pi（「[pi 當 harness](pi.zh-TW.md)」）。

「運作說明」是一個靜態頁：`just guide`（`uv run python -m docs.guide _site`）會寫出 `_site/zh/index.html` 和 `_site/en/index.html`（樣式和一小段 script 都內嵌在裡面，可以直接用瀏覽器打開），以及 `_site/index.html`：它把讀者送到上次在頁面右上角選過的語言，沒選過就照瀏覽器的語言。推上 main 時，`.github/workflows/pages.yml` 先跑 `tests/test_guide.py`，再做同一件事並發佈到 GitHub Pages；測試沒過的話，網站上維持原來那一版。

## 一輪的事件

一次執行的事件依序是：

```
run_start
  step_start → context → prefill → token ×N → model_end → parsed                 每一步
    tool_call →（approval_request → approval）→（tool_start）→ tool_result       有工具呼叫的那一步
（error）
run_end
```

- `run_start` 說這一輪是哪個 harness 跑的（`harness`：`simple` 或 `pi`）。
- `context` 帶的是模型實際讀到的 prompt（每個附件都展開成它的 token），以及每種媒體佔了幾個 token（`media_tokens`）。
- `token` 帶著這個 token，以及 backend 知道的話，它的機率、排名、前 5 名候選和 MTP 草稿模型猜了什麼（`backend.TOKEN_DETAILS`）：`simple_backend.py` 全都知道；backend 沒有回報的，畫面就不畫，不會拿沒量過的數字來填。
- `model_end`：等這一步結束才知道哪些 token 是 MTP 猜中的 backend（vLLM 伺服器），把它們放在 MTP 統計裡（`kept_at`、`turned_down_at`），畫面到那時才標出來。
- `approval_request` 和 `approval` 只在打開「執行工具前先問我」時才有，`tool_start` 只在真的執行工具時才有。
- `tool_result` 帶著模型讀的觀察，另外還有工具做給你看的圖（`images`：`run_python` 畫的圖的路徑），模型讀不到。
- 出錯時 `run_end` 前面還有一個 `error`：`message` 是例外的訊息，backend 的錯誤（例如 vLLM 伺服器的）另外帶著兩種語言的版本（`text`），畫面顯示目前語言的那一個。
- pi 跑的 step 先有 `request`，也就是 pi 送給模型的請求，寫成 JSON。pi 問這個網頁的模型時，那一步的 `context`、`prefill`、`token` 和 `model_end` 由模型端點送出，和內建 harness 一樣；pi 問 provider 的模型時，沒有 family，也沒有這四個，改送 `delta`，模型邊寫邊傳回來的一段輸出和它的 channel（思考、回覆、工具呼叫），`model_end` 帶的則是 provider 報的 token 數（`usage`）。

## 兩種語言

畫面上的每一段文字都中英文並排寫在程式裡：程式碼裡是 `pick(lang, "中文", "English")`，資料（特殊 token 的說明、停止原因、運作說明的段落）是 `{"zh": …, "en": …}`。`render.py` 裡每個寫出文字的函式都多一個 `lang` 參數，事件本身不分語言，所以切換語言就是用另一種語言重畫同一份事件，跑完的對話也會跟著換。網頁先看 cookie 裡上次選的語言，沒有就看瀏覽器的 `navigator.language`（`zh` 開頭是中文，其他是英文）；切換時頁面用一小段 script 寫入 cookie，因為 Streamlit 只讀得到 cookie、寫不了。

模型讀到的錯誤（參數不對、工具失敗、你拒絕了）也用這一輪開始時網頁的語言寫，因為它們會原封不動變成觀察；system prompt 兩種語言都一樣，所以模型的行為不跟著網頁語言變。

## 支援更多模型

harness（`harnesses/simple_harness.py`）、解碼迴圈（`simple_backend.py`）和畫面（`render.py`）都只寫一次，裡面沒有任何「如果是 Gemma」的分支。每個模型不一樣的地方集中在 `model_families/` 的一個 `Family` 物件裡：

- 讀輸出：`parse`（把輸出切成思考、工具呼叫、回覆）、`thought_prefix`、`channel_switch`（哪些 token 切到思考、工具呼叫、回覆）、`stop_tokens`
- 寫回對話：`reasoning_key`（思考存在哪個欄位，chat template 才讀得到）、`text_with_calls`（工具呼叫前的文字留不留）
- 畫面：`user_turn`、`byte_level`（詞表是不是把 byte 寫成字元，Qwen 就是，所以 token 浮窗要顯示「如果」而不是 `å¦Ĥæŀľ`）、每個特殊 token 的說明、`file_notes` 和 `drafter_file_notes`（checkpoint 資料夾裡每個檔案裝了什麼，以及模型分頁要顯示哪些欄位的值）、側欄與模型分頁的說明文字、沒有 generation_config.json 時的建議解碼設定；中英文各一份
- 媒體：`processor_kwargs`，給 processor 的設定（Qwen 限制每張影片畫格的像素）；模型讀得懂哪幾種媒體由 checkpoint 決定，不是由家族決定

要加模型：

1. 同一個家族的另一個 checkpoint（例如更大的 Gemma 4 或 Qwen3.5）：在 `agent/model_families/__init__.py` 的 `MODELS` 加一行，`REVISIONS` 也加一行，寫上要下載的 commit。Gemma 4 的其他 checkpoint 也有對應的 MTP 草稿模型（`google/gemma-4-*-it-assistant`），在 `DRAFTERS` 加一行（草稿模型的 commit 也加進 `REVISIONS`），側欄的 MTP 開關就能用。
2. 新的家族：照 `agent/model_families/qwen3_5.py` 寫一個模組（輸出的 parser 加上特殊 token 的說明，中英文都要），把它的 `Family` 加進 `FAMILIES`。載入模型時會用 checkpoint `config.json` 裡的 `model_type` 自動找到它。`tests/test_chat_template.py` 會拿真的 tokenizer 和 chat template 檢查新家族：每個特殊 token 都有說明、模板寫進歷史的工具呼叫讀得回來、step 卡片標成「新加入」的剛好是工具結果。

也可以提出需求：在 vLLM 伺服器上選了網頁不認得的家族的模型，網頁會附上一個已經填好的 GitHub issue；其他想看看的模型，也歡迎到 https://github.com/Agentic-System-Lab/agent-loop-visualizer/issues 提。

## 兩個模型的格式

Gemma 4 的字串用 `<|"|>` 這個特殊 token 包起來，key 也不加引號，所以不是 JSON，`agent/model_families/gemma4.py` 有自己的小 parser：

```
<|tool_call>call:get_current_time{timezone:<|"|>Asia/Taipei<|"|>}<tool_call|><|tool_response>
```

Gemma 寫完工具呼叫會停在 `<|tool_response>`，等 harness 接上結果；回答完則停在 `<turn|>`。這兩個停止 token 正好對應到 Anthropic Messages API 的 `stop_reason: tool_use` 和 `end_turn`。

Qwen3.5 用 XML，每個值都是純文字，型別要照工具的 schema 轉（和 vLLM 的 `qwen3_coder` parser 一樣）：

```
<tool_call>
<function=get_current_time>
<parameter=timezone>
Asia/Taipei
</parameter>
</function>
</tool_call><|im_end|>
```

Qwen 不管回答完或要用工具都停在 `<|im_end|>`，所以 harness 是看「解析出來有沒有工具呼叫」決定要不要結束，而不是看停止 token。工具結果會放進一則新的 `user` 訊息（`<tool_response>…</tool_response>`），而不是像 Gemma 接在同一個 model turn 裡。
