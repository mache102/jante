import nltk
from nltk.stem import WordNetLemmatizer

nltk.download('wordnet')  
nltk.download('omw-1.4')
lemmatizer = WordNetLemmatizer()
  
print(lemmatizer.lemmatize("shouldn't"))