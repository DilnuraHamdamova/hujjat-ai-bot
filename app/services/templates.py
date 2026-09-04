TEMPLATE_FAMILIES = ("classic", "modern", "europass")
TEMPLATE_CODES = tuple(
    f"{family}_{number}"
    for family in TEMPLATE_FAMILIES
    for number in range(1, 4)
)


def template_family(template_code: str) -> str:
    family = template_code.split("_", 1)[0]
    return family if family in TEMPLATE_FAMILIES else "classic"
