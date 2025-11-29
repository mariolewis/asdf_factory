from setuptools import setup, Extension
import sys

# Determine suffix based on platform
# Windows: .pyd, Linux: .so
module_name = "vault"

vault_module = Extension(
    module_name,
    sources=['vault.c'],
    language='c',
    # Optional: Add compile args if needed for specific compilers
    # extra_compile_args=["/O2"] if sys.platform == "win32" else ["-O3"]
)

setup(
    name=module_name,
    version='1.0',
    description='Secure storage for Klyve assets',
    ext_modules=[vault_module],
)