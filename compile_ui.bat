@echo off
setlocal enabledelayedexpansion
echo Recompiling all .ui files...
for %%f in (gui\*.ui) do (
    set "py_file=gui\ui_%%~nf.py"
    echo Compiling %%f to !py_file!
    pyside6-uic "%%f" -o "!py_file!"
)
echo.
echo All UI files have been recompiled.