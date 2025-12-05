"""
Benchmarking & Value Driver Analysis Module for ERP Modernization Health Check.
Compares KPIs against industry benchmarks and identifies value drivers.
"""
from typing import List, Dict, Optional
import numpy as np
import pandas as pd
from loguru import logger

from langchain.schema import Document


class BenchmarkingEngine:
    """Engine for benchmarking and value driver analysis."""
    
    # Industry benchmark ranges (can be loaded from external source)
    INDUSTRY_BENCHMARKS = {
        "process_cycle_time": {"optimal": 24, "acceptable": 48, "poor": 72, "unit": "hours"},
        "automation_rate": {"optimal": 0.80, "acceptable": 0.60, "poor": 0.40, "unit": "ratio"},
        "user_satisfaction": {"optimal": 4.5, "acceptable": 3.5, "poor": 2.5, "unit": "score"},
        "system_uptime": {"optimal": 0.99, "acceptable": 0.95, "poor": 0.90, "unit": "ratio"},
        "integration_coverage": {"optimal": 0.90, "acceptable": 0.70, "poor": 0.50, "unit": "ratio"},
        "data_accuracy": {"optimal": 0.98, "acceptable": 0.90, "poor": 0.80, "unit": "ratio"},
        "cost_per_transaction": {"optimal": 5, "acceptable": 10, "poor": 20, "unit": "dollars"},
        "training_hours": {"optimal": 8, "acceptable": 16, "poor": 32, "unit": "hours"}
    }
    
    def __init__(self, benchmark_threshold: float = 0.85):
        """
        Initialize benchmarking engine.
        
        Args:
            benchmark_threshold: Threshold for benchmark comparison (0-1)
        """
        self.benchmark_threshold = benchmark_threshold
        self.kpis = {}
        self.gaps = []
    
    def analyze_benchmarks(self, documents: List[Document]) -> Dict:
        """
        Analyze KPIs and compare against benchmarks.
        
        Args:
            documents: Documents containing KPI and benchmark data
            
        Returns:
            Benchmark analysis results
        """
        logger.info(f"Analyzing benchmarks from {len(documents)} documents")
        
        # Extract benchmark-related documents
        benchmark_docs = [
            doc for doc in documents
            if doc.metadata.get("category") in ["benchmarks", "erp_exports"]
        ]
        
        if not benchmark_docs:
            logger.warning("No benchmark documents found")
            return {}
        
        # Extract KPIs from documents
        self._extract_kpis(benchmark_docs)
        
        # Compare against benchmarks
        results = {
            "kpis": self.kpis,
            "gaps": self._identify_gaps(),
            "value_drivers": self._identify_value_drivers(),
            "prioritized_improvements": self._prioritize_improvements(),
            "gap_analysis_summary": self._create_gap_summary(),
            "recommendations": self._generate_recommendations()
        }
        
        logger.info(f"Benchmark analysis complete. Found {len(results['gaps'])} gaps")
        
        return results
    
    def _extract_kpis(self, documents: List[Document]):
        """Extract KPI values from documents."""
        import re
        
        kpi_patterns = {
            "process_cycle_time": [
                r'cycle\s*time[:\s]+(\d+\.?\d*)\s*hours?',
                r'process\s*time[:\s]+(\d+\.?\d*)\s*hours?'
            ],
            "automation_rate": [
                r'automation[:\s]+(\d+\.?\d*)%',
                r'automated[:\s]+(\d+\.?\d*)%'
            ],
            "user_satisfaction": [
                r'satisfaction[:\s]+(\d+\.?\d*)',
                r'rating[:\s]+(\d+\.?\d*)'
            ],
            "system_uptime": [
                r'uptime[:\s]+(\d+\.?\d*)%',
                r'availability[:\s]+(\d+\.?\d*)%'
            ],
            "integration_coverage": [
                r'integration[:\s]+(\d+\.?\d*)%',
                r'coverage[:\s]+(\d+\.?\d*)%'
            ],
            "data_accuracy": [
                r'accuracy[:\s]+(\d+\.?\d*)%',
                r'data\s*quality[:\s]+(\d+\.?\d*)%'
            ],
            "cost_per_transaction": [
                r'cost\s*per\s*transaction[:\s]+\$?(\d+\.?\d*)',
                r'transaction\s*cost[:\s]+\$?(\d+\.?\d*)'
            ],
            "training_hours": [
                r'training[:\s]+(\d+\.?\d*)\s*hours?',
                r'onboarding[:\s]+(\d+\.?\d*)\s*hours?'
            ]
        }
        
        for doc in documents:
            content = doc.page_content.lower()
            
            for kpi_name, patterns in kpi_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, content)
                    if match:
                        value = float(match.group(1))
                        
                        # Convert percentages to ratios
                        if '%' in pattern and value > 1:
                            value = value / 100
                        
                        # Store KPI value
                        if kpi_name not in self.kpis:
                            self.kpis[kpi_name] = {
                                "values": [],
                                "sources": []
                            }
                        
                        self.kpis[kpi_name]["values"].append(value)
                        self.kpis[kpi_name]["sources"].append(doc.metadata.get("source", "unknown"))
        
        # Calculate averages
        for kpi_name, kpi_data in self.kpis.items():
            if kpi_data["values"]:
                kpi_data["average"] = float(np.mean(kpi_data["values"]))
                kpi_data["count"] = len(kpi_data["values"])
    
    def _identify_gaps(self) -> List[Dict]:
        """Identify gaps between current KPIs and benchmarks."""
        gaps = []
        
        for kpi_name, kpi_data in self.kpis.items():
            if kpi_name not in self.INDUSTRY_BENCHMARKS:
                continue
            
            benchmark = self.INDUSTRY_BENCHMARKS[kpi_name]
            current_value = kpi_data.get("average")
            
            if current_value is None:
                continue
            
            # Determine performance level
            performance = self._evaluate_performance(current_value, benchmark)
            
            # Calculate gap
            gap_value = benchmark["optimal"] - current_value
            
            # Determine if improvement is needed
            if performance in ["poor", "acceptable"]:
                gaps.append({
                    "kpi": kpi_name,
                    "current_value": current_value,
                    "optimal_value": benchmark["optimal"],
                    "gap": gap_value,
                    "gap_percentage": abs(gap_value / benchmark["optimal"] * 100) if benchmark["optimal"] != 0 else 0,
                    "performance": performance,
                    "unit": benchmark["unit"],
                    "priority": self._calculate_priority(performance, gap_value, benchmark)
                })
        
        # Sort by priority
        gaps.sort(key=lambda x: x["priority"], reverse=True)
        
        return gaps
    
    def _evaluate_performance(self, value: float, benchmark: Dict) -> str:
        """Evaluate performance level against benchmark."""
        optimal = benchmark["optimal"]
        acceptable = benchmark["acceptable"]
        poor = benchmark["poor"]
        
        # Determine if higher is better based on benchmark structure
        higher_is_better = optimal > poor
        
        if higher_is_better:
            if value >= optimal:
                return "optimal"
            elif value >= acceptable:
                return "acceptable"
            else:
                return "poor"
        else:
            if value <= optimal:
                return "optimal"
            elif value <= acceptable:
                return "acceptable"
            else:
                return "poor"
    
    def _calculate_priority(self, performance: str, gap: float, benchmark: Dict) -> float:
        """Calculate improvement priority (0-100)."""
        # Base priority on performance level
        performance_score = {"poor": 100, "acceptable": 60, "optimal": 0}
        base_score = performance_score.get(performance, 0)
        
        # Adjust by gap magnitude
        gap_ratio = abs(gap) / benchmark["optimal"] if benchmark["optimal"] != 0 else 0
        gap_score = min(gap_ratio * 50, 50)
        
        return min(base_score + gap_score, 100)
    
    def _identify_value_drivers(self) -> List[Dict]:
        """Identify key value drivers for improvement."""
        value_drivers = []
        
        # Prioritize based on potential impact
        impact_weights = {
            "automation_rate": 0.9,
            "process_cycle_time": 0.85,
            "data_accuracy": 0.8,
            "integration_coverage": 0.75,
            "cost_per_transaction": 0.7,
            "system_uptime": 0.65,
            "user_satisfaction": 0.6,
            "training_hours": 0.5
        }
        
        for gap in self.gaps:
            kpi = gap["kpi"]
            impact_weight = impact_weights.get(kpi, 0.5)
            
            # Calculate value driver score
            value_score = gap["priority"] * impact_weight
            
            if value_score > 40:  # Only include significant value drivers
                value_drivers.append({
                    "kpi": kpi,
                    "impact_weight": impact_weight,
                    "value_score": value_score,
                    "potential_improvement": self._estimate_improvement_potential(gap),
                    "implementation_difficulty": self._estimate_difficulty(kpi)
                })
        
        # Sort by value score
        value_drivers.sort(key=lambda x: x["value_score"], reverse=True)
        
        return value_drivers
    
    def _estimate_improvement_potential(self, gap: Dict) -> str:
        """Estimate improvement potential."""
        gap_percentage = gap["gap_percentage"]
        
        if gap_percentage > 40:
            return "high"
        elif gap_percentage > 20:
            return "medium"
        else:
            return "low"
    
    def _estimate_difficulty(self, kpi: str) -> str:
        """Estimate implementation difficulty."""
        # Simplified difficulty assessment
        high_difficulty = ["automation_rate", "integration_coverage", "data_accuracy"]
        medium_difficulty = ["process_cycle_time", "cost_per_transaction", "system_uptime"]
        
        if kpi in high_difficulty:
            return "high"
        elif kpi in medium_difficulty:
            return "medium"
        else:
            return "low"
    
    def _prioritize_improvements(self) -> List[Dict]:
        """Prioritize improvements based on value and feasibility."""
        improvements = []
        
        for driver in self._identify_value_drivers():
            kpi = driver["kpi"]
            
            # Find corresponding gap
            gap = next((g for g in self.gaps if g["kpi"] == kpi), None)
            if not gap:
                continue
            
            # Calculate feasibility score (inverse of difficulty)
            difficulty_scores = {"low": 0.9, "medium": 0.6, "high": 0.3}
            feasibility = difficulty_scores.get(driver["implementation_difficulty"], 0.5)
            
            # Calculate overall priority (value * feasibility)
            priority_score = driver["value_score"] * feasibility
            
            improvements.append({
                "kpi": kpi,
                "current": gap["current_value"],
                "target": gap["optimal_value"],
                "improvement_potential": driver["potential_improvement"],
                "implementation_difficulty": driver["implementation_difficulty"],
                "priority_score": priority_score,
                "rank": 0  # Will be set after sorting
            })
        
        # Sort by priority score and assign ranks
        improvements.sort(key=lambda x: x["priority_score"], reverse=True)
        for idx, improvement in enumerate(improvements, 1):
            improvement["rank"] = idx
        
        return improvements
    
    def _create_gap_summary(self) -> Dict:
        """Create summary of gap analysis."""
        if not self.gaps:
            return {}
        
        total_gaps = len(self.gaps)
        
        # Count by performance level
        performance_counts = {
            "poor": sum(1 for g in self.gaps if g["performance"] == "poor"),
            "acceptable": sum(1 for g in self.gaps if g["performance"] == "acceptable"),
            "optimal": sum(1 for g in self.gaps if g["performance"] == "optimal")
        }
        
        # Calculate average gap
        avg_gap_percentage = np.mean([g["gap_percentage"] for g in self.gaps])
        
        return {
            "total_kpis_analyzed": len(self.kpis),
            "total_gaps_identified": total_gaps,
            "performance_distribution": performance_counts,
            "average_gap_percentage": float(avg_gap_percentage),
            "critical_gaps": sum(1 for g in self.gaps if g["priority"] > 70)
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        if not self.gaps:
            recommendations.append("All KPIs are performing at optimal levels.")
            return recommendations
        
        # Priority-based recommendations
        high_priority_gaps = [g for g in self.gaps if g["priority"] > 70]
        
        if high_priority_gaps:
            recommendations.append(
                f"Address {len(high_priority_gaps)} critical gaps immediately to improve system performance."
            )
        
        # Specific KPI recommendations
        for gap in self.gaps[:5]:  # Top 5 gaps
            kpi = gap["kpi"].replace("_", " ").title()
            recommendations.append(
                f"Improve {kpi} from {gap['current_value']:.2f} to {gap['optimal_value']:.2f} "
                f"({gap['performance']} → optimal)"
            )
        
        # Value driver recommendations
        value_drivers = self._identify_value_drivers()
        if value_drivers:
            top_driver = value_drivers[0]
            recommendations.append(
                f"Focus on {top_driver['kpi'].replace('_', ' ').title()} as the primary value driver "
                f"with {top_driver['potential_improvement']} improvement potential."
            )
        
        return recommendations
    
    def export_gap_matrix(self) -> pd.DataFrame:
        """Export gap analysis as a matrix for visualization."""
        if not self.gaps:
            return pd.DataFrame()
        
        data = []
        for gap in self.gaps:
            data.append({
                "KPI": gap["kpi"].replace("_", " ").title(),
                "Current": gap["current_value"],
                "Optimal": gap["optimal_value"],
                "Gap %": gap["gap_percentage"],
                "Performance": gap["performance"],
                "Priority": gap["priority"]
            })
        
        return pd.DataFrame(data)
