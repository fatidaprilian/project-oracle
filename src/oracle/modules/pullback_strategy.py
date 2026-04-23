from __future__ import annotations

import math

from oracle.domain.models import MarketSnapshot, PullbackSignal


def _sma(values: list[float], period: int) -> float:
    if not values:
        return 0.0
    window = values[-period:] if len(values) >= period else values
    return sum(window) / len(window)


def _ema(values: list[float], period: int) -> float:
    if not values:
        return 0.0
    if len(values) < period:
        return _sma(values, period)

    smoothing = 2 / (period + 1)
    ema_value = sum(values[:period]) / period
    for price in values[period:]:
        ema_value = price * smoothing + ema_value * (1 - smoothing)
    return ema_value


def _bollinger_lower(values: list[float], period: int = 20, std_dev: float = 2.0) -> float:
    if not values:
        return 0.0
    window = values[-period:] if len(values) >= period else values
    mean = sum(window) / len(window)
    variance = sum((value - mean) ** 2 for value in window) / len(window)
    return mean - (std_dev * math.sqrt(variance))


def _is_bullish_pinbar(open_price: float, close_price: float, high_price: float, low_price: float) -> bool:
    candle_range = max(high_price - low_price, 1e-9)
    body = abs(close_price - open_price)
    lower_wick = min(open_price, close_price) - low_price
    upper_wick = high_price - max(open_price, close_price)

    if body / candle_range > 0.35:
        return False
    if lower_wick < body * 2.0:
        return False
    if lower_wick < upper_wick * 1.2:
        return False
    return close_price > open_price


def _is_near(price: float, level: float, tolerance: float) -> bool:
    return abs(price - level) / max(abs(level), 1e-9) <= tolerance


def evaluate_stock_pullback(snapshot: MarketSnapshot) -> PullbackSignal:
    if len(snapshot.closes) < 200 or len(snapshot.highs) < 200 or len(snapshot.lows) < 200:
        return PullbackSignal(
            is_valid=False,
            strategy_name="NONE",
            confidence_score=0.0,
            ema_200=0.0,
            ma_99=0.0,
            volume_ratio=0.0,
            reason_codes=["INSUFFICIENT_BARS_FOR_PULLBACK"],
        )

    volumes = snapshot.volumes or []
    if len(volumes) < 20:
        return PullbackSignal(
            is_valid=False,
            strategy_name="NONE",
            confidence_score=0.0,
            ema_200=0.0,
            ma_99=0.0,
            volume_ratio=0.0,
            reason_codes=["INSUFFICIENT_VOLUME_HISTORY"],
        )

    ema_200 = _ema(snapshot.closes, 200)
    ma_99 = _sma(snapshot.closes, 99)
    lower_band = _bollinger_lower(snapshot.closes, 20, 2.0)

    trend_aligned = snapshot.current_price >= ema_200

    volume_ma20 = _sma(volumes, 20)
    volume_ratio = snapshot.volume / max(volume_ma20, 1e-9)
    volume_anomaly = volume_ratio >= 1.2

    open_proxy = snapshot.closes[-2]
    close_price = snapshot.closes[-1]
    high_price = snapshot.highs[-1]
    low_price = snapshot.lows[-1]
    pinbar_confirmed = _is_bullish_pinbar(open_proxy, close_price, high_price, low_price)

    dynamic_wall_touched = low_price <= ma_99 * 1.003 or low_price <= lower_band * 1.003

    support_100 = min(snapshot.lows[-100:])
    support_touched = _is_near(low_price, support_100, tolerance=0.015)

    golden_pullback_ready = all(
        [
            trend_aligned,
            volume_anomaly,
            pinbar_confirmed,
            dynamic_wall_touched,
            support_touched,
        ]
    )

    prior_pullback_volumes = volumes[-6:-1] if len(volumes) >= 6 else []
    silent_pullback = bool(prior_pullback_volumes) and (
        _sma(prior_pullback_volumes, len(prior_pullback_volumes)) <= volume_ma20 * 0.8
    )
    silent_pullback_ready = golden_pullback_ready and silent_pullback

    confidence_checks = [
        trend_aligned,
        volume_anomaly,
        pinbar_confirmed,
        dynamic_wall_touched,
        support_touched,
    ]
    confidence_score = round(
        (sum(1 for check in confidence_checks if check) / len(confidence_checks)) * 100,
        2,
    )

    if silent_pullback_ready:
        return PullbackSignal(
            is_valid=True,
            strategy_name="SILENT_PULLBACK",
            confidence_score=confidence_score,
            ema_200=round(ema_200, 6),
            ma_99=round(ma_99, 6),
            volume_ratio=round(volume_ratio, 6),
            reason_codes=["PULLBACK_READY", "SILENT_PULLBACK_CONFIRMED"],
        )

    if golden_pullback_ready:
        return PullbackSignal(
            is_valid=True,
            strategy_name="GOLDEN_PULLBACK",
            confidence_score=confidence_score,
            ema_200=round(ema_200, 6),
            ma_99=round(ma_99, 6),
            volume_ratio=round(volume_ratio, 6),
            reason_codes=["PULLBACK_READY", "GOLDEN_PULLBACK_CONFIRMED"],
        )

    reason_codes: list[str] = []
    if not trend_aligned:
        reason_codes.append("TREND_BELOW_EMA200")
    if not volume_anomaly:
        reason_codes.append("VOLUME_BELOW_1P2_MA20")
    if not pinbar_confirmed:
        reason_codes.append("PINBAR_NOT_CONFIRMED")
    if not dynamic_wall_touched:
        reason_codes.append("DYNAMIC_WALL_NOT_TOUCHED")
    if not support_touched:
        reason_codes.append("SUPPORT_100_NOT_TOUCHED")

    return PullbackSignal(
        is_valid=False,
        strategy_name="NONE",
        confidence_score=confidence_score,
        ema_200=round(ema_200, 6),
        ma_99=round(ma_99, 6),
        volume_ratio=round(volume_ratio, 6),
        reason_codes=reason_codes,
    )
