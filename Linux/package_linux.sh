#!/bin/bash

DIST_DIR="dist/klyve.dist"

# --- SAFETY CHECK: Ensure Binary Exists ---
if [ ! -f "$DIST_DIR/klyve.bin" ]; then
    echo "❌ CRITICAL ERROR: Binary '$DIST_DIR/klyve.bin' not found!"
    echo "   You must run 'python3 build_release_linux.py' BEFORE running this packaging script."
    exit 1
fi
echo "✅ Found binary: $DIST_DIR/klyve.bin"

echo "--- Preparing AppImage Structure ---"

# 1. Download AppImageTool
if [ ! -f "appimagetool-x86_64.AppImage" ]; then
    echo "Downloading AppImageTool..."
    wget https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x appimagetool-x86_64.AppImage
fi

# 2. Bundle XCB Dependencies (Expanded List)
echo "Bundling Extended XCB dependency suite to /lib..."
mkdir -p $DIST_DIR/lib

# Expanded list including core dependencies of xcb-cursor
# Expanded list including core dependencies of xcb-cursor AND xkbcommon
# Expanded list including core dependencies of xcb-cursor AND xkbcommon
LIBS=(
    "libxcb-cursor.so.0"
    "libxcb-image.so.0"
    "libxcb-keysyms.so.1"
    "libxcb-render-util.so.0"
    "libxcb-icccm.so.4"
    "libxcb-util.so.1"
    "libxcb-xinerama.so.0"
    "libxcb-randr.so.0"
    "libxcb-shape.so.0"
    "libxcb-xfixes.so.0"
    "libxcb-render.so.0"
    "libxcb-shm.so.0"
    "libxcb-sync.so.1"
    "libxcb-xkb.so.1"
    "libxkbcommon-x11.so.0"
    "libxkbcommon.so.0"
)

SEARCH_ROOT="/usr/lib"

for LIB in "${LIBS[@]}"; do
    FOUND_PATH=$(find "$SEARCH_ROOT" -name "$LIB" -print -quit 2>/dev/null)
    if [ -n "$FOUND_PATH" ]; then
        cp -L "$FOUND_PATH" "$DIST_DIR/lib/"
        echo "   ✅ Bundled: $LIB"
    else
        echo "   ⚠️ Optional lib not found (skipping): $LIB"
    fi
done

# 3. Create the AppRun entry point (Diagnostic Mode)
echo "Creating AppRun..."
cat > $DIST_DIR/AppRun <<EOF
#!/bin/bash

# --- FIX: Force UI Scaling ---
export QT_AUTO_SCREEN_SCALE_FACTOR=0
export QT_SCALE_FACTOR=1.25

# --- FIX: Force X11 Backend ---
export QT_QPA_PLATFORM=xcb

# --- DIAGNOSTIC: Enable Plugin Debugging ---
# This will print the EXACT reason why the plugin fails to load
# export QT_DEBUG_PLUGINS=1

SELF=\$(readlink -f "\$0")
HERE=\${SELF%/*}

# --- LIBRARY CONFIGURATION ---
# 1. Bundled Libs, 2. Qt Libs, 3. System Libs
export LD_LIBRARY_PATH="\${HERE}/lib:\${HERE}/PySide6:\${HERE}/shiboken6:\${LD_LIBRARY_PATH}"
export QT_PLUGIN_PATH="\${HERE}/PySide6/plugins"
export PATH="\${HERE}:\${PATH}"

echo "Starting Klyve..."
exec "\${HERE}/klyve.bin" "\$@"
EOF

# --- Finalize Permissions & Formatting ---
sed -i 's/\r$//' $DIST_DIR/AppRun
chmod +x $DIST_DIR/AppRun
chmod +x $DIST_DIR/klyve.bin
chmod -R +x $DIST_DIR/lib/*.so* 2>/dev/null

# 4. Create .desktop file
cat > $DIST_DIR/klyve.desktop <<EOF
[Desktop Entry]
Name=Klyve
Exec=AppRun
Icon=klyve_logo
Type=Application
Categories=Development;
EOF

# 5. Icon Processing
echo "Processing Icon..."
ICON_SRC="$DIST_DIR/gui/icons/klyve_logo.ico"
ICON_DST="$DIST_DIR/klyve_logo.png"

if [ -f "$ICON_SRC" ]; then
    convert "$ICON_SRC" "$DIST_DIR/temp_icon.png" 2>/dev/null
    BEST_ICON=$(ls -S $DIST_DIR/temp_icon-*.png 2>/dev/null | head -n 1)

    if [ -n "$BEST_ICON" ]; then
        mv "$BEST_ICON" "$ICON_DST"
        rm $DIST_DIR/temp_icon-*.png 2>/dev/null
        echo "✅ Created high-res icon"
    else
        echo "⚠️ Icon conversion failed. Using generic."
    fi
fi

# 6. Copy Legal Documents
cp "Third_Party_Notices.txt" "$DIST_DIR/" 2>/dev/null
cp "Privacy_Policy.txt" "$DIST_DIR/" 2>/dev/null
cp "EULA.txt" "$DIST_DIR/" 2>/dev/null

# 7. Build the AppImage
echo "--- Building AppImage ---"
export ARCH=x86_64
./appimagetool-x86_64.AppImage --appimage-extract-and-run $DIST_DIR

if [ $? -eq 0 ]; then
    echo "✅ Packaging Complete."
else
    echo "❌ Packaging Failed."
    exit 1
fi