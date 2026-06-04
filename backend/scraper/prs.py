import io
import re
import unicodedata

import pandas as pd

_IMAGE_RE = re.compile(rb'/files/mptrack/18-lok-sabha/profile_image/\d+\.jpg')


def parse_image_url(html_bytes: bytes) -> str | None:
    match = _IMAGE_RE.search(html_bytes)
    if match:
        return "https://prsindia.org" + match.group(0).decode()
    return None


def _slugify(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")


def _to_float(val) -> float | None:
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _to_int(val) -> int | None:
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


_TERM_WORDS = {
    "first": 1, "second": 2, "third": 3, "fourth": 4,
    "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8,
}


def _parse_terms(val) -> int | None:
    if not val:
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    first_word = str(val).strip().lower().split()[0]
    return _TERM_WORDS.get(first_word)


def parse_csv_download(csv_bytes: bytes) -> list[dict]:
    # "NA" in the CSV is a literal string, not a pandas NA
    df = pd.read_csv(io.BytesIO(csv_bytes), na_values=["NA", ""], keep_default_na=False)

    results = []
    for _, row in df.iterrows():
        note = str(row.get("mp_note") or "")
        note_lower = note.lower()
        is_minister = "minister" in note_lower
        is_speaker = "speaker" in note_lower
        is_loa = "leader of opposition" in note_lower

        # Attendance in the CSV is a 0–1 proportion; convert to 0–100 percentage
        attendance = _to_float(row.get("attendance"))
        if attendance is not None:
            attendance = attendance * 100

        nat_avg_att = _to_float(row.get("attendance_national_average"))
        if nat_avg_att is not None:
            nat_avg_att = nat_avg_att * 100

        st_avg_att = _to_float(row.get("attendance_state_average"))
        if st_avg_att is not None:
            st_avg_att = st_avg_att * 100

        results.append(
            {
                "slug": _slugify(str(row["mp_name"])),
                "name": str(row["mp_name"]),
                "constituency": str(row["pc_name"]) if pd.notna(row.get("pc_name")) else None,
                "state": str(row["state"]) if pd.notna(row.get("state")) else None,
                "party": str(row["mp_political_party"]) if pd.notna(row.get("mp_political_party")) else None,
                "age": _to_int(row.get("mp_age")),
                "gender": str(row["mp_gender"]) if pd.notna(row.get("mp_gender")) else None,
                "education": str(row["educational_qualification"]) if pd.notna(row.get("educational_qualification")) else None,
                "terms": _parse_terms(row.get("term")),
                "is_minister": is_minister,
                "is_speaker": is_speaker,
                "is_loa": is_loa,
                "attendance_pct": attendance,
                "questions_count": _to_int(row.get("questions")),
                "debates_count": _to_int(row.get("debates")),
                "pmb_count": _to_int(row.get("private_member_bills")),
                "national_avg_attendance": nat_avg_att,
                "state_avg_attendance": st_avg_att,
                "national_avg_questions": _to_float(row.get("national_average_questions")),
                "state_avg_questions": _to_float(row.get("state_average_questions")),
                "national_avg_debates": _to_float(row.get("national_average_debate")),
                "state_avg_debates": _to_float(row.get("state_average_debate")),
                "national_avg_pmb": _to_float(row.get("national_average_pmb")),
                "state_avg_pmb": _to_float(row.get("state_average_pmb")),
            }
        )

    return results
