import os

os.makedirs('air', exist_ok=True)
import shutil
for file in os.listdir():
    if file.endswith('.txt') or file.endswith('.wav'):
        if os.path.exists('air/' + file):
            os.remove('air/' + file)
        shutil.move(file, 'air')