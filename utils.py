def is_political(text: str) -> bool:
    political_keywords = [
        "украина", "україна", "ukraine", "zelensky", "зеленский", "киев", "київ",
        "донбасс", "донецк", "луганск", "россия", "russia", "политика", "война",
        "военные", "конфликт", "санкции", "путин", "мобилизация", "спецоперация"
    ]
    text_lower = text.lower()
    return any(word in text_lower for word in political_keywords)
