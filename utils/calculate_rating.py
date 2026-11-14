from math import floor


def calculate_rating(score: int, const: float) -> float:
    """
    Calculate the rating of a CHUNITHM chart from its score and constant.

    @param score: The score obtained in game.
    @param const: The constant of the song concerned.
    @return: The calculated rating value.
    """
    if score >= 1_009_000:
        # SSS+
        return const + 2.15
    if score >= 1_007_500:
        # SSS
        return const + 2.0 + floor((score - 1_007_500) / 100) * 0.01
    if score >= 1_005_000:
        # SS+
        return const + 1.5 + floor((score - 1_005_000) / 50) * 0.01
    if score >= 1_000_000:
        # SS
        return const + 1.0 + floor((score - 1_000_000) / 100) * 0.01
    if score >= 990_000:
        # S+
        return const + 0.6 + floor((score - 990_000) / 250) * 0.01
    if score >= 975_000:
        # S
        return const + floor((score - 975_000) / 250) * 0.01
    if score >= 950_000:
        # AAA
        return max(0.0, const - 1.67 + floor((score - 950_000) / 150) * 0.01)
    if score >= 925_000:
        # AA
        return max(0.0, const - 3.34 + floor((score - 925_000) / 150) * 0.01)
    if score >= 900_000:
        # A
        return max(0.0, const - 5.0 + floor((score - 900_000) / 150) * 0.01)
    if score >= 800_000:
        # BBB
        return max(
            0.0,
            (const - 5.0) / 2
            + (score - 800_000) / 2_000 * (const - 5.0) * 0.01,
        )
    if score >= 500_000:
        # C ~ B
        return max(0.0, (score - 500_000) / 6_000 * (const - 5.0) * 0.01)

    return 0.0
