from video_analyzer import VideoContentAnalyzer

def test_analyzer():
    # EXMAPLEEEEEEEEEEEE*
    transcript = """
    This is a test video about machine learning.
    We'll cover neural networks and deep learning.
    The applications of AI in healthcare are revolutionary.
    Data science is transforming how we analyze information.
    """

    analyzer = VideoContentAnalyzer()
    

    results = analyzer.analyze_content(
        text=transcript,
        num_summary_sentences=2,
        num_keywords=5,
        num_topics=2,
        words_per_topic=3
    )
    
    # RESULTS
    print("Summary:")
    print(results['summary'])
    print("\nKeywords:")
    for keyword, score in results['keywords']:
        print(f"- {keyword}: {score:.4f}")
    print("\nTopics:")
    for i, topic in enumerate(results['topics'], 1):
        print(f"Topic {i}: {', '.join(topic)}")

if __name__ == "__main__":
    test_analyzer()