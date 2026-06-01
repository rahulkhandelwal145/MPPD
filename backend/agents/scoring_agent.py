from datetime import datetime

import pandas as pd


def _to_peer_group(is_minister: bool, is_speaker: bool) -> str:
    if is_minister or is_speaker:
        return "minister"
    return "non-minister"


def _percentile_score(series: pd.Series) -> pd.Series:
    return (series.rank(method="min", pct=True) * 100).round(1)


def _rank_column(series: pd.Series) -> pd.Series:
    return series.rank(method="min").astype(pd.Int64Dtype())


async def run_scoring_agent(state: dict) -> dict:
    raw_data = state.get("raw_mp_data", [])
    mplads_data = state.get("mplads_data", {})

    if not raw_data:
        return {"scored_data": [], "errors": state.get("errors", [])}

    df = pd.DataFrame(raw_data)
    df["attendance_pct"] = pd.to_numeric(df["attendance_pct"], errors="coerce")
    df["questions_count"] = pd.to_numeric(df["questions_count"], errors="coerce")
    df["debates_count"] = pd.to_numeric(df["debates_count"], errors="coerce")
    df["pmb_count"] = pd.to_numeric(df["pmb_count"], errors="coerce")
    df["mplads_utilization"] = df["slug"].map(mplads_data)
    df["peer_group"] = df.apply(
        lambda row: _to_peer_group(bool(row.get("is_minister")), bool(row.get("is_speaker"))),
        axis=1,
    )

    df["attendance_score"] = _percentile_score(df["attendance_pct"].fillna(-1))
    df.loc[df["attendance_pct"].isna(), "attendance_score"] = pd.NA
    df["attendance_rank"] = _rank_column(df["attendance_pct"].fillna(-1))
    df.loc[df["attendance_pct"].isna(), "attendance_rank"] = pd.NA

    non_minister = df[df["peer_group"] == "non-minister"].copy()
    for metric in ["questions_count", "debates_count", "pmb_count"]:
        score_col = metric.replace("_count", "_score")
        rank_col = metric.replace("_count", "_rank")
        non_minister[score_col] = _percentile_score(non_minister[metric].fillna(-1))
        non_minister.loc[non_minister[metric].isna(), score_col] = pd.NA
        non_minister[rank_col] = _rank_column(non_minister[metric].fillna(-1))
        non_minister.loc[non_minister[metric].isna(), rank_col] = pd.NA

    df = df.merge(
        non_minister[["slug", "questions_score", "debates_score", "pmb_score", "questions_rank", "debates_rank", "pmb_rank"]],
        on="slug",
        how="left",
    )

    df.loc[df["peer_group"] == "minister", ["questions_score", "debates_score", "pmb_score"]] = pd.NA
    df.loc[df["peer_group"] == "minister", ["questions_rank", "debates_rank", "pmb_rank"]] = pd.NA

    df["total_peers"] = df.groupby("peer_group")["slug"].transform("count")
    df["scored_at"] = datetime.utcnow()

    scored_data = []
    for _, row in df.iterrows():
        scored_data.append(
            {
                "slug": row["slug"],
                "name": row.get("name"),
                "constituency": row.get("constituency"),
                "state": row.get("state"),
                "party": row.get("party"),
                "is_minister": bool(row.get("is_minister")),
                "is_speaker": bool(row.get("is_speaker")),
                "attendance_pct": None if pd.isna(row["attendance_pct"]) else float(row["attendance_pct"]),
                "questions_count": None if pd.isna(row["questions_count"]) else int(row["questions_count"]),
                "debates_count": None if pd.isna(row["debates_count"]) else int(row["debates_count"]),
                "pmb_count": None if pd.isna(row["pmb_count"]) else int(row["pmb_count"]),
                "mplads_utilization": None if pd.isna(row["mplads_utilization"]) else float(row["mplads_utilization"]),
                "peer_group": row["peer_group"],
                "attendance_score": None if pd.isna(row["attendance_score"]) else float(row["attendance_score"]),
                "questions_score": None if pd.isna(row["questions_score"]) else float(row["questions_score"]),
                "debates_score": None if pd.isna(row["debates_score"]) else float(row["debates_score"]),
                "pmb_score": None if pd.isna(row["pmb_score"]) else float(row["pmb_score"]),
                "attendance_rank": None if pd.isna(row["attendance_rank"]) else int(row["attendance_rank"]),
                "questions_rank": None if pd.isna(row["questions_rank"]) else int(row["questions_rank"]),
                "debates_rank": None if pd.isna(row["debates_rank"]) else int(row["debates_rank"]),
                "pmb_rank": None if pd.isna(row["pmb_rank"]) else int(row["pmb_rank"]),
                "total_peers": int(row["total_peers"]),
                "scored_at": row["scored_at"],
            }
        )

    return {"scored_data": scored_data, "errors": state.get("errors", [])}
