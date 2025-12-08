import os
import sys

try:
    import cairosvg
except (OSError, ImportError):
    print("Error: CairoSVG not found.")
    sys.exit(1)

def create_high_res_splash():
    input_filename = "klyve_logo_integrated.svg"
    output_filename = "splash.png"

    # We generate a LARGE image (1280px).
    # Your App code (Step 1) will shrink this down to 640px.
    # This "Oversampling" is the secret to sharp graphics.
    target_width = 1280

    current_folder = os.getcwd()
    input_path = os.path.join(current_folder, input_filename)
    output_path = os.path.join(current_folder, output_filename)

    if not os.path.exists(input_path):
        print(f"Error: Could not find '{input_filename}'")
        return

    print(f"Converting SVG to High-Res PNG ({target_width}px)...")

    try:
        cairosvg.svg2png(
            url=input_path,
            write_to=output_path,
            output_width=target_width
        )
        print(f"Success! Created {output_filename}")
        print("Now run your application to see the sharp, correctly sized splash.")

    except Exception as e:
        print(f"Conversion Failed: {e}")

if __name__ == "__main__":
    create_high_res_splash()