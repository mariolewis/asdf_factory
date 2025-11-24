import os

def pack_resources():
    # files to read
    files = {
        "EULA_TEXT": "EULA.txt",
        "PRIVACY_POLICY_TEXT": "Privacy_Policy.txt",
        "THIRD_PARTY_NOTICES_TEXT": "Third_Party_Notices.txt"
    }

    output_content = [
        "# resources.py",
        "# This file is auto-generated. Do not edit manually.",
        "# It contains the legal text resources for the Klyve application.",
        ""
    ]

    print("Packing legal documents into resources.py...")

    for var_name, filename in files.items():
        if not os.path.exists(filename):
            print(f"[ERROR] Could not find {filename}. Make sure it is in this folder.")
            return

        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()

        # Escape triple quotes to prevent syntax errors in the generated Python code
        safe_content = content.replace('"""', '\\"\\"\\"')

        output_content.append(f'{var_name} = """{safe_content}"""')
        output_content.append("")

    with open("resources.py", "w", encoding="utf-8") as f:
        f.write("\n".join(output_content))

    print("[SUCCESS] Created resources.py. You may now delete this script and the original .txt files if desired.")

if __name__ == "__main__":
    pack_resources()