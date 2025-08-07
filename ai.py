import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet, stopwords
from nltk.tokenize import word_tokenize
import tensorflow as tf
from transformers import RobertaTokenizer, TFRobertaForSequenceClassification
import networkx as nx
import numpy as np

# nltk.download('punkt')
# nltk.download('stopwords')
# nltk.download('averaged_perceptron_tagger')
# nltk.download('wordnet')

def issue_tag(description):
    def lemmatize_word(word, pos):
        lemmatizer = WordNetLemmatizer()
        return lemmatizer.lemmatize(word, pos=pos)

    def segregate_words(text):
        tokens = nltk.word_tokenize(text)
        tags = nltk.pos_tag(tokens)
        nouns = []
        for token, tag in tags:
            if tag.startswith('NN'):
                token = lemmatize_word(token, wordnet.NOUN)
                nouns.append(token)
        return nouns

    def remove_auxiliary_stopwords(sentence):
        words = word_tokenize(sentence)
        stop_words = set(stopwords.words('english'))
        auxiliary_verbs = ['am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                           'have', 'has', 'had', 'do', 'does', 'did', 'shall', 'will',
                           'should', 'would', 'may', 'might', 'must', 'can', 'could']
        filtered_words = [word for word in words if word.lower() not in auxiliary_verbs and word.lower() not in stop_words]
        return ' '.join(filtered_words)

    def predict_class(sentence, tokenizer, model, classes, threshold=0.3):
        inputs = tokenizer(sentence, return_tensors="tf", truncation=True, padding=True)
        outputs = model(inputs)
        probs = tf.nn.softmax(outputs.logits, axis=1).numpy()[0]
        max_index = np.argmax(probs)
        if probs[max_index] >= threshold:
            return classes[max_index]
        return None

    tokenizer = RobertaTokenizer.from_pretrained('roberta-base')
    model = TFRobertaForSequenceClassification.from_pretrained(r"D:\Ishaan\Bin Arena\Fixter\sentence_classification_model_v2")

    classes = [
        "hygiene_cleanliness", "safety_security", "maintenance_upkeep",
        "facilities_amenities", "internet_connectivity", "plumbing",
        "bathroom_supplies", "bathroom_hardware", "electrical",
        "lighting", "furniture"
    ]

    filt = remove_auxiliary_stopwords(description)
    segregation = segregate_words(filt)
    tags = list(set(
        prediction for word in segregation
        if (prediction := predict_class(word, tokenizer, model, classes))
    ))
    return tags

def build_consequence_graph():
    G = nx.DiGraph()
    edges = [
        ("plumbing", "bathroom_supplies"),
        ("plumbing", "maintenance_upkeep"),
        ("plumbing", "hygiene_cleanliness"),
        ("bathroom_hardware", "maintenance_upkeep"),
        ("bathroom_supplies", "hygiene_cleanliness"),
        ("electrical", "lighting"),
        ("electrical", "safety_security"),
        ("lighting", "safety_security"),
        ("lighting", "facilities_amenities"),
        ("hygiene_cleanliness", "safety_security"),
        ("hygiene_cleanliness", "facilities_amenities"),
        ("internet_connectivity", "facilities_amenities"),
        ("internet_connectivity", "maintenance_upkeep"),
        ("maintenance_upkeep", "safety_security"),
        ("maintenance_upkeep", "facilities_amenities"),
        ("furniture", "facilities_amenities"),
        ("furniture", "safety_security")
    ]
    for src, dst in edges:
        G.add_edge(src, dst)
    return G

def compute_priority(tags):
    keyword_weights = {
        "hygiene_cleanliness": 4,
        "safety_security": 5,
        "maintenance_upkeep": 3,
        "facilities_amenities": 1,
        "internet_connectivity": 2,
        "plumbing": 4,
        "bathroom_supplies": 3,
        "bathroom_hardware": 3,
        "electrical": 5,
        "lighting": 2,
        "furniture": 0
    }

    G = build_consequence_graph()
    score = 0
    visited = set()

    for tag in tags:
        if tag not in keyword_weights:
            continue
        stack = [(tag, 1.0)]
        while stack:
            node, decay = stack.pop()
            if (node, decay) in visited:
                continue
            visited.add((node, decay))
            score += keyword_weights.get(node, 0) * decay
            for neighbor in G.successors(node):
                stack.append((neighbor, decay * 0.4))  

    return score / len(tags) if tags else 0


