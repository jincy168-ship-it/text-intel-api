"""Pre-download NLTK data. Run once during build."""
import nltk
for resource in ["punkt", "punkt_tab", "stopwords", "averaged_perceptron_tagger"]:
    nltk.download(resource, quiet=True)
print("NLTK data ready.")
