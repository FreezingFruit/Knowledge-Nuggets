from video_analyzer import VideoContentAnalyzer
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

class YouTubeAnalyzer:
    def __init__(self):
        self.content_analyzer = VideoContentAnalyzer()

    def get_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL."""
        if 'youtube.com' in url or 'youtu.be' in url:
            if 'youtu.be' in url:
                return url.split('/')[-1]
            else:
                parsed_url = urlparse(url)
                return parse_qs(parsed_url.query)['v'][0]
        else:
            raise ValueError("Invalid YouTube URL")

    def get_transcript(self, url: str) -> str:
        """Get transcript from YouTube video."""
        try:
            video_id = self.get_video_id(url)
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            return ' '.join([entry['text'] for entry in transcript_list])
        except Exception as e:
            raise Exception(f"Error getting transcript: {str(e)}")

    def analyze_video(self, url: str, 
                     num_summary_sentences: int = 3,
                     num_keywords: int = 10,
                     num_topics: int = 3) -> dict:
        """
        Analyze a YouTube video and return summary, keywords, and topics.
        
        Args:
            url: YouTube video URL
            num_summary_sentences: Number of sentences in summary
            num_keywords: Number of keywords to extract
            num_topics: Number of topics to identify
        
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Get transcript
            transcript = self.get_transcript(url)
            
            # Analyze content
            results = self.content_analyzer.analyze_content(
                text=transcript,
                num_summary_sentences=num_summary_sentences,
                num_keywords=num_keywords,
                num_topics=num_topics
            )
            
            return results
            
        except Exception as e:
            raise Exception(f"Analysis failed: {str(e)}")


def main():
    # Example usage
    analyzer = YouTubeAnalyzer()
    
    # Replace with your YouTube video URL
    video_url = "https://www.youtube.com/watch?v=gI2WezmpGIo"
    
    try:
        print("Analyzing video...")
        results = analyzer.analyze_video(
            url=video_url,
            num_summary_sentences=3,
            num_keywords=5,
            num_topics=2
        )
        
        print("\nSummary:")
        print(results['summary'])
        
        print("\nKeywords:")
        for keyword, score in results['keywords']:
            print(f"- {keyword}: {score:.4f}")
        
        print("\nTopics:")
        for i, topic in enumerate(results['topics'], 1):
            print(f"Topic {i}: {', '.join(topic)}")
            
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()