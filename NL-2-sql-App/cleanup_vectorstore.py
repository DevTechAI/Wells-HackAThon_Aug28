import os
import shutil

# Remove the vectorstore directory and all its contents
vectorstore_path = "vectorstore"

print(f"🔍 Attempting to remove {vectorstore_path} directory...")

if os.path.exists(vectorstore_path):
    try:
        # Force remove the directory and all contents
        shutil.rmtree(vectorstore_path, ignore_errors=True)
        print(f"✅ Successfully removed {vectorstore_path} directory")
    except Exception as e:
        print(f"❌ Error removing {vectorstore_path}: {e}")
else:
    print(f"ℹ️ {vectorstore_path} directory does not exist")

print("✅ Cleanup script completed")
