# pi 當 harness

[English](pi.md) | 繁體中文 · [回到 README](../README.zh-TW.md)

網頁也可以把迴圈交給 [pi](https://pi.dev)，一個有自己的迴圈、system prompt 和工具（read、bash、edit、write、grep、find、ls）的 coding agent。在側欄最上面的「用什麼跑迴圈」選 pi，再在「pi 問的模型」選它問哪個模型，網頁就用同一張迴圈圖、同樣的 step 卡片和事件列表，畫出 pi 做了什麼。每一步的脈絡段顯示 pi 送給模型的請求（它的 system prompt、工具和對話，寫成 JSON），這一步新加的部分另外標出來。

- **這個網頁的模型**（預設）：Gemma 4 E2B 或 Qwen3.5 0.8B，跑在 transformers 或 vLLM 上，用和內建 harness 一樣的模型選單和「用什麼跑模型」來選。pi 只會用 HTTP 問模型，所以 `agent/harnesses/model_endpoint.py` 把記憶體裡的模型當成 127.0.0.1 上一個相容 OpenAI 的 chat completions 端點，用一個 token 擋住別的程式，pi 的 extension 再把它註冊成 provider `agent-loop`。每個請求都用模型的 chat template render、encode、生成，和內建 harness 的一步一樣，事件進到 pi 的那一步：「脈絡」分頁顯示模型讀到的字串（下面收著 pi 送出的請求），每個 token 的機率和候選也都看得到。回覆一邊生成一邊傳回 pi：思考是 `reasoning_content`，回覆是 `content`，最後是 family 從模型自己的格式解析出來的工具呼叫（`tool_calls`）。解碼設定是側欄的；「思考模式」變成 pi 的思考等級送出，端點再換成 chat template 的思考開關。
- **pi 自己的模型**：pi 登入過的模型（Claude、GPT、Gemini，或它 `models.json` 裡任何相容的端點），這台電腦不載入模型。API 傳回來的是文字，不是 token，所以沒有 token 的機率、候選和特殊 token，API 那邊怎麼把請求寫成模型讀的字串也沒有人說：一個 step 顯示 pi 的請求、一段段傳回來的文字、provider 報的 token 數（以及其中多少來自 cache），和照 pi 的價目估的費用。

## 安裝 pi

```bash
nvm install                                      # 用 nvm 的話：照 .nvmrc 裝好最新的 Node 22 再換過去；nvm use 可能挑到已經裝好、但對 pi 來說太舊的 22。pi 也要裝在它底下，因為 nvm 的全域套件是每個版本各裝各的
npm install -g @earendil-works/pi-coding-agent   # pi 1.4 需要 Node.js 22.19 以上
pi                                               # 再輸入 /login 登入一次；或在啟動 app 之前設好 API key，例如 ANTHROPIC_API_KEY
PI_COMMAND=/path/to/pi just run                  # pi 不在 PATH 上的話（任何指令都行，npx 也可以）
```

## 細節

- **網頁怎麼跑它。** `agent/harnesses/pi_harness.py` 每個問題都用 RPC 模式啟動 pi（`pi --mode rpc`）：指令寫進它的 stdin，紀錄從它的 stdout 讀出來，一行一個 JSON。它先選好模型和思考等級、關掉 pi 自己的重試（重試會變成另一個 step，所以請求失敗就當成錯誤顯示），再送出問題，每個指令都等 pi 回應了才送下一個；pi 的一個 turn（向模型送一次請求，加上回覆裡要執行的工具）就是一個 step。pi 把對話存在這段對話資料夾裡的 session 檔，下一個問題就接著它；按「新對話」會刪掉。
- **啟動 pi 時不帶的東西。** 你自己的 extension、skill、prompt 範本和 context 檔（AGENTS.md、CLAUDE.md）都不載入（`--no-extensions` 之類），所以網頁畫的是 pi 本身的迴圈，每台電腦上都一樣；模型和登入資訊還是你的，在 `~/.pi/agent`。
- **工具。** 側欄選模型看得到 pi 的哪些工具（預設是 read、bash、edit、write，和 pi 一樣）。它們在這台電腦上、這段對話的資料夾裡執行，沒有沙箱：不像 `run_python`，bash 碰得到你碰得到的一切。附上的檔案存在那個資料夾裡，問題裡會寫出檔名；讀得懂圖片的模型，圖片也會跟著問題一起送過去。
- **Extension。** 網頁啟動的每個 pi 都載入 `agent/harnesses/pi_extension.ts`。每次向模型送出請求前，它把請求當成一則通知送出，在 RPC 模式下就是 stdout 上的一筆 `extension_ui_request`，變成那一步的 `request`；pi 問這個網頁的模型時，它註冊那個模型；執行工具前先問你的也是它（見下）。
- **執行工具前先問我。** pi 自己不會問；打開時，extension 在每次執行工具前開一個確認對話框。在 RPC 模式下，對話框出現在 stdout，網頁把它顯示成「允許」和「拒絕」，你的回答再從 stdin 送回去；被拒絕的呼叫不會執行，模型讀到的是用這一輪語言寫的拒絕原因。
- **停止。** 按停止會送給 pi `abort`。pi 自己沒有步數上限，所以「步數上限」由網頁來守：pi 開始超過上限的那個 turn 時，網頁就請它中止。確認一直沒人回答的話，5 分鐘後停掉 pi，和內建 harness 一樣。
- **測試**用的是 pi 1.4.0：透過照劇本說它的協定的替身（`tests/fake_pi.py`，它也會像 pi 一樣用 HTTP 問模型端點），以及 `RUN_PI_TESTS=1` 時的真 pi，分別指向 127.0.0.1 上一個照劇本回答的模型，和後面接著假模型的模型端點。
