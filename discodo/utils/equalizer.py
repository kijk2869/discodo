def bassboost(Percentage):
    multiplier = Percentage * 2 / 5

    return {
        "anequalizer": "|".join(
            [
                f"c0 f={i[0]} w=100 g={i[1] * multiplier}|c1 f={i[0]} w=100 g={i[1] * multiplier}"
                for i in [
                    [25, -0.05],
                    [40, 0.07],
                    [63, 0.16],
                    [100, 0.03],
                    [160, -0.05],
                    [250, -0.11],
                ]
            ]
        )
    }
