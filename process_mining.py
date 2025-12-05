"""
Process Mining & Discovery Module for ERP Modernization Health Check.
Analyzes process flows, variants, and patterns.
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from loguru import logger

from langchain.schema import Document


class ProcessMiningEngine:
    """Engine for process mining and discovery analysis."""
    
    def __init__(self, min_variant_frequency: float = 0.05):
        """
        Initialize process mining engine.
        
        Args:
            min_variant_frequency: Minimum frequency threshold for process variants
        """
        self.min_variant_frequency = min_variant_frequency
        self.process_data = []
        self.variants = {}
        self.bottlenecks = []
    
    def analyze_process_maps(self, documents: List[Document]) -> Dict:
        """
        Analyze process maps and workflows from documents.
        
        Args:
            documents: Documents containing process information
            
        Returns:
            Analysis results with process maps and variants
        """
        logger.info(f"Analyzing process maps from {len(documents)} documents")
        
        # Extract process-related documents
        process_docs = [
            doc for doc in documents 
            if doc.metadata.get("category") in ["process_maps", "erp_exports"]
        ]
        
        if not process_docs:
            logger.warning("No process-related documents found")
            return {}
        
        results = {
            "total_processes": 0,
            "variants": [],
            "bottlenecks": [],
            "process_complexity": {},
            "recommendations": []
        }
        
        # Analyze each document
        for doc in process_docs:
            process_info = self._extract_process_info(doc)
            if process_info:
                self.process_data.append(process_info)
        
        # Perform variant analysis
        if self.process_data:
            results["variants"] = self._discover_variants()
            results["bottlenecks"] = self._identify_bottlenecks()
            results["process_complexity"] = self._calculate_complexity()
            results["total_processes"] = len(self.process_data)
            results["recommendations"] = self._generate_recommendations()
        
        logger.info(f"Process analysis complete. Found {len(results['variants'])} variants")
        
        return results
    
    def _extract_process_info(self, document: Document) -> Optional[Dict]:
        """Extract process information from document."""
        content = document.page_content
        metadata = document.metadata
        
        # Simple process extraction (can be enhanced with NLP/ML)
        process_info = {
            "source": metadata.get("source", "unknown"),
            "process_name": self._extract_process_name(content),
            "steps": self._extract_steps(content),
            "duration": self._extract_duration(content),
            "frequency": self._extract_frequency(content),
            "participants": self._extract_participants(content),
            "systems": self._extract_systems(content)
        }
        
        # Only return if we found meaningful process info
        if process_info["steps"] or process_info["process_name"]:
            return process_info
        
        return None
    
    def _extract_process_name(self, content: str) -> str:
        """Extract process name from content."""
        lines = content.split('\n')
        
        # Look for common process indicators
        process_keywords = ["process:", "workflow:", "procedure:", "flow:"]
        
        for line in lines[:10]:  # Check first 10 lines
            line_lower = line.lower().strip()
            for keyword in process_keywords:
                if keyword in line_lower:
                    return line.split(':')[-1].strip()
        
        # Default to first non-empty line if nothing found
        for line in lines:
            if line.strip():
                return line.strip()[:100]  # Limit length
        
        return "Unknown Process"
    
    def _extract_steps(self, content: str) -> List[str]:
        """Extract process steps from content."""
        steps = []
        lines = content.split('\n')
        
        # Look for numbered steps, bullet points, or step indicators
        step_indicators = [r'^\d+\.', r'^\d+\)', r'^-', r'^•', r'^step', r'^\*']
        
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue
            
            # Check if line starts with step indicator
            is_step = any(
                line_clean.lower().startswith(indicator.strip('^')) or
                any(c.isdigit() for c in line_clean[:5])
                for indicator in step_indicators
            )
            
            if is_step and len(line_clean) > 5:
                steps.append(line_clean[:200])  # Limit step length
        
        return steps[:50]  # Limit number of steps
    
    def _extract_duration(self, content: str) -> Optional[float]:
        """Extract process duration in hours."""
        import re
        
        # Look for duration patterns
        duration_patterns = [
            r'(\d+\.?\d*)\s*hours?',
            r'(\d+\.?\d*)\s*days?',
            r'(\d+\.?\d*)\s*minutes?',
            r'duration[:\s]+(\d+\.?\d*)'
        ]
        
        content_lower = content.lower()
        
        for pattern in duration_patterns:
            match = re.search(pattern, content_lower)
            if match:
                value = float(match.group(1))
                # Convert to hours
                if 'day' in pattern:
                    value *= 24
                elif 'minute' in pattern:
                    value /= 60
                return value
        
        return None
    
    def _extract_frequency(self, content: str) -> Optional[int]:
        """Extract process frequency (executions per month)."""
        import re
        
        frequency_patterns = [
            r'(\d+)\s*times?\s*per\s*month',
            r'(\d+)\s*times?\s*per\s*week',
            r'(\d+)\s*times?\s*per\s*day',
            r'frequency[:\s]+(\d+)'
        ]
        
        content_lower = content.lower()
        
        for pattern in frequency_patterns:
            match = re.search(pattern, content_lower)
            if match:
                value = int(match.group(1))
                # Convert to per month
                if 'week' in pattern:
                    value *= 4
                elif 'day' in pattern:
                    value *= 30
                return value
        
        return None
    
    def _extract_participants(self, content: str) -> List[str]:
        """Extract process participants/roles."""
        participants = []
        
        role_keywords = [
            "manager", "approver", "reviewer", "user", "admin", "analyst",
            "accountant", "controller", "buyer", "vendor", "customer"
        ]
        
        content_lower = content.lower()
        
        for keyword in role_keywords:
            if keyword in content_lower:
                participants.append(keyword.title())
        
        return list(set(participants))
    
    def _extract_systems(self, content: str) -> List[str]:
        """Extract systems involved in process."""
        systems = []
        
        system_keywords = [
            "sap", "oracle", "dynamics", "salesforce", "workday",
            "concur", "ariba", "successfactors", "erp", "crm"
        ]
        
        content_lower = content.lower()
        
        for keyword in system_keywords:
            if keyword in content_lower:
                systems.append(keyword.upper())
        
        return list(set(systems))
    
    def _discover_variants(self) -> List[Dict]:
        """Discover process variants and their frequencies."""
        if not self.process_data:
            return []
        
        # Group processes by similarity
        variant_groups = defaultdict(list)
        
        for process in self.process_data:
            # Create variant signature based on steps
            signature = self._create_variant_signature(process)
            variant_groups[signature].append(process)
        
        # Calculate statistics for each variant
        variants = []
        total_processes = len(self.process_data)
        
        for signature, processes in variant_groups.items():
            frequency = len(processes) / total_processes
            
            # Only include variants above threshold
            if frequency >= self.min_variant_frequency:
                avg_duration = np.mean([
                    p["duration"] for p in processes if p["duration"]
                ]) if any(p["duration"] for p in processes) else None
                
                variants.append({
                    "variant_id": signature[:50],
                    "frequency": frequency,
                    "count": len(processes),
                    "avg_duration_hours": avg_duration,
                    "steps": processes[0]["steps"][:5],  # Sample steps
                    "systems": list(set(sum([p["systems"] for p in processes], [])))
                })
        
        # Sort by frequency
        variants.sort(key=lambda x: x["frequency"], reverse=True)
        
        return variants
    
    def _create_variant_signature(self, process: Dict) -> str:
        """Create a signature for process variant grouping."""
        # Simplified signature based on number of steps and systems
        steps_count = len(process["steps"])
        systems = sorted(process["systems"])
        
        return f"{steps_count}_{'_'.join(systems)}"
    
    def _identify_bottlenecks(self) -> List[Dict]:
        """Identify process bottlenecks."""
        bottlenecks = []
        
        if not self.process_data:
            return bottlenecks
        
        # Find processes with high duration
        durations = [p["duration"] for p in self.process_data if p["duration"]]
        
        if durations:
            avg_duration = np.mean(durations)
            std_duration = np.std(durations)
            threshold = avg_duration + std_duration
            
            for process in self.process_data:
                if process["duration"] and process["duration"] > threshold:
                    bottlenecks.append({
                        "process_name": process["process_name"],
                        "duration_hours": process["duration"],
                        "deviation": (process["duration"] - avg_duration) / std_duration,
                        "impact": "high" if process["duration"] > threshold * 1.5 else "medium"
                    })
        
        return bottlenecks
    
    def _calculate_complexity(self) -> Dict:
        """Calculate process complexity metrics."""
        if not self.process_data:
            return {}
        
        step_counts = [len(p["steps"]) for p in self.process_data]
        system_counts = [len(p["systems"]) for p in self.process_data]
        participant_counts = [len(p["participants"]) for p in self.process_data]
        
        return {
            "avg_steps": float(np.mean(step_counts)) if step_counts else 0,
            "max_steps": int(np.max(step_counts)) if step_counts else 0,
            "avg_systems": float(np.mean(system_counts)) if system_counts else 0,
            "avg_participants": float(np.mean(participant_counts)) if participant_counts else 0,
            "complexity_score": self._compute_complexity_score(step_counts, system_counts, participant_counts)
        }
    
    def _compute_complexity_score(self, steps: List[int], systems: List[int], participants: List[int]) -> float:
        """Compute overall complexity score (0-100)."""
        if not steps:
            return 0
        
        # Weighted complexity formula
        step_factor = min(np.mean(steps) / 20, 1) * 40  # Max 40 points
        system_factor = min(np.mean(systems) / 5, 1) * 30  # Max 30 points
        participant_factor = min(np.mean(participants) / 10, 1) * 30  # Max 30 points
        
        return round(step_factor + system_factor + participant_factor, 2)
    
    def _generate_recommendations(self) -> List[str]:
        """Generate process improvement recommendations."""
        recommendations = []
        
        if not self.process_data:
            return recommendations
        
        complexity = self._calculate_complexity()
        
        # Complexity-based recommendations
        if complexity.get("complexity_score", 0) > 70:
            recommendations.append("High process complexity detected. Consider process simplification and automation opportunities.")
        
        if complexity.get("avg_systems", 0) > 3:
            recommendations.append("Multiple systems involved in processes. Evaluate integration and consolidation opportunities.")
        
        # Bottleneck-based recommendations
        if len(self.bottlenecks) > 0:
            recommendations.append(f"Identified {len(self.bottlenecks)} process bottlenecks. Prioritize optimization of high-duration workflows.")
        
        # Variant-based recommendations
        if len(self.variants) > 10:
            recommendations.append("High process variance detected. Standardize common workflows to reduce complexity.")
        
        return recommendations
    
    def export_process_graph(self) -> Dict:
        """Export process graph data for visualization."""
        nodes = []
        edges = []
        
        for idx, process in enumerate(self.process_data):
            # Create node for process
            nodes.append({
                "id": f"process_{idx}",
                "label": process["process_name"][:50],
                "systems": process["systems"],
                "steps": len(process["steps"])
            })
            
            # Create edges between systems
            systems = process["systems"]
            for i in range(len(systems) - 1):
                edges.append({
                    "source": systems[i],
                    "target": systems[i + 1],
                    "process": process["process_name"][:30]
                })
        
        return {
            "nodes": nodes,
            "edges": edges
        }
