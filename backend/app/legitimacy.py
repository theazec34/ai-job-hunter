import re
from dataclasses import dataclass
from urllib.parse import urlparse

TRUSTED_CONNECTORS = {"eures", "arbeitnow", "remotive", "adzuna_nl"}


@dataclass(frozen=True)
class LegitimacyAssessment:
    status: str
    reasons: list[str]


def assess_legitimacy(
    *, source: str, company: str, url: str, description: str
) -> LegitimacyAssessment:
    reasons: list[str] = []
    severe = False
    parsed = urlparse(url)
    if not company.strip():
        reasons.append("missing_company")
    if parsed.scheme != "https" or not parsed.netloc:
        reasons.append("missing_or_non_https_url")
        severe = True
    if len(description.strip()) < 100:
        reasons.append("description_too_short")

    text = description.lower()
    patterns = {
        "upfront_payment_requested": r"\b(upfront|advance)\s+(payment|fee)|\bpay\b.{0,25}\bfee\b",
        "gift_card_or_crypto_payment": (
            r"\b(gift\s*cards?|bitcoin|cryptocurrency|crypto\s+payment)\b"
        ),
        "messaging_only_recruiting": (
            r"\b((telegram|whatsapp).{0,30}(only|exclusive)|"
            r"(only|exclusive).{0,30}(telegram|whatsapp))\b"
        ),
        "unrealistic_income_language": (
            r"\b(guaranteed income|get rich quick|unlimited earnings|"
            r"earn \$?\d{4,}\s*(a day|daily))\b"
        ),
    }
    for reason, pattern in patterns.items():
        if re.search(pattern, text):
            reasons.append(reason)
            severe = True

    if severe:
        return LegitimacyAssessment("rejected", reasons)
    if source not in TRUSTED_CONNECTORS:
        reasons.append("unverified_source")
    if reasons:
        return LegitimacyAssessment("needs_review", reasons)
    return LegitimacyAssessment("source_verified", ["trusted_connector_provenance"])
