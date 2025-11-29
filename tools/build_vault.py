import json
import os
import random
import sys
from pathlib import Path

# Add project root to sys.path to allow importing config
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    import config
except ImportError:
    print("Error: Could not import config.py. Ensure you are running this from the project tools directory.")
    sys.exit(1)

def generate_xor_key(length=64):
    """Generates a random byte key for XOR encryption."""
    return [random.randint(0, 255) for _ in range(length)]

def xor_encrypt(text, key):
    """Encrypts string text into a byte array using the key."""
    if not isinstance(text, bytes):
        text = text.encode('utf-8')

    encrypted = []
    for i, byte in enumerate(text):
        k = key[i % len(key)]
        encrypted.append(byte ^ k)
    return encrypted

def c_byte_array(name, bytes_data):
    """Formats a Python list of bytes into a C array string."""
    hex_bytes = ", ".join([f"0x{b:02X}" for b in bytes_data])
    return f"static const unsigned char {name}[] = {{ {hex_bytes}, 0x00 }};"

def generate_vault_c(manifest_path, output_path):
    print(f"Reading manifest from: {manifest_path}")
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    # 1. Get the DB Key from existing config
    raw_db_key = config.get_db_key()
    print(f"Securing DB Key (len={len(raw_db_key)})...")

    # 2. Generate the Session Master Key
    master_key = generate_xor_key(128)
    master_key_array = c_byte_array("MASTER_KEY", master_key)

    # 3. Encrypt DB Key
    enc_db_key = xor_encrypt(raw_db_key, master_key)
    db_key_array = c_byte_array("ENC_DB_KEY", enc_db_key)

    # 4. Process all Prompts
    prompt_arrays = []
    registry_entries = []

    print(f"Processing {len(manifest)} prompts from manifest...")

    sorted_keys = sorted(manifest.keys())

    for vault_key in sorted_keys:
        entry = manifest[vault_key]
        txt_filename = entry['filename']
        txt_path = manifest_path.parent / "prompts" / txt_filename

        if not txt_path.exists():
            print(f"WARNING: Prompt file missing: {txt_path}")
            continue

        raw_prompt = txt_path.read_text(encoding='utf-8')

        # Create safe C variable name (replace non-alphanumeric)
        c_var_name = "PROMPT_" + vault_key.replace(".", "_").replace("__", "_").upper()

        # Encrypt
        enc_bytes = xor_encrypt(raw_prompt, master_key)

        # Add C array definition
        prompt_arrays.append(c_byte_array(c_var_name, enc_bytes))

        # Add to registry table
        # Structure: { "key_string", POINTER_TO_DATA, DATA_LENGTH }
        registry_entries.append(f'    {{ "{vault_key}", {c_var_name}, {len(enc_bytes)} }}')

    # --- FIX: Correctly join entries with comma + newline ---
    registry_content = ",\n".join(registry_entries)

    # 5. Construct the C File Content
    c_source = f"""
#include <Python.h>
#include <string.h>

// --- 1. THE MASTER GATE KEY (Randomly Generated for this Build) ---
{master_key_array}
static const int MASTER_KEY_LEN = {len(master_key)};

// --- 2. ENCRYPTED ASSETS ---
{db_key_array}
static const int DB_KEY_LEN = {len(enc_db_key)};

// Prompts
{chr(10).join(prompt_arrays)}

// --- 3. REGISTRY STRUCTURE ---
typedef struct {{
    const char* key;
    const unsigned char* data;
    int length;
}} VaultEntry;

static VaultEntry prompt_registry[] = {{
{registry_content}
}};

static const int REGISTRY_SIZE = {len(registry_entries)};

// --- 4. DECRYPTION LOGIC (In-Memory Only) ---
static PyObject* decrypt_data(const unsigned char* encrypted, int len) {{
    char* buffer = (char*)malloc(len + 1);
    if (!buffer) return PyErr_NoMemory();

    for (int i = 0; i < len; i++) {{
        buffer[i] = encrypted[i] ^ MASTER_KEY[i % MASTER_KEY_LEN];
    }}
    buffer[len] = '\\0'; // Null terminate

    PyObject* result = PyUnicode_FromString(buffer);

    // CRITICAL SECURITY: Zero out the buffer immediately
    memset(buffer, 0, len);
    free(buffer);

    return result;
}}

// --- 5. PYTHON API EXPORTS ---

static PyObject* get_db_key(PyObject* self, PyObject* args) {{
    return decrypt_data(ENC_DB_KEY, DB_KEY_LEN);
}}

static PyObject* get_prompt(PyObject* self, PyObject* args) {{
    const char* key_string;
    if (!PyArg_ParseTuple(args, "s", &key_string)) {{
        return NULL;
    }}

    for (int i = 0; i < REGISTRY_SIZE; i++) {{
        if (strcmp(prompt_registry[i].key, key_string) == 0) {{
            return decrypt_data(prompt_registry[i].data, prompt_registry[i].length);
        }}
    }}

    Py_RETURN_NONE;
}}

// Module Definition
static PyMethodDef VaultMethods[] = {{
    {{"get_db_key", get_db_key, METH_NOARGS, "Get the database encryption key."}},
    {{"get_prompt", get_prompt, METH_VARARGS, "Get a decrypted system prompt by ID."}},
    {{NULL, NULL, 0, NULL}}
}};

static struct PyModuleDef vaultmodule = {{
    PyModuleDef_HEAD_INIT,
    "vault",
    "Secure storage for Klyve assets.",
    -1,
    VaultMethods
}};

PyMODINIT_FUNC PyInit_vault(void) {{
    return PyModule_Create(&vaultmodule);
}}
"""

    print(f"Writing C source to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(c_source)
    print("Vault generation complete.")

if __name__ == "__main__":
    manifest_file = project_root / "data" / "prompts_manifest.json"
    output_file = project_root / "vault.c"

    if manifest_file.exists():
        generate_vault_c(manifest_file, output_file)
    else:
        print("Manifest not found. Run extract_prompts.py first.")