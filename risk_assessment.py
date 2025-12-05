"""
Risk & Readiness Assessment Module for ERP Modernization Health Check.
Analyzes audit findings and generates risk heatmaps.
"""
from typing import List, Dict, Optional
from collections import defaultdict
import numpy as np
import pandas as pd
from loguru import logger

from langchain.schema import Document


class RiskAssessmentEngine:
    """Engine for risk assessment and readiness evaluation."""
    
    def __init__(self, risk_weights: Optional[Dict[str, float]] = None):
        """
        Initialize risk assessment engine.
        
        Args:
            risk_weights: Weights for different risk levels
        """
        self.risk_weights = risk_weights or {"high": 1.0, "medium": 0.6, "low": 0.3}
        self.risk_findings = []
        self.readiness_factors = {}
    
    def assess_risks(self, documents: List[Document]) -> Dict:
        """
        Assess risks from audit findings and other sources.
        
        Args:
            documents: Documents containing audit and risk information
            
        Returns:
            Risk assessment results with heatmap data
        """
        logger.info(f"Assessing risks from {len(documents)} documents")
        
        # Extract audit and risk documents
        risk_docs = [
            doc for doc in documents
            if doc.metadata.get("category") in ["audits", "pain_points", "erp_exports"]
        ]
        
        if not risk_docs:
            logger.warning("No risk-related documents found")
            return {}
        
        # Extract risk findings
        self._extract_risk_findings(risk_docs)
        
        # Assess readiness
        readiness_score = self._assess_readiness(risk_docs)
        
        results = {
            "risk_summary": self._create_risk_summary(),
            "risk_findings": self.risk_findings,
            "risk_heatmap": self._generate_risk_heatmap(),
            "readiness_score": readiness_score,
            "readiness_factors": self.readiness_factors,
            "mitigation_strategies": self._generate_mitigations(),
            "recommendations": self._generate_recommendations()
        }
        
        logger.info(f"Risk assessment complete. Found {len(self.risk_findings)} risk findings")
        
        return results
    
    def _extract_risk_findings(self, documents: List[Document]):
        """Extract risk findings from documents."""
        import re
        
        risk_indicators = {
            "high": [
                "critical", "severe", "major", "urgent", "immediate",
                "compliance violation", "security breach", "data loss"
            ],
            "medium": [
                "moderate", "significant", "important", "concern",
                "inefficiency", "limitation", "gap"
            ],
            "low": [
                "minor", "minor", "observation", "recommendation",
                "improvement opportunity", "suggestion"
            ]
        }
        
        risk_categories = {
            "security": ["security", "vulnerability", "breach", "unauthorized", "encryption"],
            "compliance": ["compliance", "regulation", "policy", "audit", "violation"],
            "data_quality": ["data quality", "accuracy", "integrity", "validation", "duplication"],
            "performance": ["performance", "slow", "timeout", "latency", "bottleneck"],
            "integration": ["integration", "interface", "connectivity", "sync", "data transfer"],
            "usability": ["usability", "user experience", "training", "complexity"],
            "operational": ["operational", "process", "workflow", "procedure", "manual"]
        }
        
        for doc in documents:
            content = doc.page_content
            content_lower = content.lower()
            
            # Detect risk level
            risk_level = self._detect_risk_level(content_lower, risk_indicators)
            
            if not risk_level:
                continue
            
            # Detect risk category
            risk_category = self._detect_risk_category(content_lower, risk_categories)
            
            # Extract specific findings
            finding_text = self._extract_finding_text(content, risk_indicators[risk_level])
            
            if finding_text:
                self.risk_findings.append({
                    "source": doc.metadata.get("source", "unknown"),
                    "category": risk_category,
                    "level": risk_level,
                    "finding": finding_text,
                    "impact": self._assess_impact(risk_level),
                    "likelihood": self._assess_likelihood(content_lower),
                    "risk_score": self._calculate_risk_score(risk_level, content_lower)
                })
    
    def _detect_risk_level(self, content: str, risk_indicators: Dict[str, List[str]]) -> Optional[str]:
        """Detect risk level from content."""
        for level, indicators in risk_indicators.items():
            if any(indicator in content for indicator in indicators):
                return level
        return None
    
    def _detect_risk_category(self, content: str, risk_categories: Dict[str, List[str]]) -> str:
        """Detect risk category from content."""
        category_scores = {}
        
        for category, keywords in risk_categories.items():
            score = sum(1 for keyword in keywords if keyword in content)
            category_scores[category] = score
        
        if not category_scores or max(category_scores.values()) == 0:
            return "general"
        
        return max(category_scores.items(), key=lambda x: x[1])[0]
    
    def _extract_finding_text(self, content: str, indicators: List[str]) -> Optional[str]:
        """Extract specific finding text around risk indicators."""
        sentences = content.split('.')
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(indicator in sentence_lower for indicator in indicators):
                # Clean and return first meaningful finding
                finding = sentence.strip()
                if len(finding) > 20:
                    return finding[:500]  # Limit length
        
        return None
    
    def _assess_impact(self, risk_level: str) -> str:
        """Assess business impact of risk."""
        impact_mapping = {
            "high": "critical",
            "medium": "moderate",
            "low": "minimal"
        }
        return impact_mapping.get(risk_level, "unknown")
    
    def _assess_likelihood(self, content: str) -> str:
        """Assess likelihood of risk occurring."""
        likelihood_indicators = {
            "high": ["frequent", "recurring", "ongoing", "persistent", "common"],
            "medium": ["occasional", "periodic", "intermittent", "sometimes"],
            "low": ["rare", "unlikely", "infrequent", "seldom"]
        }
        
        for likelihood, indicators in likelihood_indicators.items():
            if any(indicator in content for indicator in indicators):
                return likelihood
        
        return "medium"  # Default
    
    def _calculate_risk_score(self, risk_level: str, content: str) -> float:
        """Calculate overall risk score (0-100)."""
        # Base score from risk level
        level_scores = {"high": 80, "medium": 50, "low": 20}
        base_score = level_scores.get(risk_level, 30)
        
        # Adjust by likelihood
        likelihood = self._assess_likelihood(content)
        likelihood_multipliers = {"high": 1.2, "medium": 1.0, "low": 0.7}
        multiplier = likelihood_multipliers.get(likelihood, 1.0)
        
        return min(base_score * multiplier, 100)
    
    def _create_risk_summary(self) -> Dict:
        """Create summary of risk findings."""
        if not self.risk_findings:
            return {}
        
        total_risks = len(self.risk_findings)
        
        # Count by level
        level_counts = {
            "high": sum(1 for r in self.risk_findings if r["level"] == "high"),
            "medium": sum(1 for r in self.risk_findings if r["level"] == "medium"),
            "low": sum(1 for r in self.risk_findings if r["level"] == "low")
        }
        
        # Count by category
        category_counts = defaultdict(int)
        for finding in self.risk_findings:
            category_counts[finding["category"]] += 1
        
        # Calculate overall risk score
        overall_score = np.mean([f["risk_score"] for f in self.risk_findings])
        
        return {
            "total_findings": total_risks,
            "by_level": level_counts,
            "by_category": dict(category_counts),
            "overall_risk_score": float(overall_score),
            "critical_findings": level_counts["high"]
        }
    
    def _generate_risk_heatmap(self) -> List[Dict]:
        """Generate risk heatmap data."""
        if not self.risk_findings:
            return []
        
        heatmap_data = []
        
        # Create matrix: category x level
        categories = list(set(f["category"] for f in self.risk_findings))
        levels = ["high", "medium", "low"]
        
        for category in categories:
            for level in levels:
                # Count findings
                count = sum(
                    1 for f in self.risk_findings
                    if f["category"] == category and f["level"] == level
                )
                
                if count > 0:
                    # Calculate aggregate risk score
                    relevant_findings = [
                        f for f in self.risk_findings
                        if f["category"] == category and f["level"] == level
                    ]
                    avg_score = np.mean([f["risk_score"] for f in relevant_findings])
                    
                    heatmap_data.append({
                        "category": category,
                        "level": level,
                        "count": count,
                        "risk_score": float(avg_score)
                    })
        
        return heatmap_data
    
    def _assess_readiness(self, documents: List[Document]) -> Dict:
        """Assess modernization readiness."""
        readiness_factors = {
            "technical": 0,
            "organizational": 0,
            "process": 0,
            "data": 0,
            "security": 0
        }
        
        factor_indicators = {
            "technical": {
                "positive": ["modern", "updated", "integrated", "automated", "cloud-ready"],
                "negative": ["legacy", "outdated", "manual", "on-premise", "customized"]
            },
            "organizational": {
                "positive": ["trained", "skilled", "experienced", "change management", "leadership"],
                "negative": ["untrained", "resistance", "turnover", "siloed", "unclear roles"]
            },
            "process": {
                "positive": ["documented", "standardized", "optimized", "efficient", "streamlined"],
                "negative": ["undocumented", "ad-hoc", "complex", "inefficient", "redundant"]
            },
            "data": {
                "positive": ["accurate", "clean", "structured", "validated", "governed"],
                "negative": ["inaccurate", "duplicate", "inconsistent", "unstructured", "ungoverned"]
            },
            "security": {
                "positive": ["secure", "compliant", "encrypted", "monitored", "controlled"],
                "negative": ["vulnerable", "non-compliant", "exposed", "unmonitored", "unrestricted"]
            }
        }
        
        # Analyze documents for readiness indicators
        for doc in documents:
            content_lower = doc.page_content.lower()
            
            for factor, indicators in factor_indicators.items():
                positive_count = sum(1 for ind in indicators["positive"] if ind in content_lower)
                negative_count = sum(1 for ind in indicators["negative"] if ind in content_lower)
                
                # Calculate factor score (0-100)
                total_indicators = positive_count + negative_count
                if total_indicators > 0:
                    factor_score = (positive_count / total_indicators) * 100
                    readiness_factors[factor] += factor_score
        
        # Normalize scores
        doc_count = len(documents) if documents else 1
        for factor in readiness_factors:
            readiness_factors[factor] = round(readiness_factors[factor] / doc_count, 2)
        
        self.readiness_factors = readiness_factors
        
        # Calculate overall readiness
        overall_readiness = round(np.mean(list(readiness_factors.values())), 2)
        
        return {
            "overall_score": overall_readiness,
            "factors": readiness_factors,
            "status": self._get_readiness_status(overall_readiness),
            "blockers": self._identify_blockers(readiness_factors)
        }
    
    def _get_readiness_status(self, score: float) -> str:
        """Get readiness status from score."""
        if score >= 75:
            return "ready"
        elif score >= 50:
            return "partially_ready"
        else:
            return "not_ready"
    
    def _identify_blockers(self, readiness_factors: Dict[str, float]) -> List[str]:
        """Identify readiness blockers."""
        blockers = []
        
        for factor, score in readiness_factors.items():
            if score < 40:
                blockers.append(f"{factor.replace('_', ' ').title()} readiness is below threshold ({score:.1f}%)")
        
        return blockers
    
    def _generate_mitigations(self) -> List[Dict]:
        """Generate risk mitigation strategies."""
        mitigations = []
        
        # Group risks by category
        category_risks = defaultdict(list)
        for finding in self.risk_findings:
            category_risks[finding["category"]].append(finding)
        
        # Generate mitigation for each category
        mitigation_templates = {
            "security": "Implement enhanced security controls including access management, encryption, and monitoring",
            "compliance": "Establish compliance framework with regular audits and policy enforcement",
            "data_quality": "Deploy data quality management program with validation rules and cleansing processes",
            "performance": "Optimize system performance through infrastructure upgrades and code optimization",
            "integration": "Modernize integration architecture using API-first approach and middleware",
            "usability": "Improve user experience through redesign and comprehensive training program",
            "operational": "Standardize and automate operational processes with workflow management"
        }
        
        for category, risks in category_risks.items():
            high_risk_count = sum(1 for r in risks if r["level"] == "high")
            
            if high_risk_count > 0 or len(risks) > 3:
                mitigations.append({
                    "category": category,
                    "risk_count": len(risks),
                    "high_risk_count": high_risk_count,
                    "strategy": mitigation_templates.get(category, "Address identified risks through systematic remediation"),
                    "priority": "high" if high_risk_count > 0 else "medium"
                })
        
        # Sort by priority and risk count
        mitigations.sort(key=lambda x: (x["priority"] == "high", x["risk_count"]), reverse=True)
        
        return mitigations
    
    def _generate_recommendations(self) -> List[str]:
        """Generate risk management recommendations."""
        recommendations = []
        
        if not self.risk_findings:
            recommendations.append("No significant risks identified. Continue monitoring.")
            return recommendations
        
        summary = self._create_risk_summary()
        
        # Critical findings
        if summary.get("critical_findings", 0) > 0:
            recommendations.append(
                f"Address {summary['critical_findings']} critical findings immediately before proceeding with modernization."
            )
        
        # Category-specific recommendations
        category_counts = summary.get("by_category", {})
        top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        for category, count in top_categories:
            recommendations.append(
                f"Focus on {category.replace('_', ' ')} risks ({count} findings) as a priority area."
            )
        
        # Readiness recommendations
        if self.readiness_factors:
            low_readiness = [
                factor for factor, score in self.readiness_factors.items()
                if score < 50
            ]
            
            if low_readiness:
                recommendations.append(
                    f"Improve readiness in: {', '.join(f.replace('_', ' ') for f in low_readiness)}"
                )
        
        return recommendations
    
    def export_risk_matrix(self) -> pd.DataFrame:
        """Export risk assessment as a matrix."""
        if not self.risk_findings:
            return pd.DataFrame()
        
        data = []
        for finding in self.risk_findings:
            data.append({
                "Category": finding["category"].replace("_", " ").title(),
                "Level": finding["level"].upper(),
                "Impact": finding["impact"],
                "Likelihood": finding["likelihood"],
                "Risk Score": finding["risk_score"],
                "Finding": finding["finding"][:100]  # Truncate for display
            })
        
        return pd.DataFrame(data)
