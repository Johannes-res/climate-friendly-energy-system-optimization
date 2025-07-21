import numpy as np

N = 96
werte1 = [np.sin(np.pi * n / (N - 1)) for n in range(N)]

print("1.Werte_sin:")
for n, wert in enumerate(werte1):
    print(f"{wert:.4f}")


werte2 = [(1 + np.cos(2 * np.pi * n / (N - 1))) / 2 for n in range(N)]

print("2.Werte_cos:")
for n, wert in enumerate(werte2):
    print(f"{wert:.4f}")
