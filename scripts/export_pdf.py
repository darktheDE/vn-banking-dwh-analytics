"""Script to export proposal.md into proposal.pdf with a LaTeX-style cover page.
"""

import os
import re
import warnings
from pathlib import Path
from fpdf import FPDF

# Suppress fpdf2 warnings
warnings.simplefilter("ignore")

class ProposalPDF(FPDF):
    def __init__(self, metadata=None):
        super().__init__()
        self.metadata = metadata or {}
        
        # Load Times New Roman Unicode fonts from Windows
        font_dir = Path("C:/Windows/Fonts")
        self.reg_font = str(font_dir / "times.ttf") if (font_dir / "times.ttf").exists() else None
        self.bold_font = str(font_dir / "timesbd.ttf") if (font_dir / "timesbd.ttf").exists() else None
        self.ital_font = str(font_dir / "timesi.ttf") if (font_dir / "timesi.ttf").exists() else None
        self.bi_font = str(font_dir / "timesbi.ttf") if (font_dir / "timesbi.ttf").exists() else None
        
        if self.reg_font:
            # Choose a unique non-core name like 'Times_VN'
            self.font_family = "Times_VN"
            self.add_font(self.font_family, "", self.reg_font)
            if self.bold_font:
                self.add_font(self.font_family, "B", self.bold_font)
            if self.ital_font:
                self.add_font(self.font_family, "I", self.ital_font)
            if self.bi_font:
                self.add_font(self.font_family, "BI", self.bi_font)
        else:
            self.font_family = "Helvetica"  # Fallback
            
    def header(self):
        # No header on cover page (page 1)
        if self.page_no() > 1:
            self.set_font(self.font_family, "I", 9)
            self.set_text_color(128, 128, 128)
            # Use fixed width self.epw and reset X
            self.multi_cell(self.epw, 10, "Đề xuất nghiên cứu khoa học - Nhóm 2 - Hệ thống phân tích tài chính ngân hàng Việt Nam", align="R")
            self.set_x(self.l_margin)
            self.ln(2)

    def footer(self):
        # No footer on cover page (page 1)
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font(self.font_family, "I", 9)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f"Trang {self.page_no()}", 0, 0, "C")

    def draw_cover_page(self):
        self.add_page()
        # Draw a beautiful LaTeX-style border
        self.set_line_width(0.5)
        self.rect(10, 10, 190, 277)
        self.rect(11, 11, 188, 275) # Double border
        
        # School / Department
        self.set_y(25)
        self.set_font(self.font_family, "B", 13)
        self.multi_cell(self.epw, 7, self.metadata.get("university", "TRƯỜNG ĐẠI HỌC CÔNG NGHỆ KỸ THUẬT THÀNH PHỐ HỒ CHÍ MINH"), align="C")
        self.set_x(self.l_margin)
        self.set_font(self.font_family, "B", 12)
        self.multi_cell(self.epw, 7, self.metadata.get("department", "BỘ MÔN HỆ THỐNG THÔNG TIN"), align="C")
        self.set_x(self.l_margin)
        
        # Decorative line
        self.ln(5)
        self.set_line_width(0.8)
        self.line(40, self.get_y(), 170, self.get_y())
        
        # Document Type
        self.set_y(80)
        self.set_font(self.font_family, "B", 20)
        self.multi_cell(self.epw, 10, self.metadata.get("title", "ĐỀ XUẤT NGHIÊN CỨU KHOA HỌC"), align="C")
        self.set_x(self.l_margin)
        
        # Subject / Course
        self.ln(5)
        self.set_font(self.font_family, "I", 13)
        self.multi_cell(self.epw, 10, self.metadata.get("subject", "Môn học: Phân tích Dữ liệu (Data Analysis)"), align="C")
        self.set_x(self.l_margin)
        
        # Project Title
        self.set_y(120)
        self.set_font(self.font_family, "B", 15)
        self.multi_cell(self.epw, 8, self.metadata.get("project", ""), align="C")
        self.set_x(self.l_margin)
        
        # Authors / Group Info
        self.set_y(190)
        self.set_font(self.font_family, "B", 12)
        self.set_x(50)
        self.multi_cell(self.epw - 40, 7, self.metadata.get("group", "Nhóm thực hiện: Nhóm 2"), align="L")
        self.set_x(self.l_margin)
        
        self.set_font(self.font_family, "", 12)
        members = self.metadata.get("members", [])
        for m in members:
            self.set_x(55)
            self.multi_cell(self.epw - 45, 6, f"- {m}", align="L")
            self.set_x(self.l_margin)
            
        # Date & Location at the bottom
        self.set_y(260)
        self.set_font(self.font_family, "", 11)
        self.multi_cell(self.epw, 10, self.metadata.get("date", "Thành phố Hồ Chí Minh, Năm 2026"), align="C")
        self.set_x(self.l_margin)

def parse_markdown_proposal(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Split YAML metadata
    metadata = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            yaml_content = parts[1]
            body = parts[2]
            
            # Simple YAML parsing
            for line in yaml_content.split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key == "members":
                        metadata[key] = []
                    elif key == "":
                        continue
                    else:
                        metadata[key] = val
                elif line.strip().startswith("-") and "members" in metadata:
                    member_name = line.strip().lstrip("-").strip().strip('"').strip("'")
                    metadata["members"].append(member_name)

    return metadata, body

def export_proposal_to_pdf():
    proposal_md = Path("docs/proposal.md")
    proposal_pdf_path = Path("docs/proposal.pdf")
    
    if not proposal_md.exists():
        print(f"Proposal markdown file not found at: {proposal_md}")
        return False
        
    metadata, body = parse_markdown_proposal(proposal_md)
    pdf = ProposalPDF(metadata)
    
    # 1. Generate cover page
    pdf.draw_cover_page()
    
    # 2. Add main content page
    pdf.add_page()
    pdf.set_y(25)
    
    lines = body.split("\n")
    skip_title_headers = True  # Skip the first few markdown headers that duplicate the cover info
    
    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            # Empty line, add a little space
            pdf.ln(3)
            continue
            
        if line_strip.startswith("---"):
            # Separator line, draw a neat light-grey line
            pdf.ln(2)
            pdf.set_draw_color(200, 200, 200)
            pdf.set_line_width(0.2)
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
            pdf.ln(4)
            continue
            
        if line_strip.startswith("# "):
            if skip_title_headers:
                continue
            # Main Title (Heading 1)
            pdf.ln(5)
            pdf.set_font(pdf.font_family, "B", 18)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(pdf.epw, 8, line_strip.lstrip("# ").strip())
            pdf.set_x(pdf.l_margin)
            pdf.ln(4)
            
        elif line_strip.startswith("## "):
            if skip_title_headers and ("RESEARCH PROPOSAL" in line_strip or "Phân tích Dữ liệu" in line_strip):
                continue
            skip_title_headers = False  # Start printing from Section 1 onwards
            
            # Section Title (Heading 2)
            pdf.ln(4)
            pdf.set_font(pdf.font_family, "B", 14)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(pdf.epw, 8, line_strip.lstrip("## ").strip())
            pdf.set_x(pdf.l_margin)
            pdf.ln(2)
            
        elif line_strip.startswith("- "):
            # Bullet point
            pdf.set_font(pdf.font_family, "", 12)
            pdf.set_text_color(50, 50, 50)
            text = line_strip.lstrip("- ").strip()
            pdf.multi_cell(pdf.epw, 6, f"  •  {text}")
            pdf.set_x(pdf.l_margin)
            
        else:
            # Paragraph text
            pdf.set_font(pdf.font_family, "", 12)
            pdf.set_text_color(50, 50, 50)
            pdf.multi_cell(pdf.epw, 6, line_strip)
            pdf.set_x(pdf.l_margin)
            
    # Save the output file
    pdf.output(str(proposal_pdf_path))
    print(f"Academic proposal PDF exported successfully to: {proposal_pdf_path}")
    return True

if __name__ == "__main__":
    export_proposal_to_pdf()
