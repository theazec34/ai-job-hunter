import re
from urllib.parse import quote, urlencode

from app.schemas import (
    AffordabilityEstimate,
    HousingAssistanceRequest,
    HousingAssistanceResponse,
    HousingCitySuggestion,
    HousingProviderLink,
)

NEARBY_CITIES: dict[str, tuple[str, list[tuple[str, str]]]] = {
    "amsterdam": ("Amsterdam", [("Haarlem", "nearby"), ("Almere", "commuter option")]),
    "rotterdam": ("Rotterdam", [("Delft", "nearby"), ("Schiedam", "adjacent")]),
    "utrecht": ("Utrecht", [("Nieuwegein", "adjacent"), ("Amersfoort", "commuter option")]),
    "the hague": ("The Hague", [("Delft", "nearby"), ("Leiden", "commuter option")]),
    "den haag": ("The Hague", [("Delft", "nearby"), ("Leiden", "commuter option")]),
    "eindhoven": ("Eindhoven", [("Veldhoven", "adjacent"), ("Helmond", "commuter option")]),
    "groningen": ("Groningen", [("Haren", "nearby"), ("Assen", "commuter option")]),
}

MANUAL_CHECKLIST = [
    "Open the provider page and confirm the listing is still available.",
    "Verify the landlord or agent identity and property address independently.",
    "Check municipality registration permission in the signed lease before paying.",
    "Never pay before viewing, identity checks, and a written rental agreement.",
    "Confirm fees, deposit, utilities, income requirements, and cancellation terms.",
]


def city_slug(city: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", city.lower()).strip("-")


def provider_links(city: str) -> list[HousingProviderLink]:
    funda_query = urlencode({"selected_area": f'["{city}"]'})
    slug = quote(city_slug(city), safe="-")
    return [
        HousingProviderLink(
            provider="Funda",
            url=f"https://www.funda.nl/zoeken/huur?{funda_query}",
        ),
        HousingProviderLink(
            provider="Pararius",
            url=f"https://www.pararius.com/apartments/{slug}",
        ),
        HousingProviderLink(
            provider="Kamernet",
            url=f"https://kamernet.nl/en/for-rent/properties-{slug}",
        ),
    ]


def affordability(payload: HousingAssistanceRequest) -> AffordabilityEstimate | None:
    if payload.annual_gross_salary is not None:
        monthly_gross = payload.annual_gross_salary / 12
        minimum = monthly_gross * 0.25
        maximum = monthly_gross * 0.35
        basis = "25%-35% of supplied gross monthly salary; provider rules may differ."
        if payload.max_monthly_rent is not None:
            maximum = min(maximum, payload.max_monthly_rent)
            minimum = min(minimum, maximum)
            basis += " Capped by the supplied maximum monthly rent."
    elif payload.max_monthly_rent is not None:
        minimum = payload.max_monthly_rent * 0.8
        maximum = payload.max_monthly_rent
        basis = "80%-100% of the supplied maximum monthly rent."
    else:
        return None
    return AffordabilityEstimate(
        minimum_monthly_rent=round(minimum, 2),
        maximum_monthly_rent=round(maximum, 2),
        basis=basis,
    )


def housing_assistance(payload: HousingAssistanceRequest) -> HousingAssistanceResponse:
    key = " ".join(payload.job_city.lower().split())
    canonical, nearby = NEARBY_CITIES[key]
    cities = [(canonical, "job city"), *nearby]
    return HousingAssistanceResponse(
        job_city=canonical,
        nearby_cities=[
            HousingCitySuggestion(
                city=city,
                relation=relation,
                registration_status="unknown",
                provider_links=provider_links(city),
            )
            for city, relation in cities
        ],
        affordability=affordability(payload),
        manual_verification_checklist=MANUAL_CHECKLIST,
        guarantee_notice=(
            "Listing availability, landlord legitimacy, affordability, and registration "
            "permission are not guaranteed."
        ),
        data_notice=(
            "These are static nearby-city suggestions and provider search links, not current "
            "listings or API integrations. Rental portals are not scraped."
        ),
    )
