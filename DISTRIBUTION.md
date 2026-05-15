# 📦 Distribution Guide: Building the .exe

Follow these steps to convert the Python code into a single, installable `.exe` file that you can share on GitHub or send to anyone.

## 1. Prerequisites
You need to have Python installed and the project dependencies ready.
```bash
pip install -r requirements.txt
pip install pyinstaller
```

## 2. Build the Executable
Run this command in your terminal from the project root:

```bash
pyinstaller --noconsole --onefile --name "AutoContent_Ultimate" app.py
```

### Command Breakdown:
*   `--noconsole`: Prevents a black terminal window from appearing when you open the app.
*   `--onefile`: Bundles everything into a single `.exe` file (easier to share).
*   `--name`: Sets the name of the final file.

## 3. Where is my file?
Once the process finishes:
1. Open the `dist/` folder.
2. You will find `AutoContent_Ultimate.exe` inside.
3. **That's it!** You can now send this file to anyone. They do **not** need to have Python installed to run it.

---

## 🚀 Pro Tip: Adding a Custom Icon
If you have an `.ico` file (e.g., `icon.ico`), you can build with an icon like this:

```bash
pyinstaller --noconsole --onefile --icon="icon.ico" --name "AutoContent_Ultimate" app.py
```

## 🐙 Sharing on GitHub
1. Go to your GitHub repository.
2. Click on **Releases** -> **Create a new release**.
3. Upload the `AutoContent_Ultimate.exe` from the `dist/` folder as a binary asset.
4. Users can now download and run it directly!
