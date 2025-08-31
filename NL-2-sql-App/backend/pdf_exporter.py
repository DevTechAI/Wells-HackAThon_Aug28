#!/usr/bin/env python3
"""
PDF Export Module for SQL RAG Agent
Generates comprehensive PDF reports with query results, analysis, and insights
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io

class PDFExporter:
    """Generate PDF reports for SQL RAG Agent queries"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.darkblue
        ))
        
        # Section style
        self.styles.add(ParagraphStyle(
            name='CustomSection',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=15,
            textColor=colors.darkgreen
        ))
        
        # Code style
        self.styles.add(ParagraphStyle(
            name='CustomCode',
            parent=self.styles['Code'],
            fontSize=10,
            fontName='Courier',
            leftIndent=20,
            rightIndent=20,
            backColor=colors.lightgrey
        ))
        
        # Info style
        self.styles.add(ParagraphStyle(
            name='CustomInfo',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=10,
            leftIndent=20,
            textColor=colors.darkblue
        ))
    
    def generate_query_report(self, query_data: Dict[str, Any], output_path: str = None) -> bytes:
        """
        Generate comprehensive PDF report for a query
        
        Args:
            query_data: Dictionary containing all query information
            output_path: Optional path to save PDF file
            
        Returns:
            PDF content as bytes
        """
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Build PDF content
        story = []
        
        # Title page
        story.extend(self._create_title_page(query_data))
        story.append(PageBreak())
        
        # Query details
        story.extend(self._create_query_details(query_data))
        story.append(PageBreak())
        
        # Chain-of-Thought analysis
        story.extend(self._create_cot_analysis(query_data))
        story.append(PageBreak())
        
        # Results and analysis
        story.extend(self._create_results_analysis(query_data))
        story.append(PageBreak())
        
        # Security and validation
        story.extend(self._create_security_validation(query_data))
        story.append(PageBreak())
        
        # Performance metrics
        story.extend(self._create_performance_metrics(query_data))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Save to file if path provided
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_content)
        
        return pdf_content
    
    def _create_title_page(self, query_data: Dict[str, Any]) -> List:
        """Create title page"""
        elements = []
        
        # Main title
        title = Paragraph("SQL RAG Agent Query Report", self.styles['CustomTitle'])
        elements.append(title)
        elements.append(Spacer(1, 30))
        
        # Query information
        query_info = [
            ["Query Date:", query_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))],
            ["User:", query_data.get('user', 'Unknown')],
            ["Role:", query_data.get('role', 'Unknown')],
            ["Natural Language Query:", query_data.get('query', 'N/A')]
        ]
        
        query_table = Table(query_info, colWidths=[2*inch, 4*inch])
        query_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 0), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(query_table)
        elements.append(Spacer(1, 30))
        
        # Generated SQL
        sql_title = Paragraph("Generated SQL Query", self.styles['CustomSubtitle'])
        elements.append(sql_title)
        
        sql_code = Paragraph(
            f"<code>{query_data.get('sql', 'N/A')}</code>",
            self.styles['CustomCode']
        )
        elements.append(sql_code)
        
        return elements
    
    def _create_query_details(self, query_data: Dict[str, Any]) -> List:
        """Create query details section"""
        elements = []
        
        # Section title
        title = Paragraph("Query Analysis Details", self.styles['CustomSubtitle'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Query summary
        summary_title = Paragraph("Summary & Insights", self.styles['CustomSection'])
        elements.append(summary_title)
        
        summary_text = Paragraph(
            query_data.get('summary', 'No summary available'),
            self.styles['Normal']
        )
        elements.append(summary_text)
        elements.append(Spacer(1, 20))
        
        # Results overview
        results_title = Paragraph("Results Overview", self.styles['CustomSection'])
        elements.append(results_title)
        
        results_info = [
            ["Total Records:", str(query_data.get('results_count', 0))],
            ["Query Execution Time:", f"{query_data.get('query_time', 0):.3f} seconds"],
            ["Security Guards Applied:", str(query_data.get('guards_count', 0))]
        ]
        
        results_table = Table(results_info, colWidths=[2*inch, 4*inch])
        results_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(results_table)
        
        return elements
    
    def _create_cot_analysis(self, query_data: Dict[str, Any]) -> List:
        """Create Chain-of-Thought analysis section"""
        elements = []
        
        # Section title
        title = Paragraph("Chain-of-Thought Analysis", self.styles['CustomSubtitle'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Agent workflow
        workflow_title = Paragraph("Agent Workflow", self.styles['CustomSection'])
        elements.append(workflow_title)
        
        agent_timings = query_data.get('agent_timings', {})
        if agent_timings:
            workflow_data = [["Agent", "Duration (ms)", "Status", "Details"]]
            
            for agent, timing in agent_timings.items():
                workflow_data.append([
                    agent.upper(),
                    str(timing.get('duration_ms', 0)),
                    timing.get('status', 'unknown'),
                    str(timing.get('details', {}))
                ])
            
            workflow_table = Table(workflow_data, colWidths=[1.5*inch, 1*inch, 1*inch, 2.5*inch])
            workflow_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(workflow_table)
            elements.append(Spacer(1, 20))
        
        # LLM Interactions
        llm_title = Paragraph("LLM Interactions", self.styles['CustomSection'])
        elements.append(llm_title)
        
        llm_interactions = query_data.get('llm_interactions', [])
        if llm_interactions:
            llm_data = [["Type", "Model", "Duration (ms)", "Tokens"]]
            
            for interaction in llm_interactions:
                llm_data.append([
                    interaction.get('type', 'N/A'),
                    interaction.get('model', 'N/A'),
                    str(interaction.get('duration_ms', 0)),
                    str(interaction.get('tokens_used', 0))
                ])
            
            llm_table = Table(llm_data, colWidths=[1.5*inch, 2*inch, 1*inch, 1*inch])
            llm_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightyellow),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(llm_table)
        
        return elements
    
    def _create_results_analysis(self, query_data: Dict[str, Any]) -> List:
        """Create results analysis section"""
        elements = []
        
        # Section title
        title = Paragraph("Query Results & Analysis", self.styles['CustomSubtitle'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Results table
        results = query_data.get('results', [])
        if results:
            # Convert to DataFrame for easier handling
            df = pd.DataFrame(results)
            
            # Create table data
            table_data = [df.columns.tolist()]  # Header
            table_data.extend(df.values.tolist()[:50])  # First 50 rows
            
            # Create table
            results_table = Table(table_data, colWidths=[2*inch] * len(df.columns))
            results_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(results_table)
            
            # Show total count
            total_text = Paragraph(
                f"<b>Total Records:</b> {len(results)} (showing first 50)",
                self.styles['Normal']
            )
            elements.append(total_text)
        else:
            no_results = Paragraph("No results found for this query.", self.styles['Normal'])
            elements.append(no_results)
        
        return elements
    
    def _create_security_validation(self, query_data: Dict[str, Any]) -> List:
        """Create security and validation section"""
        elements = []
        
        # Section title
        title = Paragraph("Security & Validation", self.styles['CustomSubtitle'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Security guards
        guards_title = Paragraph("Security Guards Applied", self.styles['CustomSection'])
        elements.append(guards_title)
        
        guards = query_data.get('guards', {}).get('guards_applied', [])
        if guards:
            guards_data = [["Guard Type", "Description", "Status"]]
            
            for guard in guards:
                guards_data.append([
                    guard.get('type', 'N/A'),
                    guard.get('description', 'N/A'),
                    guard.get('status', 'N/A')
                ])
            
            guards_table = Table(guards_data, colWidths=[2*inch, 3*inch, 1*inch])
            guards_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(guards_table)
        else:
            no_guards = Paragraph("No security guards were applied.", self.styles['Normal'])
            elements.append(no_guards)
        
        return elements
    
    def _create_performance_metrics(self, query_data: Dict[str, Any]) -> List:
        """Create performance metrics section"""
        elements = []
        
        # Section title
        title = Paragraph("Performance Metrics", self.styles['CustomSubtitle'])
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Timing breakdown
        timing_title = Paragraph("Timing Breakdown", self.styles['CustomSection'])
        elements.append(timing_title)
        
        timing_data = [
            ["Component", "Duration (ms)", "Percentage"],
            ["Total Time", str(query_data.get('total_time_ms', 0)), "100%"],
            ["LLM Time", str(query_data.get('total_llm_time_ms', 0)), 
             f"{(query_data.get('total_llm_time', 0) / query_data.get('total_time', 1) * 100):.1f}%"],
            ["VectorDB Time", str(query_data.get('total_vectordb_time_ms', 0)),
             f"{(query_data.get('total_vectordb_time', 0) / query_data.get('total_time', 1) * 100):.1f}%"],
            ["Database Time", str(query_data.get('total_database_time_ms', 0)),
             f"{(query_data.get('total_database_time', 0) / query_data.get('total_time', 1) * 100):.1f}%"]
        ]
        
        timing_table = Table(timing_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
        timing_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(timing_table)
        
        return elements

def create_query_data_for_pdf(query_data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare query data for PDF export"""
    return {
        'timestamp': query_data.get('timestamp', datetime.now().isoformat()),
        'user': query_data.get('user', 'Unknown'),
        'role': query_data.get('role', 'Unknown'),
        'query': query_data.get('query', 'N/A'),
        'sql': query_data.get('sql', 'N/A'),
        'summary': query_data.get('summary', 'No summary available'),
        'results': query_data.get('results', []),
        'results_count': len(query_data.get('results', [])),
        'query_time': query_data.get('query_time', 0.0),
        'guards': query_data.get('guards', {}),
        'guards_count': query_data.get('guards', {}).get('total_guards', 0),
        'agent_timings': query_data.get('agent_timings', {}),
        'llm_interactions': query_data.get('llm_interactions', []),
        'total_time': query_data.get('total_time', 0.0),
        'total_time_ms': query_data.get('total_time_ms', 0),
        'total_llm_time': query_data.get('total_llm_time', 0.0),
        'total_llm_time_ms': int(query_data.get('total_llm_time', 0.0) * 1000),
        'total_vectordb_time': query_data.get('total_vectordb_time', 0.0),
        'total_vectordb_time_ms': int(query_data.get('total_vectordb_time', 0.0) * 1000),
        'total_database_time': query_data.get('total_database_time', 0.0),
        'total_database_time_ms': int(query_data.get('total_database_time', 0.0) * 1000)
    }
