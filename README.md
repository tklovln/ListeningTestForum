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

```bash
cd subjective-forum
bash run.sh
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.
