"""
GitHub Actions から呼ばれる定期取得スクリプト。
全市場（プライム・スタンダード・グロース）を取得して
output/tse_daily_YYYY-MM-DD.csv に保存する。
"""
import os
import sys
from datetime import datetime
import pytz

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import OUTPUT_DIR, MARKET_MAP
from core.fetcher import load_stock_list, fetch_quotes, build_result_df

JST = pytz.timezone("Asia/Tokyo")
now = datetime.now(JST)

# 土日スキップ（SKIP_WEEKEND=false で無効化可能）
skip_weekend = os.environ.get("SKIP_WEEKEND", "true").lower() == "true"
if skip_weekend and now.weekday() >= 5:
    print(f"本日（{now.strftime('%Y-%m-%d %a')}）は土日のためスキップします")
    print("土日も実行したい場合は workflow の SKIP_WEEKEND を false に設定してください")
    sys.exit(0)

os.makedirs(OUTPUT_DIR, exist_ok=True)
today   = now.strftime("%Y-%m-%d")
outfile = os.path.join(OUTPUT_DIR, f"tse_daily_{today}.csv")

markets = list(MARKET_MAP.keys())
print(f"[{now.strftime('%H:%M JST')}] 取得開始: {markets}")

stock_df  = load_stock_list(markets)
print(f"対象銘柄数: {len(stock_df)}")

quotes_df = fetch_quotes(stock_df)
result_df = build_result_df(stock_df, quotes_df)

result_df.to_csv(outfile, index=False, encoding="utf-8-sig")
print(f"保存完了: {outfile}  ({len(result_df)} 銘柄)")
