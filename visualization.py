"""
Visualization & Reporting Module for ERP Modernization Health Check.
Generates interactive dashboards, heatmaps, and reports.
"""
from typing import List, Dict, Optional
from pathlib import Path
import json
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from loguru import logger

from config import Config, get_config


class VisualizationEngine:
    """Engine for generating visualizations and reports."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize visualization engine."""
        self.config = config or get_config()
        self.output_dir = Path(self.config.visualization.output_directory)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_pain_point_heatmap(
        self,
        heatmap_data: List[Dict],
        output_file: str = "pain_point_heatmap.html"
    ) -> str:
        """
        Generate pain point heatmap visualization.
        
        Args:
            heatmap_data: Pain point data with category and severity
            output_file: Output filename
            
        Returns:
            Path to generated file
        """
        if not heatmap_data:
            logger.warning("No heatmap data provided")
            return ""
        
        # Convert to DataFrame
        df = pd.DataFrame(heatmap_data)
        
        # Pivot for heatmap
        pivot_df = df.pivot_table(
            values='count',
            index='category',
            columns='severity',
            aggfunc='sum',
            fill_value=0
        )
        
        # Ensure all severity levels are present
        for severity in ['high', 'medium', 'low']:
            if severity not in pivot_df.columns:
                pivot_df[severity] = 0
        
        # Reorder columns
        pivot_df = pivot_df[['high', 'medium', 'low']]
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=pivot_df.values,
            x=['High', 'Medium', 'Low'],
            y=pivot_df.index,
            colorscale=self.config.visualization.heatmap_colorscale,
            text=pivot_df.values,
            texttemplate='%{text}',
            textfont={"size": 12},
            colorbar=dict(title="Count")
        ))
        
        fig.update_layout(
            title="Pain Point Severity Heatmap",
            xaxis_title="Severity Level",
            yaxis_title="Category",
            width=self.config.visualization.heatmap_width,
            height=self.config.visualization.heatmap_height,
            template=self.config.visualization.dashboard_theme
        )
        
        # Save
        output_path = self.output_dir / output_file
        fig.write_html(str(output_path))
        logger.info(f"Pain point heatmap saved to {output_path}")
        
        return str(output_path)
    
    def generate_risk_heatmap(
        self,
        risk_data: List[Dict],
        output_file: str = "risk_heatmap.html"
    ) -> str:
        """Generate risk assessment heatmap."""
        if not risk_data:
            logger.warning("No risk data provided")
            return ""
        
        df = pd.DataFrame(risk_data)
        
        # Pivot for heatmap
        pivot_df = df.pivot_table(
            values='risk_score',
            index='category',
            columns='level',
            aggfunc='mean',
            fill_value=0
        )
        
        # Ensure all levels are present
        for level in ['high', 'medium', 'low']:
            if level not in pivot_df.columns:
                pivot_df[level] = 0
        
        pivot_df = pivot_df[['high', 'medium', 'low']]
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=pivot_df.values,
            x=['High', 'Medium', 'Low'],
            y=pivot_df.index,
            colorscale='Reds',
            text=pivot_df.values.round(1),
            texttemplate='%{text}',
            textfont={"size": 12},
            colorbar=dict(title="Risk Score")
        ))
        
        fig.update_layout(
            title="Risk Assessment Heatmap",
            xaxis_title="Risk Level",
            yaxis_title="Category",
            width=self.config.visualization.heatmap_width,
            height=self.config.visualization.heatmap_height,
            template=self.config.visualization.dashboard_theme
        )
        
        output_path = self.output_dir / output_file
        fig.write_html(str(output_path))
        logger.info(f"Risk heatmap saved to {output_path}")
        
        return str(output_path)
    
    def generate_sentiment_dashboard(
        self,
        sentiment_results: Dict,
        output_file: str = "sentiment_dashboard.html"
    ) -> str:
        """Generate sentiment analysis dashboard."""
        if not sentiment_results:
            logger.warning("No sentiment results provided")
            return ""
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Overall Sentiment Distribution',
                'Top Issues by Category',
                'Sentiment by Category',
                'Pain Point Severity'
            ),
            specs=[
                [{"type": "pie"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "bar"}]
            ]
        )
        
        # 1. Overall sentiment pie chart
        overall = sentiment_results.get('overall_sentiment', {})
        if overall:
            fig.add_trace(
                go.Pie(
                    labels=['Positive', 'Negative', 'Neutral'],
                    values=[
                        overall.get('positive_ratio', 0),
                        overall.get('negative_ratio', 0),
                        overall.get('neutral_ratio', 0)
                    ],
                    marker_colors=['green', 'red', 'gray']
                ),
                row=1, col=1
            )
        
        # 2. Top issues bar chart
        top_issues = sentiment_results.get('top_issues', [])
        if top_issues:
            categories = [issue['category'] for issue in top_issues[:5]]
            counts = [issue['total_count'] for issue in top_issues[:5]]
            
            fig.add_trace(
                go.Bar(x=categories, y=counts, marker_color='indianred'),
                row=1, col=2
            )
        
        # 3. Sentiment by category
        sentiment_by_cat = sentiment_results.get('sentiment_by_category', {})
        if sentiment_by_cat:
            categories = list(sentiment_by_cat.keys())
            scores = [sentiment_by_cat[cat]['average_score'] for cat in categories]
            
            fig.add_trace(
                go.Bar(x=categories, y=scores, marker_color='lightblue'),
                row=2, col=1
            )
        
        # 4. Pain point severity distribution
        pain_points = sentiment_results.get('pain_points', [])
        if pain_points:
            severity_counts = {'high': 0, 'medium': 0, 'low': 0}
            for pp in pain_points:
                severity = pp.get('severity', 'low')
                severity_counts[severity] += 1
            
            fig.add_trace(
                go.Bar(
                    x=list(severity_counts.keys()),
                    y=list(severity_counts.values()),
                    marker_color=['red', 'orange', 'yellow']
                ),
                row=2, col=2
            )
        
        fig.update_layout(
            title_text="Sentiment Analysis Dashboard",
            showlegend=False,
            height=1000,
            width=1400,
            template=self.config.visualization.dashboard_theme
        )
        
        output_path = self.output_dir / output_file
        fig.write_html(str(output_path))
        logger.info(f"Sentiment dashboard saved to {output_path}")
        
        return str(output_path)
    
    def generate_benchmark_dashboard(
        self,
        benchmark_results: Dict,
        output_file: str = "benchmark_dashboard.html"
    ) -> str:
        """Generate benchmarking dashboard."""
        if not benchmark_results:
            logger.warning("No benchmark results provided")
            return ""
        
        gaps = benchmark_results.get('gaps', [])
        
        if not gaps:
            logger.warning("No gap data available")
            return ""
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Current vs Optimal Values',
                'Gap Analysis by KPI',
                'Performance Distribution',
                'Priority Scores'
            ),
            specs=[
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "pie"}, {"type": "bar"}]
            ]
        )
        
        # Prepare data
        kpis = [gap['kpi'].replace('_', ' ').title() for gap in gaps[:8]]
        current_values = [gap['current_value'] for gap in gaps[:8]]
        optimal_values = [gap['optimal_value'] for gap in gaps[:8]]
        gap_percentages = [gap['gap_percentage'] for gap in gaps[:8]]
        priorities = [gap['priority'] for gap in gaps[:8]]
        
        # 1. Current vs Optimal
        fig.add_trace(
            go.Bar(name='Current', x=kpis, y=current_values, marker_color='lightcoral'),
            row=1, col=1
        )
        fig.add_trace(
            go.Bar(name='Optimal', x=kpis, y=optimal_values, marker_color='lightgreen'),
            row=1, col=1
        )
        
        # 2. Gap percentages
        fig.add_trace(
            go.Bar(x=kpis, y=gap_percentages, marker_color='orange'),
            row=1, col=2
        )
        
        # 3. Performance distribution pie
        performance_counts = {'poor': 0, 'acceptable': 0, 'optimal': 0}
        for gap in gaps:
            performance = gap.get('performance', 'acceptable')
            performance_counts[performance] += 1
        
        fig.add_trace(
            go.Pie(
                labels=list(performance_counts.keys()),
                values=list(performance_counts.values()),
                marker_colors=['red', 'yellow', 'green']
            ),
            row=2, col=1
        )
        
        # 4. Priority scores
        fig.add_trace(
            go.Bar(x=kpis, y=priorities, marker_color='steelblue'),
            row=2, col=2
        )
        
        fig.update_layout(
            title_text="Benchmarking & Gap Analysis Dashboard",
            showlegend=True,
            height=1000,
            width=1400,
            template=self.config.visualization.dashboard_theme
        )
        
        fig.update_xaxes(tickangle=45)
        
        output_path = self.output_dir / output_file
        fig.write_html(str(output_path))
        logger.info(f"Benchmark dashboard saved to {output_path}")
        
        return str(output_path)
    
    def generate_readiness_gauge(
        self,
        readiness_score: Dict,
        output_file: str = "readiness_gauge.html"
    ) -> str:
        """Generate readiness assessment gauge."""
        if not readiness_score:
            logger.warning("No readiness score provided")
            return ""
        
        overall = readiness_score.get('overall_score', 0)
        factors = readiness_score.get('factors', {})
        
        # Create gauge chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=overall,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Overall Readiness Score"},
            delta={'reference': 75, 'increasing': {'color': "green"}},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 75], 'color': "yellow"},
                    {'range': [75, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 75
                }
            }
        ))
        
        fig.update_layout(
            title="Modernization Readiness Assessment",
            height=500,
            template=self.config.visualization.dashboard_theme
        )
        
        output_path = self.output_dir / output_file
        fig.write_html(str(output_path))
        logger.info(f"Readiness gauge saved to {output_path}")
        
        # Also create factor breakdown
        if factors:
            self._generate_readiness_factors_chart(factors)
        
        return str(output_path)
    
    def _generate_readiness_factors_chart(self, factors: Dict):
        """Generate readiness factors breakdown chart."""
        factor_names = [f.replace('_', ' ').title() for f in factors.keys()]
        factor_scores = list(factors.values())
        
        fig = go.Figure(go.Bar(
            x=factor_names,
            y=factor_scores,
            marker_color=['green' if s >= 75 else 'yellow' if s >= 50 else 'red' for s in factor_scores],
            text=factor_scores,
            texttemplate='%{text:.1f}%',
            textposition='outside'
        ))
        
        fig.update_layout(
            title="Readiness Factors Breakdown",
            xaxis_title="Factor",
            yaxis_title="Score (%)",
            yaxis_range=[0, 100],
            height=500,
            template=self.config.visualization.dashboard_theme
        )
        
        output_path = self.output_dir / "readiness_factors.html"
        fig.write_html(str(output_path))
        logger.info(f"Readiness factors chart saved to {output_path}")
    
    def generate_executive_report(
        self,
        all_results: Dict,
        output_file: str = "executive_report.html"
    ) -> str:
        """Generate comprehensive executive report."""
        logger.info("Generating executive report")
        
        # Build HTML report
        html_content = self._build_executive_html(all_results)
        
        output_path = self.output_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Executive report saved to {output_path}")
        return str(output_path)
    
    def _build_executive_html(self, results: Dict) -> str:
        """Build HTML content for executive report."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ERP Modernization Health Check - Executive Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        .section {{
            background-color: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        .metric {{
            display: inline-block;
            margin: 10px 20px;
            padding: 15px;
            background-color: #ecf0f1;
            border-radius: 5px;
            min-width: 150px;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .metric-label {{
            font-size: 0.9em;
            color: #7f8c8d;
        }}
        .high-priority {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .medium-priority {{
            color: #f39c12;
            font-weight: bold;
        }}
        .low-priority {{
            color: #27ae60;
            font-weight: bold;
        }}
        ul {{
            padding-left: 20px;
        }}
        .footer {{
            text-align: center;
            color: #7f8c8d;
            margin-top: 40px;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>ERP Modernization Health Check</h1>
        <p>Executive Summary Report</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    {self._build_summary_section(results)}
    {self._build_sentiment_section(results.get('sentiment', {}))}
    {self._build_benchmark_section(results.get('benchmarking', {}))}
    {self._build_risk_section(results.get('risk', {}))}
    {self._build_recommendations_section(results)}
    
    <div class="footer">
        <p>ERP Modernization Health Check System</p>
        <p>Powered by Open Source AI & Analytics</p>
    </div>
</body>
</html>
        """
        return html
    
    def _build_summary_section(self, results: Dict) -> str:
        """Build summary section."""
        return """
    <div class="section">
        <h2>📊 Overall Assessment</h2>
        <div class="metric">
            <div class="metric-value">🎯</div>
            <div class="metric-label">Health Check Complete</div>
        </div>
        <p>Comprehensive analysis of ERP system covering sentiment analysis, process mining, 
        benchmarking, and risk assessment has been completed.</p>
    </div>
        """
    
    def _build_sentiment_section(self, sentiment: Dict) -> str:
        """Build sentiment analysis section."""
        if not sentiment:
            return ""
        
        overall = sentiment.get('overall_sentiment', {})
        pain_points = sentiment.get('pain_points', [])
        
        return f"""
    <div class="section">
        <h2>💭 Sentiment & Pain Points Analysis</h2>
        <div class="metric">
            <div class="metric-value">{overall.get('average_score', 0):.2f}</div>
            <div class="metric-label">Average Sentiment</div>
        </div>
        <div class="metric">
            <div class="metric-value">{len(pain_points)}</div>
            <div class="metric-label">Pain Points Identified</div>
        </div>
        <div class="metric">
            <div class="metric-value">{overall.get('negative_ratio', 0):.1%}</div>
            <div class="metric-label">Negative Sentiment</div>
        </div>
        <h3>Top Issues:</h3>
        <ul>
            {''.join(f'<li>{issue["category"]}: {issue["total_count"]} occurrences</li>' for issue in sentiment.get('top_issues', [])[:5])}
        </ul>
    </div>
        """
    
    def _build_benchmark_section(self, benchmarking: Dict) -> str:
        """Build benchmarking section."""
        if not benchmarking:
            return ""
        
        gaps = benchmarking.get('gaps', [])
        
        return f"""
    <div class="section">
        <h2>📈 Benchmarking & Gap Analysis</h2>
        <div class="metric">
            <div class="metric-value">{len(gaps)}</div>
            <div class="metric-label">Gaps Identified</div>
        </div>
        <h3>Priority Improvements:</h3>
        <ul>
            {''.join(f'<li class="{gap["performance"]}-priority">{gap["kpi"].replace("_", " ").title()}: {gap["gap_percentage"]:.1f}% gap</li>' for gap in gaps[:5])}
        </ul>
    </div>
        """
    
    def _build_risk_section(self, risk: Dict) -> str:
        """Build risk assessment section."""
        if not risk:
            return ""
        
        summary = risk.get('risk_summary', {})
        readiness = risk.get('readiness_score', {})
        
        return f"""
    <div class="section">
        <h2>⚠️ Risk Assessment</h2>
        <div class="metric">
            <div class="metric-value">{summary.get('total_findings', 0)}</div>
            <div class="metric-label">Total Risks</div>
        </div>
        <div class="metric">
            <div class="metric-value high-priority">{summary.get('critical_findings', 0)}</div>
            <div class="metric-label">Critical Findings</div>
        </div>
        <div class="metric">
            <div class="metric-value">{readiness.get('overall_score', 0):.1f}%</div>
            <div class="metric-label">Readiness Score</div>
        </div>
    </div>
        """
    
    def _build_recommendations_section(self, results: Dict) -> str:
        """Build recommendations section."""
        all_recommendations = []
        
        for key in ['sentiment', 'benchmarking', 'risk', 'process_mining']:
            if key in results and 'recommendations' in results[key]:
                all_recommendations.extend(results[key]['recommendations'])
        
        if not all_recommendations:
            return ""
        
        recommendations_html = ''.join(f'<li>{rec}</li>' for rec in all_recommendations[:10])
        
        return f"""
    <div class="section">
        <h2>💡 Key Recommendations</h2>
        <ul>
            {recommendations_html}
        </ul>
    </div>
        """
    
    def export_json_report(self, results: Dict, output_file: str = "full_report.json") -> str:
        """Export complete results as JSON."""
        output_path = self.output_dir / output_file
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"JSON report saved to {output_path}")
        return str(output_path)
