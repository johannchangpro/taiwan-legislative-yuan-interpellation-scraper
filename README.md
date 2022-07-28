# 中華民國立法院質詢系統檢索結果截取器

截取[中華民國立法院質詢系統](http://lis.ly.gov.tw/qrkmc/qrkmout)檢索結果的[後設資料](https://zh.wikipedia.org/zh-tw/%E5%85%83%E6%95%B0%E6%8D%AE)並輸出到 `<關鍵字>.csv` 檔案。

## 下載

\>\> [Releases](https://github.com/changyuheng/taiwan-legislative-yuan-interpellation-scraper/releases) <<

## 設定

1. \[選擇性] 設定瀏覽器。支援 `Edge` 與 `Firefox`，預設為 `Edge`。

範例：設定瀏覽器為 Firefox

```
lyjournal-scraper config browser "firefox"
```

## 使用

```
lyjournal-scraper scrape "<關鍵字>"
```
