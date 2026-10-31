# 畫面上看得到什麼

[English](page.md) | 繁體中文 · [回到 README](../README.zh-TW.md)

畫面上的每個部分、看得到什麼，以及對應 [Agent Atlas 技術與實戰交流](https://agentic-system-lab.github.io/agent-atlas-learning/) unit 01 導讀的哪一節。

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
