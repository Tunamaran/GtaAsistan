import os
import sys
import ast

def verify_syntax(filepath):
    """Syntax check to ensure agents haven't broken the python files."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        print(f"✅ [test-engineer] Syntax Ok: {filepath}")
        return True
    except SyntaxError as e:
        print(f"❌ [test-engineer] Syntax Hata: {filepath}\n{e}")
        return False
    except FileNotFoundError:
        print(f"❌ [test-engineer] Dosya bulunamadı: {filepath}")
        return False

if __name__ == "__main__":
    files_to_check = [
        "workers.py",
        "launcher.py"
    ]
    
    all_passed = True
    print("--- Başlıyor: Doğrulama Scripti ---")
    for file in files_to_check:
        full_path = os.path.join(os.path.dirname(__file__), file)
        if not verify_syntax(full_path):
            all_passed = False
            
    if all_passed:
        print("✅ [test-engineer] Bütün doğrulama testleri başarıyla geçti.")
        sys.exit(0)
    else:
        print("❌ [test-engineer] Doğrulama BAŞARISIZ.")
        sys.exit(1)
