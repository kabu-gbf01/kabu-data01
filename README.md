# tse_prime_tool

東証（プライム/スタンダード/グロース）日次株価スクリーナー

## 構成

```
tse_prime_tool/
├── .github/
│   └── workflows/
│       └── fetch_daily.yml   # GitHub Actions cron（平日 15:35 JST）
├── .streamlit/
│   └── config.toml           # テーマ設定
├── core/
│   ├── fetcher.py            # データ取得・指標計算
│   └── fetch_and_commit.py   # Actions から呼ぶ単体スクリプト
├── ui/
│   └── app.py                # Streamlit 公開用アプリ（表示専用）
├── output/                   # CSV 出力先（Actions が push）
├── config.py                 # 定数・ソートプリセット定義
├── requirements.txt
└── README.md
```

## 公開までの手順

### 1. GitHub リポジトリ作成
1. https://github.com/new でリポジトリ作成（Public or Private どちらでも可）
2. ローカルで初期化して push

```bash
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/<ユーザー名>/<リポジトリ名>.git
git push -u origin main
```

### 2. output/ ディレクトリを Git 管理対象にする
output/ は .gitignore に入れず、.gitkeep を置いて空ディレクトリを管理する。
Actions が CSV を push できるようにするため。

```bash
touch output/.gitkeep
git add output/.gitkeep
git commit -m "chore: add output gitkeep"
git push
```

### 3. GitHub Actions の権限設定
1. リポジトリ → Settings → Actions → General
2. **Workflow permissions** を "Read and write permissions" に変更して Save

### 4. Streamlit Community Cloud にデプロイ
1. https://share.streamlit.io にアクセス（GitHub アカウントでログイン）
2. "New app" → リポジトリ選択
3. **Main file path: `ui/app.py`** を指定
4. Deploy

### 5. 動作確認
- Actions タブ → "Daily Stock Fetch" → "Run workflow" で手動実行
- output/ に CSV が push されたことを確認
- Streamlit アプリに CSV が表示されることを確認

## 指標一覧

| 列名 | 説明 |
|------|------|
| 変動率(%) | (終値-始値)/始値 × 100 |
| 前日比(%) | (終値-前日終値)/前日終値 × 100 |
| 振れ幅(%) | (高値-安値)/始値 × 100 |
| レンジ位置 | (終値-安値)/(高値-安値)　0=安値圏  1=高値圏 |
| 上ヒゲ比 | (高値-終値)/(高値-安値) |
| VWAP | (高値+安値+終値)/3 |
| 終値/VWAP | 1以上=VWAP上抜け(強い引け) |
| 売買代金(百万円) | VWAP × 出来高 / 1,000,000 |
| 全体順位 | 変動率の全銘柄内順位 |
| セクター内順位 | 変動率のセクター内順位 |
| セクター内% | セクター内順位/セクター銘柄数 |
| vsセクター | 自分の変動率-セクター平均 |

## ソートプリセット

| プリセット | ソート列 | 意図 |
|---|---|---|
| 🔺 上昇率ランキング | 変動率(%) 降順 | 当日強い銘柄 |
| 🔻 下落率ランキング | 変動率(%) 昇順 | 当日弱い銘柄 |
| ⚡ セクター内で突出して強い | vsセクター 降順 | セクター内アウトパフォーマー |
| 🎯 高値圏で引けた銘柄 | レンジ位置 降順 | 続伸候補 |
| 📉 安値圏で引けた銘柄 | レンジ位置 昇順 | 売り継続候補 |
| 🕯️ 上ヒゲが長い銘柄 | 上ヒゲ比 降順 | 売り圧力あり |
| 🌊 値動きが大きかった銘柄 | 振れ幅(%) 降順 | 高ボラティリティ |
| 💰 売買代金ランキング | 売買代金 降順 | 商いが集まった銘柄 |
| 📊 VWAP上抜けで引けた銘柄 | 終値/VWAP 降順 | 強い引け |
| 📊 VWAP割れで引けた銘柄 | 終値/VWAP 昇順 | 弱い引け |
| 💹 出来高が多い銘柄 | Volume 降順 | 出来高上位 |
