import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.cluster.util import cosine_distance
from nltk.probability import FreqDist
from nltk.tag import pos_tag
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import numpy as np
import networkx as nx
from typing import List, Optional, Dict, Tuple
import pandas as pd

class VideoContentAnalyzer:
    def __init__(self):
        required_resources = [
            ('punkt', 'tokenizers/punkt'),
            ('stopwords', 'corpora/stopwords'),
            ('averaged_perceptron_tagger', 'taggers/averaged_perceptron_tagger'),
            ('words', 'corpora/words')
        ]
        
        for resource, path in required_resources:
            try:
                nltk.data.find(path)
            except LookupError:
                print(f"Downloading {resource}...")
                nltk.download(resource, quiet=True)
        
        self.stop_words = set(stopwords.words('english'))
    
    def clean_text(self, text: str) -> str:
        """Remove special characters and convert to lowercase."""
        return ' '.join([word.lower() for word in word_tokenize(text)
                        if word.isalnum()])
    
    def create_sentence_vectors(self, sentences: List[str]) -> List[List[float]]:
        """Create vectors for each sentence based on word frequencies."""
        word_freq = {}
        
        for sentence in sentences:
            words = word_tokenize(self.clean_text(sentence))
            for word in words:
                if word not in self.stop_words:
                    word_freq[word] = word_freq.get(word, 0) + 1
        
        sentence_vectors = []
        for sentence in sentences:
            vector = []
            words = word_tokenize(self.clean_text(sentence))
            for word in word_freq.keys():
                if word in words:
                    vector.append(word_freq[word])
                else:
                    vector.append(0)
            sentence_vectors.append(vector)
        
        return sentence_vectors
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """
        Extract important keywords from the text using TF-IDF scores.
        
        Args:
            text: Input text
            top_n: Number of keywords to extract
            
        Returns:
            List of tuples containing (keyword, importance_score)
        """
        words = word_tokenize(text.lower())
        words = [word for word in words if word.isalnum() and word not in self.stop_words]
        
        tagged_words = pos_tag(words)
        
        important_words = [word for word, tag in tagged_words 
                         if tag.startswith(('NN', 'VB', 'JJ'))]
        
        freq_dist = FreqDist(important_words)
        
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([' '.join(important_words)])
        
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]
        
        keyword_scores = [(feature_names[i], scores[i]) 
                         for i in range(len(feature_names))]
        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        
        return keyword_scores[:top_n]
    
    def identify_topics(self, text: str, num_topics: int = 3, num_words: int = 5) -> List[List[str]]:
        """
        Identify main topics in the text using Latent Dirichlet Allocation.
        
        Args:
            text: Input text
            num_topics: Number of topics to identify
            num_words: Number of words per topic
            
        Returns:
            List of topics, where each topic is a list of representative words
        """
        sentences = sent_tokenize(text)
        
        vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        tfidf_matrix = vectorizer.fit_transform(sentences)
        
        lda = LatentDirichletAllocation(n_components=num_topics, random_state=42)
        lda.fit(tfidf_matrix)
        
        feature_names = vectorizer.get_feature_names_out()
        
        topics = []
        for topic_idx, topic in enumerate(lda.components_):
            top_words = [feature_names[i] 
                        for i in topic.argsort()[:-num_words-1:-1]]
            topics.append(top_words)
        
        return topics
    
    def generate_summary(self, text: str, num_sentences: Optional[int] = None) -> str:
        """Generate a summary of the given text."""
        sentences = sent_tokenize(text)
        
        if not num_sentences:
            num_sentences = max(3, len(sentences) // 3)
        
        num_sentences = min(num_sentences, len(sentences))
        
        similarity_matrix = np.zeros((len(sentences), len(sentences)))
        sentence_vectors = self.create_sentence_vectors(sentences)
        
        for i in range(len(sentences)):
            for j in range(len(sentences)):
                if i != j:
                    similarity_matrix[i][j] = 1 - cosine_distance(
                        sentence_vectors[i],
                        sentence_vectors[j]
                    )
    
        nx_graph = nx.from_numpy_array(similarity_matrix)
        scores = nx.pagerank(nx_graph)
        
        ranked_sentences = sorted(
            [(scores[i], sentence) for i, sentence in enumerate(sentences)],
            reverse=True
        )
        
        summary_sentences = sorted(
            [(i, sentence) for i, (score, sentence) in enumerate(ranked_sentences[:num_sentences])],
            key=lambda x: x[0]
        )
        
        return ' '.join([sentence for _, sentence in summary_sentences])
    
    def analyze_content(self, text: str, 
                       num_summary_sentences: Optional[int] = None,
                       num_keywords: int = 10,
                       num_topics: int = 3,
                       words_per_topic: int = 5) -> Dict:
        """
        Perform complete content analysis including summary, keywords, and topics.
        
        Args:
            text: Input text to analyze
            num_summary_sentences: Number of sentences in summary
            num_keywords: Number of keywords to extract
            num_topics: Number of topics to identify
            words_per_topic: Number of words per topic
            
        Returns:
            Dictionary containing summary, keywords, and topics
        """
        return {
            'summary': self.generate_summary(text, num_summary_sentences),
            'keywords': self.extract_keywords(text, num_keywords),
            'topics': self.identify_topics(text, num_topics, words_per_topic)
        }

def main():
    transcript = """
    In this comprehensive video, we'll explore the fascinating world of artificial intelligence and its applications.
    AI has revolutionized many industries, from healthcare to transportation and manufacturing.
    Machine learning, a subset of AI, enables computers to learn patterns from vast amounts of data.
    Deep learning, inspired by the human brain's neural networks, has achieved remarkable results in image and speech recognition.
    Neural networks can recognize complex patterns in data that humans might miss.
    The future of AI holds great promise for solving complex problems in science and medicine.
    However, we must also consider the ethical implications of AI development and deployment.
    Responsible AI development ensures benefits for all of humanity while minimizing potential risks.
    Recent advances in natural language processing have enabled AI to understand and generate human-like text.
    The integration of AI with robotics is transforming automation in manufacturing and logistics.
    """
    
    analyzer = VideoContentAnalyzer()
    results = analyzer.analyze_content(transcript)
    
    print("\nOriginal text:")
    print(transcript)
    
    print("\nSummary:")
    print(results['summary'])
    
    print("\nKeywords:")
    for keyword, score in results['keywords']:
        print(f"- {keyword}: {score:.4f}")
    
    print("\nTopics:")
    for i, topic in enumerate(results['topics'], 1):
        print(f"Topic {i}: {', '.join(topic)}")

if __name__ == "__main__":
    main()