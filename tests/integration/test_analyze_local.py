import time
from pathlib import Path
from src.services.analyze import generate_acoustid, get_spectral_ceiling, calculate_quality_score

test_wav = Path("/tmp/test.wav")

print(f"Testing Analysis for: {test_wav.name}")
print("-" * 40)

print("\n1. Generating Fingerprint on chunk...")
t2 = time.time()
fp = generate_acoustid(test_wav)
t3 = time.time()
print(f"   AcoustID: {'[GENERATED]' if fp else 'FAILED'} (Took {t3-t2:.2f}s)")

print("\n2. Computing Spectral Ceiling on chunk...")
t4 = time.time()
ceiling = get_spectral_ceiling(test_wav)
t5 = time.time()
print(f"   Spectral Ceiling: {ceiling:.2f} Hz" if ceiling else "   Spectral Ceiling: FAILED")
print(f"   (Took {t5-t4:.2f}s)")

print("\n3. Calculating Score...")
if ceiling:
    score, verdict = calculate_quality_score('opus', 128000, None, ceiling)
    print(f"   Calculated Score: {score}")
    print(f"   Calculated Verdict: {verdict}")
