# Music Generation Listening Test

## Introduction

這個 repository 是為了舉辦音樂生成聆聽測試而建立的。測試的方式是一個 reference audio 以及數個參考 reference 生成的音檔的比較, 詳細的使用方式可以見 subjective-forum 這個資料夾內部的 README.md。


## Main Features

* 高度客製化表單中的問題 （見 config/forum.json）
* 可以建立 question template, 自己設定受測者需選填的 metrics, questioin title, random generate samples 的數量等等
* 在規則頁的部分整合了 markdown 格式, 方便你一直修改聽測的規則以及注意事項 （詳見 config/rules.md）
* 優化了跨裝置的 UX, 可以在電腦以及手機上執行聽測, 超級方便
* 流暢的聽測體驗（比起 google form 好太多了）
* 可以自動 randomize 選擇 sample pools 中 (reference audio, 生成音檔的) testing pair, 讓所有受測者可以聽到不同的 sample pair
* 可以自動幫你 randomize 盲測模型的聽測順序, 不用再多耗心力紀錄跟整理忙測的結果

## Usage

### Setting
#### 更改 `config/forum.json`
1. 基本設定
    - `debug`: debug 模式開啟的話會把所有盲測的音檔資訊（例如選用了哪些 sample_id, model 直接秀在 UI, 預設是關閉
    - `branding`: 可以改個 Title
    - `participantFields`: 使用者的基本資料填答, 可以改裡面的文字敘述, 也可以照要求刪掉某個行, 就不會顯示
    - `rulesMarkdown`: 規則頁的 markdown 檔路徑, 這個 markdown 可以完全的自由改動, 會出現在使用者填完基本資料後
    - `audioRoot`: 聽測音檔的 Root Folder, 很重要
2. 設定 Question Template
    - `questions`: *包含了一個 List, 其中有多個 Question Template*, 裡面每個東西都要設定
    - `audioSubfolder`： 每種 Question templatel 中如果測試的是不同的 task, 例如 continuation, unconditional, inpainring, 就要放在不同的 subfolder, eg. `audioRoot/continuation`, `audioRoot/continuation`
    - `n_to_present`: 每個 question template 要 sample 幾組聽測
    - `title`: 問題設計
    - `metrics`: 填答選項跟敘述, 只有 name 會在 ui 上, description 會自動放到規則頁顯示
    - `models`: **要 compare 的 model 種類, 必須符合聽測音檔的路徑名, 系統會透過這個
     list 抓取 `audioSubfolder` 下的音檔路徑. 系統會比對這個 list 中所有的 model 的音檔路徑都存在, 才會加進 sampling pool!!**
    -  聽測表單會根據 Question template 中的 `n_to_present`, 預先從 audioSubFolder 中隨機抽樣, 然後隨機的播放, 需要注意的是如果有多個 Question template, 題目的出現的順序也都是隨機的, 所以必須好好的設計 `title` 的寫法


#### 聽測音檔的 Folder Structure

- **音檔要用 {sample_id}_{model_id}.mp3 來命名**
- **目前的架構一定要有 prompt audio, 系統會先顯示 prompt 的頁面才會進如填答**
```
audioRoot/
├── audioSubfolder01/                        # 就是 forum.json 中指定的 audioSubfolder
├── audioSubfolder02/               
│   ├── {sample_id}_prompt.mp3         
│   ├── {sample_id}_{model_id}.mp3        
│   ├── {sample_id}_{model_id}.mp3         
│   ├── {sample_id}_prompt.mp3        
│   ├── {sample_id}_{model_id}.mp3         
│   └── {sample_id}_{model_id}.mp3         
├── audioSubfolder02/
```

For example:
```
mnt/home/PicoGen9/
├── continuation/                        # 就是 forum.json 中指定的 audioSubfolder
├── unconditional/               
│   ├── unconditional-001_prompt.mp3         
│   ├── unconditional-001_baseline-1.mp3        
│   ├── unconditional-001_our.mp3         
│   ├── unconditional-002_prompt.mp3        
│   ├── unconditional-002_baseline-1.mp3         
│   └── unconditional-002_our.mp3         
├── conditional/
```
## 表單流程

主頁 -> 使用者資料頁 -> 規則頁 -> 問題頁 （先播放 prmpt, 跳轉到填答, 一直循環）-> 結束頁

### Run Forum
```bash
cd subjective-forum
bash run.sh
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.
