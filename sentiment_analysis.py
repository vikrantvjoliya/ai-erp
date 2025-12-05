"""
Pain Point & Sentiment Analysis Module for ERP Modernization Health Check.
Uses NLP for sentiment analysis and pain point identification.
"""
from typing import List, Dict, Optional, Tuple
from collections import Counter, defaultdict
import numpy as np
import pandas as pd
from loguru import logger

from langchain.schema import Document
from textblob import TextBlob

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available. Using TextBlob fallback.")


class SentimentAnalyzer:
    """Sentiment analysis engine for pain point detection."""
    
    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english", use_transformers: bool = True):
        """
        Initialize sentiment analyzer.
        
        Args:
            model_name: HuggingFace model for sentiment analysis
            use_transformers: Whether to use transformers (falls back to TextBlob)
        """
        self.use_transformers = use_transformers and TRANSFORMERS_AVAILABLE
        
        if self.use_transformers:
            try:
                logger.info(f"Loading sentiment model: {model_name}")
                self.sentiment_pipeline = pipeline(
                    "sentiment-analysis",
                    model=model_name,
                    device=-1  # CPU
                )
                logger.info("Sentiment model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load transformers model: {e}. Falling back to TextBlob.")
                self.use_transformers = False
        
        self.pain_points = []
        self.sentiment_scores = []
    
    def analyze_documents(self, documents: List[Document]) -> Dict:
        """
        Analyze sentiment across all documents and identify pain points.
        
        Args:
            documents: Documents to analyze
            
        Returns:
            Analysis results with sentiment scores and pain points
        """
        logger.info(f"Analyzing sentiment for {len(documents)} documents")
        
        # Filter for pain point and feedback documents
        relevant_docs = [
            doc for doc in documents
            if doc.metadata.get("category") in ["pain_points", "audits", "erp_exports"]
        ]
        
        if not relevant_docs:
            logger.warning("No relevant documents found for sentiment analysis")
            return self._empty_results()
        
        results = {
            "overall_sentiment": {},
            "pain_points": [],
            "sentiment_by_category": {},
            "sentiment_trend": [],
            "top_issues": [],
            "heatmap_data": []
        }
        
        # Analyze each document
        all_sentiments = []
        category_sentiments = defaultdict(list)
        
        for doc in relevant_docs:
            sentiment_data = self._analyze_document(doc)
            
            if sentiment_data:
                all_sentiments.append(sentiment_data)
                category = doc.metadata.get("category", "unknown")
                category_sentiments[category].append(sentiment_data["score"])
                
                # Extract pain points from negative sentiment
                if sentiment_data["score"] < 0:
                    pain_point = self._extract_pain_point(doc, sentiment_data)
                    if pain_point:
                        self.pain_points.append(pain_point)
        
        # Aggregate results
        if all_sentiments:
            results["overall_sentiment"] = self._calculate_overall_sentiment(all_sentiments)
            results["sentiment_by_category"] = self._aggregate_by_category(category_sentiments)
            results["pain_points"] = self._rank_pain_points(self.pain_points)
            results["top_issues"] = self._extract_top_issues(self.pain_points)
            results["heatmap_data"] = self._generate_heatmap_data(self.pain_points)
        
        logger.info(f"Sentiment analysis complete. Found {len(results['pain_points'])} pain points")
        
        return results
    
    def _analyze_document(self, document: Document) -> Optional[Dict]:
        """Analyze sentiment of a single document."""
        content = document.page_content
        
        if not content or len(content.strip()) < 10:
            return None
        
        # Split into chunks for better analysis
        chunks = self._split_into_sentences(content)
        
        if not chunks:
            return None
        
        # Analyze sentiment for each chunk
        chunk_sentiments = []
        
        for chunk in chunks[:50]:  # Limit to first 50 sentences
            if len(chunk.strip()) > 10:
                sentiment = self._analyze_text(chunk)
                if sentiment:
                    chunk_sentiments.append(sentiment)
        
        if not chunk_sentiments:
            return None
        
        # Aggregate chunk sentiments
        avg_score = np.mean([s["score"] for s in chunk_sentiments])
        
        return {
            "score": avg_score,
            "label": self._score_to_label(avg_score),
            "confidence": np.mean([s.get("confidence", 0.5) for s in chunk_sentiments]),
            "chunks": len(chunk_sentiments)
        }
    
    def _analyze_text(self, text: str) -> Optional[Dict]:
        """Analyze sentiment of a text chunk."""
        if self.use_transformers:
            try:
                result = self.sentiment_pipeline(text[:512])[0]  # Limit to model max length
                
                # Convert to unified format
                score = result["score"] if result["label"] == "POSITIVE" else -result["score"]
                
                return {
                    "score": score,
                    "confidence": result["score"],
                    "label": result["label"]
                }
            except Exception as e:
                logger.error(f"Transformers sentiment analysis failed: {e}")
                # Fallback to TextBlob
                return self._analyze_with_textblob(text)
        else:
            return self._analyze_with_textblob(text)
    
    def _analyze_with_textblob(self, text: str) -> Dict:
        """Fallback sentiment analysis using TextBlob."""
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # Range: -1 to 1
        
        return {
            "score": polarity,
            "confidence": abs(polarity),  # Use absolute value as confidence
            "label": "POSITIVE" if polarity > 0 else "NEGATIVE" if polarity < 0 else "NEUTRAL"
        }
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        import re
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _score_to_label(self, score: float) -> str:
        """Convert sentiment score to label."""
        if score > 0.3:
            return "POSITIVE"
        elif score < -0.3:
            return "NEGATIVE"
        else:
            return "NEUTRAL"
    
    def _extract_pain_point(self, document: Document, sentiment_data: Dict) -> Optional[Dict]:
        """Extract pain point from document with negative sentiment."""
        content = document.page_content
        
        # Look for key pain point indicators
        pain_indicators = [
            "problem", "issue", "error", "fail", "slow", "difficult",
            "unable", "cannot", "frustrat", "delay", "bug", "crash",
            "timeout", "inefficient", "complex", "confus", "complaint"
        ]
        
        content_lower = content.lower()
        
        # Check if document contains pain indicators
        matching_indicators = [
            indicator for indicator in pain_indicators
            if indicator in content_lower
        ]
        
        if not matching_indicators:
            return None
        
        # Extract key phrases around pain indicators
        key_phrases = self._extract_key_phrases(content, pain_indicators)
        
        # Categorize pain point
        category = self._categorize_pain_point(content_lower)
        
        return {
            "source": document.metadata.get("source", "unknown"),
            "sentiment_score": sentiment_data["score"],
            "category": category,
            "indicators": matching_indicators,
            "key_phrases": key_phrases[:5],  # Top 5 phrases
            "severity": self._calculate_severity(sentiment_data["score"], len(matching_indicators)),
            "excerpt": content[:300]  # First 300 chars for context
        }
    
    def _extract_key_phrases(self, text: str, indicators: List[str]) -> List[str]:
        """Extract key phrases around pain indicators."""
        sentences = self._split_into_sentences(text)
        key_phrases = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(indicator in sentence_lower for indicator in indicators):
                # Clean and limit length
                phrase = sentence.strip()[:200]
                if phrase:
                    key_phrases.append(phrase)
        
        return key_phrases
    
    def _categorize_pain_point(self, content: str) -> str:
        """Categorize pain point by type."""
        categories = {
            "performance": ["slow", "performance", "latency", "timeout", "delay", "hang"],
            "usability": ["difficult", "complex", "confusing", "hard to", "unclear"],
            "functionality": ["error", "fail", "bug", "crash", "broken", "not working"],
            "integration": ["integration", "interface", "connection", "sync", "data transfer"],
            "security": ["security", "access", "permission", "unauthorized", "breach"],
            "reporting": ["report", "dashboard", "analytics", "data", "export"]
        }
        
        category_scores = {}
        
        for category, keywords in categories.items():
            score = sum(1 for keyword in keywords if keyword in content)
            category_scores[category] = score
        
        # Return category with highest score, or "general" if no match
        if not category_scores or max(category_scores.values()) == 0:
            return "general"
        
        return max(category_scores.items(), key=lambda x: x[1])[0]
    
    def _calculate_severity(self, sentiment_score: float, indicator_count: int) -> str:
        """Calculate pain point severity."""
        # Combine sentiment score and indicator count
        severity_score = (abs(sentiment_score) * 10) + indicator_count
        
        if severity_score > 15:
            return "high"
        elif severity_score > 8:
            return "medium"
        else:
            return "low"
    
    def _calculate_overall_sentiment(self, sentiments: List[Dict]) -> Dict:
        """Calculate overall sentiment statistics."""
        scores = [s["score"] for s in sentiments]
        
        return {
            "average_score": float(np.mean(scores)),
            "median_score": float(np.median(scores)),
            "std_deviation": float(np.std(scores)),
            "positive_ratio": sum(1 for s in scores if s > 0.3) / len(scores),
            "negative_ratio": sum(1 for s in scores if s < -0.3) / len(scores),
            "neutral_ratio": sum(1 for s in scores if -0.3 <= s <= 0.3) / len(scores),
            "total_analyzed": len(scores)
        }
    
    def _aggregate_by_category(self, category_sentiments: Dict[str, List[float]]) -> Dict:
        """Aggregate sentiment by category."""
        aggregated = {}
        
        for category, scores in category_sentiments.items():
            if scores:
                aggregated[category] = {
                    "average_score": float(np.mean(scores)),
                    "count": len(scores),
                    "negative_count": sum(1 for s in scores if s < -0.3)
                }
        
        return aggregated
    
    def _rank_pain_points(self, pain_points: List[Dict]) -> List[Dict]:
        """Rank pain points by severity and frequency."""
        if not pain_points:
            return []
        
        # Group by category
        category_groups = defaultdict(list)
        for pp in pain_points:
            category_groups[pp["category"]].append(pp)
        
        # Rank within each category
        ranked = []
        
        for category, points in category_groups.items():
            # Sort by severity
            severity_order = {"high": 3, "medium": 2, "low": 1}
            sorted_points = sorted(
                points,
                key=lambda x: (severity_order[x["severity"]], abs(x["sentiment_score"])),
                reverse=True
            )
            
            # Add category summary
            for point in sorted_points:
                point["category_count"] = len(points)
            
            ranked.extend(sorted_points)
        
        return ranked[:100]  # Limit to top 100
    
    def _extract_top_issues(self, pain_points: List[Dict]) -> List[Dict]:
        """Extract and summarize top issues."""
        if not pain_points:
            return []
        
        # Count by category and severity
        issue_summary = defaultdict(lambda: {"count": 0, "high": 0, "medium": 0, "low": 0})
        
        for pp in pain_points:
            category = pp["category"]
            severity = pp["severity"]
            
            issue_summary[category]["count"] += 1
            issue_summary[category][severity] += 1
        
        # Convert to list and sort
        top_issues = [
            {
                "category": category,
                "total_count": stats["count"],
                "high_severity": stats["high"],
                "medium_severity": stats["medium"],
                "low_severity": stats["low"],
                "priority": stats["high"] * 3 + stats["medium"] * 2 + stats["low"]
            }
            for category, stats in issue_summary.items()
        ]
        
        top_issues.sort(key=lambda x: x["priority"], reverse=True)
        
        return top_issues[:10]
    
    def _generate_heatmap_data(self, pain_points: List[Dict]) -> List[Dict]:
        """Generate data for pain point heatmap visualization."""
        if not pain_points:
            return []
        
        # Create matrix: category x severity
        heatmap_data = []
        
        categories = list(set(pp["category"] for pp in pain_points))
        severities = ["high", "medium", "low"]
        
        for category in categories:
            for severity in severities:
                count = sum(
                    1 for pp in pain_points
                    if pp["category"] == category and pp["severity"] == severity
                )
                
                if count > 0:
                    heatmap_data.append({
                        "category": category,
                        "severity": severity,
                        "count": count
                    })
        
        return heatmap_data
    
    def _empty_results(self) -> Dict:
        """Return empty results structure."""
        return {
            "overall_sentiment": {},
            "pain_points": [],
            "sentiment_by_category": {},
            "sentiment_trend": [],
            "top_issues": [],
            "heatmap_data": []
        }
    
    def generate_sentiment_report(self, results: Dict) -> str:
        """Generate a text report from sentiment analysis results."""
        report_lines = [
            "="*60,
            "SENTIMENT ANALYSIS & PAIN POINT REPORT",
            "="*60,
            ""
        ]
        
        # Overall sentiment
        if results.get("overall_sentiment"):
            overall = results["overall_sentiment"]
            report_lines.extend([
                "OVERALL SENTIMENT:",
                f"  Average Score: {overall.get('average_score', 0):.3f}",
                f"  Positive Ratio: {overall.get('positive_ratio', 0):.1%}",
                f"  Negative Ratio: {overall.get('negative_ratio', 0):.1%}",
                f"  Neutral Ratio: {overall.get('neutral_ratio', 0):.1%}",
                f"  Total Analyzed: {overall.get('total_analyzed', 0)}",
                ""
            ])
        
        # Top issues
        if results.get("top_issues"):
            report_lines.append("TOP ISSUES BY CATEGORY:")
            for issue in results["top_issues"][:5]:
                report_lines.extend([
                    f"  {issue['category'].upper()}:",
                    f"    Total: {issue['total_count']} (High: {issue['high_severity']}, Medium: {issue['medium_severity']}, Low: {issue['low_severity']})",
                ])
            report_lines.append("")
        
        # Pain points summary
        if results.get("pain_points"):
            report_lines.extend([
                f"TOTAL PAIN POINTS IDENTIFIED: {len(results['pain_points'])}",
                ""
            ])
        
        return "\n".join(report_lines)
