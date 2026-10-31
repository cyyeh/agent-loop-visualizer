# 解碼迴圈與 MTP

[English](decoding.md) | 繁體中文 · [回到 README](../README.zh-TW.md)

## 為什麼自己寫解碼迴圈

`model.generate()` 不會在每一步把機率分布交出來，所以 `simple_backend.py` 自己跑迴圈：每個 token 做一次 forward pass（帶 KV cache），依序套用 temperature、top-k、top-p，再抽樣。每個 token 因此都能回報：在模型原始分布裡的機率和排名、取樣時的機率、top-k / top-p 之後剩幾個候選，以及前 5 名候選。Greedy 模式下的輸出和 `generate()` 實測一致；兩個 token 機率一樣時（bfloat16 的 logits 打平比想像中常見）拿 id 小的，和 `generate()` 的 argmax 一樣。

## MTP 推測解碼

解碼時每個 token 都要跑一次完整的 forward，時間主要花在把權重從記憶體讀出來；同一次 forward 多算幾個位置幾乎不會更慢（Gemma 4 E2B 在 Apple M5 上，1 個位置約 56 ms，7 個位置約 70 ms）。所以只要先便宜地猜好接下來幾個 token，主模型就能一次 forward 全部驗證。Google 為 Gemma 4 訓練了這樣的草稿模型（MTP，multi-token prediction），`transformers` 的 `generate(assistant_model=…)` 會用它，但同樣看不到每一步的分布，所以 `simple_backend.py` 把它接進自己的解碼迴圈：

1. **猜**（`_draft`）：草稿模型 `gemma-4-E2B-it-assistant` 約 78M 參數、4 層。它沒有自己的 KV cache，直接讀主模型的 key / value（Gemma 4 E2B 後 20 層本來就共用前面兩層算好的那份），輸入是上一個 token 的 embedding 接上主模型最後一層的 hidden state。一次 greedy 猜 6 個 token（checkpoint 的 `num_assistant_tokens`）。
2. **驗證**（`_drafted`）：主模型對「剛確定的 token + 6 個猜測」做一次 forward，拿回 7 個位置的分布，依序交給 `_sample()` 檢查。收下的猜測不用另外 forward；第一個被退回的猜測，由主模型自己在那個位置選的 token 取代，後面全部作廢，KV cache 用 `crop()` 退回去；6 個都收下時，最後一個位置還能多給一個 token。
3. **輸出不變**：greedy 時，猜測剛好是第 1 名才收下，所以輸出和不開 MTP 一樣（`tests/test_real_model.py` 用真的模型比對）。抽樣時，猜測以「temperature、top-k、top-p 處理後它的機率」被收下，沒收下就從其他候選裡抽，每個 token 最後出現的機率完全不變（speculative sampling，`tests/test_simple_backend.py` 用兩萬次抽樣檢查）。

收下的比例很看內容。在網頁裡用 Gemma 的預設解碼設定實測（Apple M5）：

| 這一步在寫什麼 | 不開 MTP | 開 MTP | 草稿收下 |
|---|---|---|---|
| 工具呼叫（「台北現在幾點？紐約呢？」第 1 步） | 12.6 tok/s | 40.9 tok/s | 34 / 35 |
| 根據工具結果回答（同一題第 2 步） | 13.0 tok/s | 22.6 tok/s | 42 / 106 |
| 英文程式碼，約 750 tokens | 8.8 tok/s | 11.6 tok/s（單獨跑 `simple_backend.py`：8.1 → 29.0） | 51% |
| 中文長文（「用三段話介紹台北。」） | 10.3 tok/s | 10.3 tok/s | 7% |

用 transformers 時只有 Gemma 4 E2B 有草稿模型。在有 GPU 的 vLLM 伺服器上兩個模型都可以推測解碼，Gemma 4 E2B 用同一個草稿模型，Qwen3.5 用它自己 checkpoint 裡的 MTP 層：Docker 裡的 vLLM 在 GPU 上預設就會，自己的伺服器要加上 `--speculative-config`（見「[在 vLLM 上跑模型](vllm.zh-TW.md)」）。
