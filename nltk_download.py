import nltk
import os
# Run only once to download NLTK data

nltk_data_dir = 'nltk_data'
if not os.path.exists(nltk_data_dir):
    os.mkdir(nltk_data_dir)

packages = ['words', 'punkt', 'averaged_perceptron_tagger', 'wordnet', 'omw-1.4']

for package in packages:
    nltk.download(package, download_dir=nltk_data_dir)