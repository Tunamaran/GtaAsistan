import config
import ctypes

def test_scaling():
    print("Testing Dynamic Scaling...")
    
    # Force detection
    w, h = config.get_screen_resolution()
    print(f"Detected Resolution: {w}x{h}")
    
    defaults = config.get_scaled_default_config()
    print("\nScaled Config:")
    print(f"OCR Region: {defaults['ocr_region']}")
    print(f"HUD Region: {defaults['hud_region']}")
    
    base_w, base_h = config.BASELINE_RESOLUTION
    print(f"\nBaseline: {base_w}x{base_h}")
    print(f"Scale X: {w/base_w:.2f}, Scale Y: {h/base_h:.2f}")

if __name__ == "__main__":
    test_scaling()
