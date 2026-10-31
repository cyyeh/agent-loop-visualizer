# 附件與程式沙箱

[English](files.md) | 繁體中文 · [回到 README](../README.zh-TW.md)

## 圖片、聲音和影片

模型讀得懂哪些東西，是載入時從 checkpoint 看出來的：config 裡要有那種編碼器，processor 也要有對應的部分。Gemma 4 E2B 讀得懂圖片、聲音和影片；Qwen3.5 0.8B 讀得懂圖片和影片。輸入框只收模型讀得懂的檔案：

| 種類 | 格式 | Gemma 4 E2B | Qwen3.5 0.8B |
|---|---|---|---|
| 圖片 | png、jpg、jpeg、webp、gif、bmp | 最多 280 個 token | 看圖片大小（640×480 約 300 個） |
| 聲音 | wav、mp3、m4a、flac、ogg | 每 40 ms 一個 token，只聽前 30 秒 | —（打開「讓模型寫程式」時當成給 `run_python` 的檔案） |
| 影片 | mp4、mov、webm、mkv | 32 張畫格（比這短的影片全部都用），每張前面寫上時間 `mm:ss`，每張最多 70 個 token | 每秒 2 張畫格，每 2 張一組，前面寫上時間 |
| 資料 | csv、tsv、json、txt、md、xlsx | 打開「讓模型寫程式」時給 `run_python` 讀 | 同左 |

chat template 在每個檔案的位置寫一個佔位 token（Gemma 是 `<|image|>`，Qwen 是 `<|vision_start|><|image_pad|><|vision_end|>`），`SimpleBackend.encode()` 把對話裡所有檔案交給 processor，processor 把每個佔位 token 展開成那個檔案的 token；脈絡分頁顯示的就是展開後的字串，因為那才是模型讀到的。檔案先由 `media.py` 解碼：圖片轉成 RGB、照 EXIF 轉正；聲音用 PyAV 解碼成單聲道、改成 feature extractor 要的 16 kHz；影片平均取最多 64 張畫格、縮到長邊 768 像素（transformers 自己讀影片要裝 torchcodec）。每個檔案只解碼一次。prefill 時，圖片和影片先跑一次視覺編碼器再交給 prefill，和 `generate()` 的做法一樣（直接交給 forward 的話，transformers 5.20 的 Gemma 4 會漏掉影片的畫格數）；Qwen3.5 記在模型上的圖片位置偏移，每次 prefill 前清掉。prefill 之後的解碼和純文字一樣；`tests/test_real_model.py` 確認附上圖片、影片和錄音時，greedy 的輸出也和 `generate()` 一致。

## 在 Docker 沙箱裡寫程式

打開「讓模型寫程式」而且 Docker 準備好時（見[安裝與設定](setup.zh-TW.md#讓模型寫程式)），模型多一個工具 `run_python`。每次呼叫都從 `agent/sandbox/Dockerfile` 建的 image 開一個新容器：沒有網路，檔案系統唯讀、只有一小塊 `/tmp` 能寫，記憶體 512 MB、一顆 CPU、最多 64 個 process，拿掉所有 Linux capability，用你自己的使用者執行、絕不用 root（在 Linux 上，掛進去的資料夾保留原本的權限，換成別的使用者可能進不去），這段對話的資料夾唯讀掛在 `/data`；程式從 stdin 送進去，跑完容器就刪掉。超過 30 秒就停掉；結束代碼不是 0、記憶體用太多或什麼都沒印（也沒畫圖），都用這一輪的語言當成錯誤回給模型，附上 traceback，模型下一步可以改。

容器寫不進任何頁面讀得到的地方，matplotlib 畫的圖還是回得來：image 把 matplotlib 的 backend 設成 `agent/sandbox/agent_loop_figures.py`，它在 `plt.show()` 或程式結束時把每張圖轉成 PNG，程式結束前接在印出來的東西後面，前面加一行 `run_python` 傳進去的記號。`run_python` 把它們從模型要讀的輸出切掉（最多四張），存進這段對話的資料夾，叫 `figure-1.png`、`figure-2.png`…，和觀察分開回傳：模型只讀到 `{"stdout": …, "figures": ["/data/figure-1.png"]}`，頁面把圖畫在聊天區和那一步底下。中文的標籤用 image 為此裝的文泉驛微米黑畫。載入 matplotlib 讓一次呼叫慢了約半秒（0.8 秒，純 Python 是 0.2 秒）。

image 先用 wheel 加 hash 裝好 pip 26.2.2，再用它裝其他套件：更舊的 pip 也信任它自己帶的那份 certifi，裡面還有外洩的 emSign 憑證。頁面會讀 image 的 `agent-loop-sandbox.version` label，比 `agent/sandbox/Dockerfile` 舊就在側欄請你重建，不提供 `run_python`。

模型看不到資料檔的內容，所以 harness 在使用者訊息後面加一段說明：`run_python` 在哪裡找得到每個檔案，以及文字檔的第一行（CSV 就是欄位名稱）。少了這一行，小模型寫程式時會亂猜欄位，例如不存在的 `Date`，然後出錯；多給幾列資料也不行，Gemma 會把那幾列抄進程式，只用它們算答案。image 裡有 `tabulate`，因為小模型很愛用的 `DataFrame.to_markdown()` 需要它。
