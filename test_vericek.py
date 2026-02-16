from thefuzz import fuzz

print(f"VeriCek.py vs Maverick (Set): {fuzz.token_set_ratio('VeriCek.py', 'Maverick')}")
print(f"VeriCek.py vs Maverick (Sort): {fuzz.token_sort_ratio('VeriCek.py', 'Maverick')}")
print(f"VeriCek.py vs Maverick (WRatio): {fuzz.WRatio('VeriCek.py', 'Maverick')}")
