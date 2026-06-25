# backend/etl/generate_insights.py
# Author: Hoang Son Lai (AI insight layer)
#
# Generates short, data-grounded narrative insights for both dashboards
# (global_dashboard.html and company_dashboard.html) using Groq's
# llama-3.1-8b-instant model. Runs server-side as part of the daily ETL
# (Phase 1), so the GROQ_API_KEY never reaches the browser.
#
# Output:
#   data/cleaned/insights_global.json
#   data/cleaned/insights_company.json
#
# Scope (kept deliberately small to stay under Groq's free-tier rate limit):
#   Global dashboard  -> only the "latest" fiscal year, one insight per
#                         metric option for Row 1 (Top Companies) and
#                         Row 2 Sector, plus one each for Row 2 Bubble,
#                         Row 3 Heatmap, and Row 4 Market Trends.
#                         (8 + 3 + 1 + 1 + 1 = 14 calls/day)
#   Company dashboard -> only Executive Summary (separate for FY and Q,
#                         since the underlying numbers differ) and one
#                         shared Stock Price insight (same for both tabs,
#                         since both tabs show identical price history).
#                         (21 tickers x (2 summaries + 1 stock) = 63 calls/day)
#   Total: ~77 calls/day, well under typical free-tier rate limits.
#
# These JSON files are pre-computed for every filter combination the
# dashboards expose, so the frontend only ever does a static fetch() —
# no client-side API calls, no exposed key.

import os
import json
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from config import DATA_CLEANED_DIR, TICKERS

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Metric options exposed by each selector in global_dashboard.html
ROW1_METRICS = [
    "revenue", "net_income", "total_assets", "total_equity",
    "total_liabilities", "cash_and_equivalents", "gross_profit",
    "operating_income_ebit",
]
ROW2_SECTOR_METRICS = ["revenue", "total_assets", "net_income"]

REPORT_TYPES = ["FY", "Q"]

# Small pause between calls so we never burst past the free-tier
# requests-per-minute limit, regardless of how fast Groq responds.
CALL_DELAY_SECONDS = 1.3

SYSTEM_PROMPT = (
    "You are a financial analyst writing very short insight captions for a "
    "live dashboard. Rules: 1-2 sentences max. Be specific and reference "
    "actual numbers/tickers given to you. No generic filler, no disclaimers, "
    "no markdown, no headers. Plain text only. If data is missing or empty, "
    "say so briefly instead of guessing."
)


# ----------------------------------------------------------------------
# Low-level Groq call with retry/backoff
# ----------------------------------------------------------------------
def call_groq(user_prompt, max_tokens=120, retries=4):
    if not GROQ_API_KEY:
        return "Insight unavailable (GROQ_API_KEY not configured)."

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.4,
    }

    result = "Insight temporarily unavailable."
    for attempt in range(retries):
        try:
            resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                result = data["choices"][0]["message"]["content"].strip()
                break
            elif resp.status_code == 429:
                # Honor Retry-After if Groq sends it, otherwise back off gradually.
                retry_after = resp.headers.get("Retry-After")
                wait = float(retry_after) if retry_after else (3 + attempt * 3)
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"  Groq error {resp.status_code}: {resp.text[:200]}")
                time.sleep(2)
        except requests.RequestException as e:
            print(f"  Request failed: {e}")
            time.sleep(2)

    # Always pause after a call (success or final failure) to stay well under
    # the per-minute request budget for the rest of the batch job.
    time.sleep(CALL_DELAY_SECONDS)
    return result


def safe_num(val, default=0):
    if val is None:
        return default
    try:
        if isinstance(val, float) and np.isnan(val):
            return default
        return val
    except TypeError:
        return default


def fmt_compact(n):
    """Compact number formatting similar to the dashboards' formatCompactNumber."""
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "N/A"
    if np.isnan(n):
        return "N/A"
    sign = "-" if n < 0 else ""
    n = abs(n)
    if n >= 1e12:
        return f"{sign}{n/1e12:.1f}T"
    if n >= 1e9:
        return f"{sign}{n/1e9:.1f}B"
    if n >= 1e6:
        return f"{sign}{n/1e6:.1f}M"
    if n >= 1e3:
        return f"{sign}{n/1e3:.1f}K"
    return f"{sign}{n:.0f}"


def metric_label(metric):
    return metric.replace("_", " ").title()


def pct_change(current, previous):
    """Safe percentage change between two values. Returns None if not computable."""
    current = safe_num(current, None)
    previous = safe_num(previous, None)
    if current is None or previous is None or previous == 0:
        return None
    return (current - previous) / abs(previous) * 100


def fmt_change(value, suffix="% vs prior period"):
    """Formats a pct_change() result as a +/- string, or '' if unavailable."""
    if value is None:
        return ""
    return f" ({value:+.1f}{suffix})"


# ----------------------------------------------------------------------
# Data loading helpers
# ----------------------------------------------------------------------
def load_data():
    companies = pd.read_csv(os.path.join(DATA_CLEANED_DIR, "companies.csv"))
    financials = pd.read_csv(os.path.join(DATA_CLEANED_DIR, "financial_statements.csv"))
    stocks = pd.read_csv(os.path.join(DATA_CLEANED_DIR, "stock_prices.csv"))

    financials["report_date"] = pd.to_datetime(financials["report_date"], errors="coerce")
    stocks["date"] = pd.to_datetime(stocks["date"], errors="coerce")

    companies_map = companies.set_index("ticker").to_dict("index")
    return companies, financials, stocks, companies_map


def latest_fy_financials(financials):
    """Replicates applyYearFilter('latest'): newest FY row per ticker with non-zero revenue."""
    fy = financials[financials["period"] == "FY"].copy()
    fy = fy[(fy["revenue"].notna()) & (fy["revenue"] != 0)]
    fy = fy.sort_values("report_date", ascending=False)
    return fy.groupby("ticker", as_index=False).first()


# ----------------------------------------------------------------------
# GLOBAL DASHBOARD INSIGHTS (latest year only)
# ----------------------------------------------------------------------
def build_global_insights(companies, financials, stocks, companies_map):
    print("\n=== Generating GLOBAL dashboard insights (latest year only) ===")

    latest = latest_fy_financials(financials)
    latest = latest.merge(
        companies[["ticker", "sector", "name"]], on="ticker", how="left", suffixes=("", "_c")
    )

    result = {"row1": {}, "row2_sector": {}}

    # --- Row 1: Top Companies Ranking, one insight per metric ---
    for metric in ROW1_METRICS:
        print(f"-- Row1 metric: {metric}")
        if metric not in latest.columns:
            result["row1"][metric] = f"Metric '{metric}' is not available in the dataset."
            continue
        top = latest[latest[metric].notna() & (latest[metric] != 0)]
        top = top.sort_values(metric, ascending=False).head(5)
        if not top.empty:
            label = metric_label(metric)
            lines = "; ".join(
                f"{r.ticker} ({r.name}): {label} {fmt_compact(getattr(r, metric))} USD"
                for r in top.itertuples()
            )
            prompt = (
                f"Top companies ranked by {label} (latest fiscal year): {lines}. "
                f"Write a 1-2 sentence insight highlighting the leader and any notable gap "
                f"between top companies for this metric."
            )
        else:
            prompt = f"No data is currently available for the metric '{metric_label(metric)}'. State this briefly."
        result["row1"][metric] = call_groq(prompt)

    # --- Row 2 Sector: sector distribution, one insight per metric ---
    for metric in ROW2_SECTOR_METRICS:
        print(f"-- Row2 sector metric: {metric}")
        if metric not in latest.columns:
            result["row2_sector"][metric] = f"Metric '{metric}' is not available in the dataset."
            continue
        sector_agg = latest.groupby("sector")[metric].sum().sort_values(ascending=False)
        sector_agg = sector_agg[sector_agg != 0]
        if not sector_agg.empty:
            label = metric_label(metric)
            total = sector_agg.sum()
            lines = "; ".join(
                f"{s}: {fmt_compact(v)} USD ({v/total*100:.1f}%)" for s, v in sector_agg.items()
            )
            prompt = (
                f"Sector distribution by {label} (latest fiscal year): {lines}. "
                f"Write a 1-2 sentence insight on sector concentration or dominance for this metric."
            )
        else:
            prompt = f"No sector data is currently available for the metric '{metric_label(metric)}'. State this briefly."
        result["row2_sector"][metric] = call_groq(prompt)

    # --- Row 2 Bubble (Revenue vs Net Income vs Assets), fixed chart ---
    print("-- Row2 bubble")
    bubble = latest.dropna(subset=["revenue", "net_income"]).copy()
    bubble = bubble[bubble["revenue"] != 0]
    if not bubble.empty:
        bubble["net_margin_calc"] = bubble["net_income"] / bubble["revenue"]
        best = bubble.sort_values("net_margin_calc", ascending=False).iloc[0]
        worst = bubble.sort_values("net_margin_calc", ascending=True).iloc[0]
        prompt = (
            "Company performance map (Revenue vs Net Income, bubble size = Total Assets), latest fiscal year. "
            f"Highest net margin: {best.ticker} ({best.net_margin_calc*100:.1f}% margin, "
            f"revenue {fmt_compact(best.revenue)} USD). "
            f"Lowest net margin: {worst.ticker} ({worst.net_margin_calc*100:.1f}% margin). "
            "Write a 1-2 sentence insight comparing profitability efficiency across companies."
        )
    else:
        prompt = "No revenue/net income data is currently available. State this briefly."
    result["row2_bubble"] = call_groq(prompt)

    # --- Row 3 Heatmap (financial health ratios), fixed chart ---
    print("-- Row3 heatmap")
    ratios = latest.dropna(subset=["roe"])
    if not ratios.empty:
        best_roe = ratios.sort_values("roe", ascending=False).iloc[0]
        worst_de = latest.dropna(subset=["debt_to_equity"]).sort_values(
            "debt_to_equity", ascending=False
        )
        worst_de_row = worst_de.iloc[0] if not worst_de.empty else None
        prompt = (
            "Financial health ratios across companies, latest fiscal year. "
            f"Highest ROE: {best_roe.ticker} ({best_roe.roe*100:.1f}%). "
            + (
                f"Highest Debt/Equity (most leveraged): {worst_de_row.ticker} "
                f"({worst_de_row.debt_to_equity:.2f}x). "
                if worst_de_row is not None
                else ""
            )
            + "Write a 1-2 sentence insight on which companies stand out for returns vs leverage risk."
        )
    else:
        prompt = "No ratio data is currently available. State this briefly."
    result["row3_heatmap"] = call_groq(prompt)

    # --- Row 4: Market Trends (always latest, independent of any filter) ---
    print("-- Row4 market trends")

    top_tickers = (
        latest
        .sort_values("revenue", ascending=False)["ticker"]
        .dropna()
        .tolist()
    )

    returns = []

    max_date = stocks["date"].max()

    if pd.notna(max_date):
        min_date = max_date - pd.DateOffset(months=12)

        for t in top_tickers:
            s = (
                stocks[
                    (stocks["ticker"] == t)
                    & (stocks["date"] >= min_date)
                ]
                .sort_values("date")
            )

            if len(s) > 1:
                start_p = s.iloc[0]["close"]
                end_p = s.iloc[-1]["close"]

                if pd.notna(start_p) and start_p > 0 and pd.notna(end_p):
                    ret = (end_p - start_p) / start_p * 100
                    returns.append((t, ret))

    # Sort from best to worst
    returns.sort(key=lambda x: x[1], reverse=True)

    # Debug (optional)
    print("\nTop revenue companies - 12M returns")
    for t, r in returns:
        print(f"{t}: {r:+.2f}%")

    if returns:

        best_ticker, best_return = returns[0]
        worst_ticker, worst_return = returns[-1]

        lines = "; ".join(
            f"{t}: {r:+.1f}%"
            for t, r in returns
        )

        prompt = f"""
        The following are 12-month cumulative stock returns for the highest-revenue companies:

        {lines}

        Verified facts:
        - Best performer: {best_ticker} ({best_return:+.1f}%)
        - Worst performer: {worst_ticker} ({worst_return:+.1f}%)

        Write a concise 2-3 sentence market insight.
        You MUST mention the verified best and worst performers above.
        Do not identify any other company as the best or worst performer.
        """

    else:

        prompt = (
            "No 12-month stock return data is currently available. "
            "State this briefly."
        )

    result["row4_market_trends"] = call_groq(prompt)

    result["_generated_at"] = datetime.now(timezone.utc).isoformat()
    return result


# ----------------------------------------------------------------------
# COMPANY DASHBOARD INSIGHTS
# Only: Executive Summary (per FY/Q, numbers differ) + Stock insight
# (shared across FY/Q tabs, since both show the same price history).
# ----------------------------------------------------------------------
def build_company_insights(companies, financials, stocks, companies_map):
    print("\n=== Generating COMPANY dashboard insights ===")
    print("(Executive Summary per FY/Q + one shared Stock insight per ticker)")
    result = {}
 
    for ticker in TICKERS:
        info = companies_map.get(ticker, {})
        name = info.get("name", ticker)
        sector = info.get("sector", "Unknown")
 
        result[ticker] = {}
        stk = stocks[stocks["ticker"] == ticker].sort_values("date")
 
        # --- Stock insight: shared across FY and Q tabs (identical price chart) ---
        print(f"-- {ticker} [stock]")
 
        if not stk.empty and len(stk) > 5:
 
            stk = stk.sort_values("date").reset_index(drop=True)
 
            latest_stock = stk.iloc[-1]
            latest_price = latest_stock["close"]
            closes = stk["close"].tolist()
 
            # ===== 1 DAY =====
            day_change = None
            if len(stk) >= 2:
                prev_price = stk.iloc[-2]["close"]
 
                if pd.notna(prev_price) and prev_price > 0:
                    day_change = (latest_price - prev_price) / prev_price * 100
 
            # ===== 3 MONTH =====
            three_month_change = None
            idx_3m = max(0, len(stk) - 63)   # ~63 trading days
 
            start_3m = stk.iloc[idx_3m]["close"]
 
            if pd.notna(start_3m) and start_3m > 0:
                three_month_change = (
                    (latest_price - start_3m) / start_3m * 100
                )
 
            # ===== 12 MONTH =====
            one_year_change = None
            idx_1y = max(0, len(stk) - 252)  # ~252 trading days
 
            start_1y = stk.iloc[idx_1y]["close"]
 
            if pd.notna(start_1y) and start_1y > 0:
                one_year_change = (
                    (latest_price - start_1y) / start_1y * 100
                )
 
            # ===== MA20 / MA50 / BOLLINGER BANDS (latest day) =====
            # Mirrors the frontend's calculateMA/calculateBB exactly:
            # SMA over the last N closes, stdDev = population std (divide by period, not period-1).
            def calc_ma(data, period):
                if len(data) < period:
                    return None
                window = data[-period:]
                return sum(window) / period
 
            def calc_bb(data, period=20, std_mult=2):
                ma = calc_ma(data, period)
                if ma is None:
                    return None, None
                window = data[-period:]
                variance = sum((x - ma) ** 2 for x in window) / period
                std_dev = variance ** 0.5
                return ma + std_dev * std_mult, ma - std_dev * std_mult
 
            ma20 = calc_ma(closes, 20)
            ma50 = calc_ma(closes, 50)
            bb_upper, bb_lower = calc_bb(closes, 20, 2)  # middle band == ma20
 
            ma20_line = "N/A (fewer than 20 trading days of history)"
            ma50_line = "N/A (fewer than 50 trading days of history)"
            ma_signal_line = ""
            cross_signal_line = ""
            bb_line = "N/A (fewer than 20 trading days of history)"
            bb_signal_line = ""
 
            # --- MA20 / MA50 rule table ---
            # Price > MA20            -> short-term uptrend
            # Price > MA50            -> medium-term uptrend
            # Price > MA20 and MA50   -> Strong bullish
            # Price < MA20 and MA50   -> Strong bearish
            # MA20 > MA50             -> Golden Cross, uptrend
            # MA20 < MA50             -> Death Cross, downtrend
            above_ma20 = None
            above_ma50 = None
            ma_signal = None   # "bullish" | "bearish" | "mixed"
            cross_signal = None  # "golden" | "death" | None
 
            if ma20 is not None:
                vs_ma20_pct = (latest_price - ma20) / ma20 * 100
                above_ma20 = latest_price > ma20
                ma20_line = (
                    f"{ma20:.2f} USD (price is {vs_ma20_pct:+.2f}% "
                    f"{'above' if above_ma20 else 'below'} MA20 -> "
                    f"{'short-term uptrend' if above_ma20 else 'short-term downtrend'})"
                )
 
            if ma50 is not None:
                vs_ma50_pct = (latest_price - ma50) / ma50 * 100
                above_ma50 = latest_price > ma50
                ma50_line = (
                    f"{ma50:.2f} USD (price is {vs_ma50_pct:+.2f}% "
                    f"{'above' if above_ma50 else 'below'} MA50 -> "
                    f"{'medium-term uptrend' if above_ma50 else 'medium-term downtrend'})"
                )
 
            if above_ma20 is not None and above_ma50 is not None:
                if above_ma20 and above_ma50:
                    ma_signal = "bullish"
                    ma_signal_line = "Combined MA signal: STRONG BULLISH (price is above both MA20 and MA50)."
                elif (not above_ma20) and (not above_ma50):
                    ma_signal = "bearish"
                    ma_signal_line = "Combined MA signal: STRONG BEARISH (price is below both MA20 and MA50)."
                else:
                    ma_signal = "mixed"
                    ma_signal_line = "Combined MA signal: MIXED (price is above one moving average but below the other)."
 
            if ma20 is not None and ma50 is not None:
                if ma20 > ma50:
                    cross_signal = "golden"
                    cross_signal_line = "Cross signal: GOLDEN CROSS (MA20 is above MA50, an uptrend signal)."
                elif ma20 < ma50:
                    cross_signal = "death"
                    cross_signal_line = "Cross signal: DEATH CROSS (MA20 is below MA50, a downtrend signal)."
                else:
                    cross_signal_line = "Cross signal: MA20 and MA50 are essentially equal right now."
 
            # --- Bollinger Bands rule table (middle band = MA20) ---
            # Price near Upper Band  -> Strong bullish momentum
            # Price above Upper Band -> Potentially overbought; trend remains strong
            # Price near Middle Band -> Neutral momentum
            # Price near Lower Band  -> Weak momentum / bearish pressure
            # Price below Lower Band -> Potentially oversold or breakdown risk
            bb_signal = None  # "bullish" | "bearish" | "neutral"
 
            if bb_upper is not None and bb_lower is not None and ma20 is not None:
 
                band_width = bb_upper - bb_lower
 
                pct_in_band = (
                    (latest_price - bb_lower) / band_width * 100
                    if band_width > 0
                    else 50
                )
 
                bb_line = (
                    f"Upper {bb_upper:.2f} USD / Middle (MA20) {ma20:.2f} USD / "
                    f"Lower {bb_lower:.2f} USD (price sits at ~{pct_in_band:.0f}% of band width)"
                )
 
                # Above upper band
                if latest_price > bb_upper:
                    bb_signal = "bullish"
                    bb_signal_line = (
                        "BB signal: ABOVE UPPER BAND - potentially overbought; trend remains strong."
                    )
 
                # Below lower band
                elif latest_price < bb_lower:
                    bb_signal = "bearish"
                    bb_signal_line = (
                        "BB signal: BELOW LOWER BAND - potentially oversold or breakdown risk."
                    )
 
                else:
                    # inside the bands -> interpret relative position
 
                    # near upper band (top ~20% zone)
                    if latest_price >= bb_upper - 0.2 * band_width:
                        bb_signal = "bullish"
                        bb_signal_line = (
                            "BB signal: NEAR UPPER BAND - strong bullish momentum."
                        )
 
                    # near lower band (bottom ~20% zone)
                    elif latest_price <= bb_lower + 0.2 * band_width:
                        bb_signal = "bearish"
                        bb_signal_line = (
                            "BB signal: NEAR LOWER BAND - weak momentum / bearish pressure."
                        )
 
                    # near middle band (around MA20)
                    elif abs(latest_price - ma20) / ma20 < 0.01:
                        bb_signal = "neutral"
                        bb_signal_line = (
                            "BB signal: NEAR MIDDLE BAND - neutral momentum."
                        )
 
                    else:
                        # middle area (between zones)
                        bb_signal = "neutral"
                        bb_signal_line = (
                            "BB signal: NEUTRAL ZONE - no clear directional pressure."
                        )
 
            # --- Contradiction check: do the MA, cross, and BB signals actually agree? ---
            # Each signal is normalized to "bullish" / "bearish" / "mixed" / "neutral" / None
            # so we can detect disagreement instead of letting the model silently pick one
            # signal and ignore the others (or invent a false consensus).
            directional_signals = {
                "Combined MA signal": ma_signal,
                "Cross signal": "bullish" if cross_signal == "golden" else (
                    "bearish" if cross_signal == "death" else None
                ),
                "BB signal": bb_signal,
            }
            present_signals = {k: v for k, v in directional_signals.items() if v is not None}
            distinct_directions = set(present_signals.values())
 
            if len(distinct_directions) <= 1:
                contradiction_line = (
                    "Signal agreement check: all available technical signals point in the same "
                    "direction (or are neutral/mixed on their own) — no contradiction to flag."
                )
            else:
                conflict_desc = "; ".join(f"{k} = {v}" for k, v in present_signals.items())
                contradiction_line = (
                    "Signal agreement check: the technical signals DISAGREE with each other "
                    f"({conflict_desc}). You MUST explicitly acknowledge this mixed/conflicting "
                    "picture in your answer instead of presenting only one signal as if it were "
                    "the whole story — explain briefly that short-term and longer-term (or "
                    "momentum-based) signals are pointing in different directions."
                )
 
            prompt = f"""
            Stock performance for {ticker}:
 
            Current close price: {latest_price:.2f} USD
 
            Daily performance:
            {'N/A' if day_change is None else f'{day_change:+.2f}% vs previous trading day'}
 
            3-month performance:
            {'N/A' if three_month_change is None else f'{three_month_change:+.2f}%'}
 
            12-month performance:
            {'N/A' if one_year_change is None else f'{one_year_change:+.2f}%'}
 
            20-day moving average (MA20): {ma20_line}
            50-day moving average (MA50): {ma50_line}
 
            Bollinger Bands (20-day, 2 std dev, middle band = MA20): {bb_line}
 
            Verified technical signals (use these exact labels as the basis for your interpretation,
            do not invent or contradict them):
            - {ma_signal_line or "Combined MA signal: Not available."}
            - {cross_signal_line or "Cross signal: Not available."}
            - {bb_signal_line or "BB signal: Not available."}
 
            {contradiction_line}
 
            Write a concise 5-6 sentence insight for a beginner/retail investor who may not know
            technical analysis. Rules for clarity:
            - First mention the latest daily movement, then place it in the 3-month/12-month trend context.
            - Describe whether price is above or below MA20 and MA50 in plain terms, then interpret using
              the verified combined MA signal and cross signal above (translate labels like "strong bullish",
              "strong bearish", "mixed", "golden cross", "death cross" into plain language - don't just repeat
              the jargon term on its own without explaining what it means for the reader).
            - Also mention the golden/death cross signal in plain language.
            - Before interpreting Bollinger Bands, briefly explain in plain words what they represent
              (e.g. "a band showing the normal trading range based on recent volatility") in one short clause.
            - Then interpret it in plain language.
            - If the signal agreement check above reports a disagreement, you must say so plainly
              (e.g. "short-term momentum looks strong while the longer-term trend still looks weak")
              rather than picking only the most bullish or most bearish signal and ignoring the rest.
            """
 
        else:
 
            prompt = (
                f"Limited stock price history is available for {ticker}. "
                "State this briefly."
            )
 
        stock_insight = call_groq(prompt, max_tokens=200)
        result[ticker]["stock"] = stock_insight

        # --- Executive Summary: separate for FY and Q ---
        for period in REPORT_TYPES:
            fin = financials[
                (financials["ticker"] == ticker)
                & (financials["period"] == period)
                & (financials["revenue"].notna())
                & (financials["revenue"] != 0)
            ].sort_values("report_date")

            print(f"-- {ticker} [{period}] executive_summary")

            if fin.empty:
                result[ticker][period] = {
                    "executive_summary": (
                        f"No {('annual' if period == 'FY' else 'quarterly')} "
                        f"financial data available for {ticker}."
                    )
                }
                continue

            latest = fin.iloc[-1]
            prev = fin.iloc[-2] if len(fin) > 1 else None

            # --- Latest stock close + change vs ~3 months ago (not the prior report period) ---
            latest_stock = stk.iloc[-1] if not stk.empty else None
            stock_3m_ago = stk.iloc[max(0, len(stk) - 63)] if not stk.empty else None  # ~63 trading days
            stock_price_change = (
                pct_change(latest_stock["close"], stock_3m_ago["close"])
                if latest_stock is not None and stock_3m_ago is not None
                else None
            )

            label = "FY" if period == "FY" else "quarter"

            # --- Period-over-period growth for every metric mentioned in the prompt ---
            rev_growth = pct_change(latest["revenue"], prev["revenue"]) if prev is not None else None
            inc_growth = (
                pct_change(latest.get("net_income"), prev.get("net_income")) if prev is not None else None
            )
            margin_growth = (
                pct_change(latest.get("net_margin"), prev.get("net_margin")) if prev is not None else None
            )
            roe_growth = pct_change(latest.get("roe"), prev.get("roe")) if prev is not None else None
            de_growth = (
                pct_change(latest.get("debt_to_equity"), prev.get("debt_to_equity"))
                if prev is not None
                else None
            )
            cr_growth = (
                pct_change(latest.get("current_ratio"), prev.get("current_ratio"))
                if prev is not None
                else None
            )

            is_bank = ticker in ("JPM", "BAC")
            current_ratio_line = (
                "" if is_bank else
                f"current ratio {safe_num(latest.get('current_ratio'), 0):.2f}"
                f"{fmt_change(cr_growth)}. "
            )

            stock_close_str = (
                f"{latest_stock['close']:.2f} USD" if latest_stock is not None else "N/A"
            )

            prompt = (
                f"Company: {name} ({ticker}), sector {sector}. Latest {label} report: "
                f"revenue {fmt_compact(latest['revenue'])} USD{fmt_change(rev_growth)}; "
                f"net income {fmt_compact(latest.get('net_income'))} USD{fmt_change(inc_growth)}; "
                f"net margin {safe_num(latest.get('net_margin'), 0)*100:.1f}%{fmt_change(margin_growth)}; "
                f"ROE {safe_num(latest.get('roe'), 0)*100:.1f}%{fmt_change(roe_growth)}; "
                f"debt-to-equity {safe_num(latest.get('debt_to_equity'), 0):.2f}x. "
                f"{current_ratio_line}"
                f"Latest stock close: {stock_close_str}"
                f"{fmt_change(stock_price_change, suffix='% vs 3 months ago')}. "
                "Note: the figures in parentheses are the RELATIVE percentage change of that ratio versus the "
                "prior period (e.g. margin going from 20% to 22% is reported as +10%, not +2 points) — describe "
                "them as relative changes, not percentage-point changes. Do not use the term 'YoY' since this "
                "may be comparing quarter to quarter, not year over year. "
                "Write a 5-6 sentence executive summary as flowing, well-connected prose — like a human analyst "
                "would write in a report, not a list of 'Metric: value, change' statements."
                "Cover growth, profitability, liquidity, and overall financial health, in a "
                "tone suitable for an investor dashboard. Note that for BAC and JPM, don't say anything about "
                "current ratio because they are banks."
            )
            exec_summary = call_groq(prompt, max_tokens=220)

            result[ticker][period] = {"executive_summary": exec_summary}

    result["_generated_at"] = datetime.now(timezone.utc).isoformat()
    return result


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    print("--- Generating AI Insights (Groq) ---")
    if not GROQ_API_KEY:
        print("WARNING: GROQ_API_KEY not set. Writing placeholder insights.")

    companies, financials, stocks, companies_map = load_data()

    global_insights = build_global_insights(companies, financials, stocks, companies_map)
    global_path = os.path.join(DATA_CLEANED_DIR, "insights_global.json")
    with open(global_path, "w", encoding="utf-8") as f:
        json.dump(global_insights, f, ensure_ascii=False, indent=2)
    print(f"Saved: {global_path}")

    company_insights = build_company_insights(companies, financials, stocks, companies_map)
    company_path = os.path.join(DATA_CLEANED_DIR, "insights_company.json")
    with open(company_path, "w", encoding="utf-8") as f:
        json.dump(company_insights, f, ensure_ascii=False, indent=2)
    print(f"Saved: {company_path}")

    print("--- AI Insights Generation Complete ---")


if __name__ == "__main__":
    main()