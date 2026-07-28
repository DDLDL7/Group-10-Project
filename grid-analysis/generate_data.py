"""Seeded synthetic Ghana electricity grid dataset generator."""
import random

import numpy as np

SEED = 42


def main():
    random.seed(SEED)
    np.random.seed(SEED)


if __name__ == "__main__":
    main()
