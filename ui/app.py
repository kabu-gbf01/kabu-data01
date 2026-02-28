import os
import sys
import glob

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import streamlit as st

from config import OUTPUT_DIR, CHG_COL, SORT_PRESETS

st.set_page_config(page_title="TSE Daily Screener", layout="wide")
st.title("\U0001f4c8 東証 日次株価スクリーナー")

# ════════════════════════════════════════════════════════════
# CSV 読み込み
# ════════════════════════════════════════════════════════════
csv_files = sorted(
    glob.glob(os.path.join(OUTPUT_DIR, "tse_daily_*.csv")), reverse=True
)

if not csv_files:
    st.error("データがありません。output/ に CSV を配置してください。")
    st.stop()

file_labels = [
    os.path.basename(f).replace("tse_daily_", "").replace(".csv", "")
    for f in csv_files
]

# サイドバー：日付選択 & ソート設定のみ
st.sidebar.header("\u2699\ufe0f 設定")
selected_label = st.sidebar.selectbox("\U0001f4c5 表示日付", options=file_labels, index=0)
selected_file  = csv_files[file_labels.index(selected_label)]

@st.cache_data(show_spinner="データ読み込み中...")
def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"Code": str})

df = load_csv(selected_file)
st.sidebar.caption(f"総銘柄数: {len(df):,} 件")

st.sidebar.divider()
st.sidebar.markdown("**\U0001f4ca ソートプリセット**")

preset_labels = [p[0] for p in SORT_PRESETS]
preset_idx = st.sidebar.selectbox(
    "プリセット",
    options=range(len(preset_labels)),
    format_func=lambda i: preset_labels[i],
    index=0,
)
_, _sort_col, _sort_asc, _preset_desc = SORT_PRESETS[preset_idx]
st.sidebar.caption(f"\U0001f4cc {_preset_desc}")
st.sidebar.caption(f"ソート: `{_sort_col}` / {'昇順 \u2191' if _sort_asc else '降順 \u2193'}")

top_n = st.sidebar.slider("表示件数 N", min_value=10, max_value=200, value=30, step=10)


# ════════════════════════════════════════════════════════════
# 銘柄詳細ダイアログ
# ════════════════════════════════════════════════════════════
@st.dialog("\U0001f4ca 銘柄詳細", width="large")
def show_detail(row: pd.Series):
    code = row.get("Code", "")
    name = row.get("CompanyName", "")
    st.subheader(f"{code}\u3000{name}")
    st.caption(f"{row.get('Market', '')} ／ {row.get('Sector17', '')}")
    st.divider()

    st.markdown("#### \U0001f4b4 価格")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("始値", f"{row.get('Open',  0):,.0f}")
    c2.metric("高値", f"{row.get('High',  0):,.0f}")
    c3.metric("安値", f"{row.get('Low',   0):,.0f}")
    c4.metric("終値", f"{row.get('Close', 0):,.0f}", delta=f"{row.get(CHG_COL, 0):+.2f}%")
    if pd.notna(row.get("PrevClose")):
        st.caption(f"前日終値: {row.get('PrevClose', 0):,.0f}　前日比: {row.get('前日比(%)', 0):+.2f}%")
    st.divider()

    st.markdown("#### \U0001f4b9 VWAP・売買代金")
    v1, v2, v3 = st.columns(3)
    v1.metric("VWAP", f"{row.get('VWAP', 0):,.0f}", help="(高値+安値+終値)/3")
    v2.metric("終値/VWAP", f"{row.get('終値/VWAP', 0):.3f}",
              delta="VWAP上" if row.get("終値/VWAP", 1) >= 1 else "VWAP割れ",
              delta_color="normal" if row.get("終値/VWAP", 1) >= 1 else "inverse")
    v3.metric("売買代金(百万円)", f"{row.get('売買代金(百万円)', 0):,.1f}")
    st.divider()

    st.markdown("#### \U0001f4d0 変動指標")
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("変動率(%)",  f"{row.get(CHG_COL,     0):+.2f}%")
    d2.metric("前日比(%)",  f"{row.get('前日比(%)', 0):+.2f}%")
    d3.metric("振れ幅(%)",  f"{row.get('振れ幅(%)', 0):.2f}%")
    d4.metric("出来高",     f"{int(row.get('Volume', 0)):,}")
    st.divider()

    st.markdown("#### \U0001f56f\ufe0f ローソク足指標")
    e1, e2 = st.columns(2)
    rp = row.get("レンジ位置", 0)
    uh = row.get("上ヒゲ比",   0)
    e1.metric("レンジ位置", f"{rp:.3f}",
              delta="高値圏" if rp >= 0.7 else ("安値圏" if rp <= 0.3 else "中間"),
              delta_color="normal" if rp >= 0.7 else ("inverse" if rp <= 0.3 else "off"))
    e2.metric("上ヒゲ比", f"{uh:.3f}",
              delta="売り圧力あり" if uh >= 0.6 else "通常",
              delta_color="inverse" if uh >= 0.6 else "off")
    st.divider()

    st.markdown("#### \U0001f3ed セクター相対")
    f1, f2, f3, f4 = st.columns(4)
    f1.metric("全体順位",       f"{int(row.get('全体順位',       0)):,}")
    f2.metric("セクター内順位", f"{int(row.get('セクター内順位', 0)):,}／{int(row.get('セクター銘柄数', 0)):,}")
    f3.metric("セクター内%",    f"{row.get('セクター内%',  0):.1%}")
    f4.metric("vsセクター",     f"{row.get('vsセクター',   0):+.2f}%")

    with st.expander("\U0001f50d 全カラムデータ"):
        st.dataframe(
            pd.DataFrame({"項目": row.index, "値": row.values}),
            use_container_width=True, hide_index=True,
        )


# ════════════════════════════════════════════════════════════
# タブ
# ════════════════════════════════════════════════════════════
tab_result, tab_sector = st.tabs(["\U0001f4cb 結果一覧", "\U0001f3ed セクター分析"])


# ────────────────────────────────────────────────────────────
# TAB 1 : 結果一覧
# ────────────────────────────────────────────────────────────
with tab_result:

    # ── タブ内フィルターバー ──────────────────────────────────
    all_markets = sorted(df["Market"].dropna().unique()) if "Market" in df.columns else []
    # 市場ごとのボタン（全市場 + 個別）
    market_options = ["すべて"] + all_markets
    sel_market = st.radio(
        "市場",
        options=market_options,
        index=0,
        horizontal=True,
        key="market_radio",
    )

    # 詳細フィルター（折り畳み）
    with st.expander("\U0001f50d 詳細フィルター"):
        fc1, fc2, fc3 = st.columns(3)

        with fc1:
            all_sectors = sorted(df["Sector17"].dropna().unique()) if "Sector17" in df.columns else []
            sel_sectors = st.multiselect("セクター", options=all_sectors, default=all_sectors, key="sec_filter")

        with fc2:
            min_vol_col = "売買代金(百万円)"
            min_turnover = st.number_input(
                "売買代金 下限（百万円）", min_value=0, value=0, step=100, key="turnover_filter"
            ) if min_vol_col in df.columns else 0

        with fc3:
            if CHG_COL in df.columns:
                chg_min, chg_max = st.slider(
                    "変動率(%) 範囲",
                    min_value=-20.0, max_value=20.0,
                    value=(-20.0, 20.0), step=0.5, key="chg_filter",
                )
            else:
                chg_min, chg_max = -20.0, 20.0

    # ── フィルター適用 ────────────────────────────────────────
    filtered = df.copy()
    if sel_market != "すべて" and "Market" in filtered.columns:
        filtered = filtered[filtered["Market"] == sel_market]
    if sel_sectors and "Sector17" in filtered.columns:
        filtered = filtered[filtered["Sector17"].isin(sel_sectors)]
    if min_turnover > 0 and min_vol_col in filtered.columns:
        filtered = filtered[filtered[min_vol_col] >= min_turnover]
    if CHG_COL in filtered.columns:
        filtered = filtered[filtered[CHG_COL].between(chg_min, chg_max)]

    # ── プリセット説明バナー ──────────────────────────────────
    st.info(
        f"**{preset_labels[preset_idx]}**　　{_preset_desc}　　"
        f"ソート: `{_sort_col}` {'\u2191 昇順' if _sort_asc else '\u2193 降順'}　　"
        f"表示: {min(top_n, len(filtered)):,} ／ {len(filtered):,} 件"
    )
    st.caption("\U0001f4a1 行をクリックすると詳細ダイアログが開きます")

    if filtered.empty:
        st.warning("フィルター条件に一致する銘柄がありません。")
    else:
        _sort_col_safe = _sort_col if _sort_col in filtered.columns else CHG_COL
        ranked = (
            filtered.sort_values(_sort_col_safe, ascending=_sort_asc)
            .head(top_n)
            .reset_index(drop=True)
        )

        _show_candidates = [
            "Code", "CompanyName", "Market", "Sector17",
            "Open", "High", "Low", "Close", "PrevClose", "Volume",
            CHG_COL, "前日比(%)", "振れ幅(%)", "レンジ位置", "上ヒゲ比",
            "VWAP", "終値/VWAP", "売買代金(百万円)",
            "全体順位", "セクター内順位", "vsセクター",
        ]
        show_cols = [c for c in _show_candidates if c in ranked.columns]

        col_config = {}
        for col, cfg in [
            (CHG_COL,            st.column_config.NumberColumn(format="%.2f")),
            ("前日比(%)",        st.column_config.NumberColumn(format="%.2f")),
            ("振れ幅(%)",        st.column_config.NumberColumn(format="%.2f")),
            ("vsセクター",       st.column_config.NumberColumn(format="%.2f")),
            ("終値/VWAP",        st.column_config.NumberColumn(format="%.3f")),
            ("売買代金(百万円)", st.column_config.NumberColumn(format="%.1f")),
            ("レンジ位置",       st.column_config.ProgressColumn(min_value=0, max_value=1)),
            ("上ヒゲ比",         st.column_config.ProgressColumn(min_value=0, max_value=1)),
        ]:
            if col in ranked.columns:
                col_config[col] = cfg

        selection = st.dataframe(
            ranked[show_cols], use_container_width=True,
            column_config=col_config,
            on_select="rerun", selection_mode="single-row",
            key="result_table",
        )
        if selection.selection.get("rows"):
            row_code = ranked.iloc[selection.selection["rows"][0]]["Code"]
            show_detail(df[df["Code"] == row_code].iloc[0])

        # 変動率分布
        if CHG_COL in filtered.columns:
            st.divider()
            st.write(f"##### {CHG_COL} 分布（フィルター後・±10%クリップ）")
            hist = (
                filtered[CHG_COL].dropna().clip(-10, 10)
                .value_counts(bins=40).sort_index()
            )
            hist.index = [f"{iv.left:.1f}~{iv.right:.1f}" for iv in hist.index]
            st.bar_chart(hist)


# ────────────────────────────────────────────────────────────
# TAB 2 : セクター分析
# ────────────────────────────────────────────────────────────
with tab_sector:
    st.subheader("\U0001f3ed セクター分析")

    # タブ内市場フィルター（結果一覧と独立して動作）
    all_markets_s = sorted(df["Market"].dropna().unique()) if "Market" in df.columns else []
    sel_market_s  = st.radio(
        "市場",
        options=["すべて"] + all_markets_s,
        index=0,
        horizontal=True,
        key="market_radio_sector",
    )
    df_sec = df[df["Market"] == sel_market_s] if sel_market_s != "すべて" else df.copy()

    if df_sec.empty or CHG_COL not in df_sec.columns:
        st.warning("データがありません。")
    else:
        agg_dict = {
            "銘柄数":       ("Code",  "count"),
            "上昇数":       (CHG_COL, lambda x: (x > 0).sum()),
            "下落数":       (CHG_COL, lambda x: (x < 0).sum()),
            "勝率":         (CHG_COL, lambda x: round((x > 0).mean() * 100, 1)),
            "平均変動率":   (CHG_COL, lambda x: round(x.mean(), 2)),
            "中央値変動率": (CHG_COL, "median"),
            "最大上昇":     (CHG_COL, "max"),
            "最大下落":     (CHG_COL, "min"),
            "標準偏差":     (CHG_COL, lambda x: round(x.std(), 2)),
        }
        if "売買代金(百万円)" in df_sec.columns:
            agg_dict["合計売買代金(百万円)"] = ("売買代金(百万円)", "sum")

        sec = df_sec.groupby("Sector17").agg(**agg_dict).reset_index()
        sec.insert(0, "順位", sec["平均変動率"].rank(ascending=False).astype(int))
        sec = sec.sort_values("平均変動率", ascending=False).reset_index(drop=True)

        st.write("#### セクター騰落ランキング")
        st.dataframe(
            sec, use_container_width=True,
            column_config={
                "勝率":         st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
                "平均変動率":   st.column_config.NumberColumn(format="%.2f"),
                "中央値変動率": st.column_config.NumberColumn(format="%.2f"),
                "標準偏差":     st.column_config.NumberColumn(format="%.2f"),
            },
        )
        st.bar_chart(sec.set_index("Sector17")["平均変動率"])
        st.divider()

        # セクター内 Top/Bottom
        st.write("#### セクター内銘柄ランキング")
        st.caption("\U0001f4a1 行をクリックすると詳細ダイアログが開きます")
        sectors = sorted(df_sec["Sector17"].dropna().unique())
        sel = st.selectbox("セクターを選択", sectors)

        sec_df = (
            df_sec[df_sec["Sector17"] == sel]
            .sort_values(CHG_COL, ascending=False)
            .reset_index(drop=True)
        )
        if "セクター内順位" not in sec_df.columns:
            sec_df.insert(0, "セクター内順位", range(1, len(sec_df) + 1))

        detail_cols = [c for c in [
            "セクター内順位", "Code", "CompanyName",
            CHG_COL, "前日比(%)", "vsセクター", "全体順位",
            "売買代金(百万円)", "終値/VWAP", "レンジ位置", "上ヒゲ比",
        ] if c in sec_df.columns]

        col1, col2 = st.columns(2)
        with col1:
            st.write("**\U0001f53a 上昇 Top 10**")
            t10 = st.dataframe(
                sec_df.head(10)[detail_cols], use_container_width=True,
                on_select="rerun", selection_mode="single-row", key="top10",
            )
            if t10.selection.get("rows"):
                rc = sec_df.head(10).iloc[t10.selection["rows"][0]]["Code"]
                show_detail(df[df["Code"] == rc].iloc[0])

        with col2:
            st.write("**\U0001f53b 下落 Bottom 10**")
            b10_df = sec_df.tail(10)[detail_cols].iloc[::-1].reset_index(drop=True)
            b10 = st.dataframe(
                b10_df, use_container_width=True,
                on_select="rerun", selection_mode="single-row", key="bot10",
            )
            if b10.selection.get("rows"):
                rc = b10_df.iloc[b10.selection["rows"][0]]["Code"]
                show_detail(df[df["Code"] == rc].iloc[0])

        st.divider()
        if "vsセクター" in sec_df.columns:
            st.write(f"#### {sel} ── vsセクター 分布")
            st.bar_chart(
                sec_df.set_index("Code")["vsセクター"].clip(-10, 10).sort_values(ascending=False)
            )
            st.caption("0 より上 = セクター平均をアウトパフォーム / 0 より下 = アンダーパフォーム")
        st.divider()
        st.write("#### セクター別ボラティリティ（標準偏差）")
        st.bar_chart(sec.set_index("Sector17")["標準偏差"].sort_values(ascending=False))
