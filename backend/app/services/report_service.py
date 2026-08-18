import os
import uuid
from datetime import datetime, timezone
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.config import settings
from app.models.detection import Detection
from app.utils.logger import logger


class ReportService:
    @staticmethod
    def generate_pdf_report(detection: Detection, user_email: str = "System User", remarks: str = "") -> str:
        """Generate the server-side technical inspection evidence report."""
        report_dir = settings.abs_report_dir
        os.makedirs(report_dir, exist_ok=True)
        pdf_filename = f"evtclip_detection_{detection.id}_{uuid.uuid4().hex[:8]}.pdf"
        pdf_full_path = os.path.join(report_dir, pdf_filename)

        doc = SimpleDocTemplate(
            pdf_full_path,
            pagesize=letter,
            rightMargin=30,
            leftMargin=30,
            topMargin=34,
            bottomMargin=34,
            title=f"EVT-CLIP inspection {detection.id}",
            author="Vision Text Anomaly Detection",
        )

        # UI/report palette. The PDF stays readable when printed in grayscale.
        NIGHT = colors.HexColor("#0F172A")
        SLATE = colors.HexColor("#475569")
        MUTED = colors.HexColor("#64748B")
        LINE = colors.HexColor("#D8E0EA")
        SOFT = colors.HexColor("#F7F9FC")
        ORANGE = colors.HexColor("#FC4C02")
        MAGENTA = colors.HexColor("#D629B8")
        PERIWINKLE = colors.HexColor("#7773E6")
        CYAN = colors.HexColor("#0891B2")
        GREEN = colors.HexColor("#15803D")
        AMBER = colors.HexColor("#B45309")
        RED = colors.HexColor("#C81E3A")

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ReportTitle", parent=styles["Heading1"], fontSize=20, leading=22,
            textColor=NIGHT, fontName="Helvetica-Bold", spaceAfter=1,
        )
        subtitle_style = ParagraphStyle(
            "ReportSubtitle", parent=styles["Normal"], fontSize=9.4, leading=12,
            textColor=MUTED,
        )
        section_heading = ParagraphStyle(
            "SectionHeading", parent=styles["Heading2"], fontSize=13.2, leading=16,
            textColor=NIGHT, fontName="Helvetica-Bold", spaceBefore=2, spaceAfter=6,
        )
        small = ParagraphStyle(
            "Small", parent=styles["Normal"], fontSize=8.1, leading=10.5,
            textColor=SLATE,
        )
        tiny = ParagraphStyle(
            "Tiny", parent=styles["Normal"], fontSize=6.9, leading=8.6,
            textColor=MUTED,
        )
        label = ParagraphStyle(
            "Label", parent=small, fontName="Helvetica-Bold", textColor=colors.HexColor("#334155"),
        )
        white_small = ParagraphStyle(
            "WhiteSmall", parent=small, textColor=colors.white, fontSize=7.7, leading=9.4,
        )
        white_bold = ParagraphStyle(
            "WhiteBold", parent=white_small, fontName="Helvetica-Bold", fontSize=9.2, leading=11,
        )

        def safe_text(value, fallback="-"):
            if value is None or value == "":
                value = fallback
            return escape(str(value))

        def fmt_float(value, digits=4, suffix=""):
            if value is None:
                return "-"
            return f"{float(value):.{digits}f}{suffix}"

        def absolute_upload_path(rel_path: str | None):
            if not rel_path:
                return None
            candidate = os.path.realpath(os.path.join(settings.BASE_DIR, rel_path))
            upload_root = os.path.realpath(settings.abs_upload_dir)
            try:
                if os.path.commonpath([candidate, upload_root]) != upload_root:
                    return None
            except ValueError:
                return None
            return candidate if os.path.isfile(candidate) else None

        def image_flow(rel_path: str | None, width=238, height=145):
            candidate = absolute_upload_path(rel_path)
            if not candidate:
                return Paragraph("Image unavailable", tiny)
            try:
                return RLImage(candidate, width=width, height=height, kind="proportional")
            except Exception:
                return Paragraph("Image could not be rendered", tiny)

        def image_pair(left_title, left_path, right_title, right_path, image_height=145):
            data = [
                [Paragraph(f"<b>{safe_text(left_title)}</b>", label), Paragraph(f"<b>{safe_text(right_title)}</b>", label)],
                [image_flow(left_path, height=image_height), image_flow(right_path, height=image_height)],
            ]
            table = Table(data, colWidths=[261, 261])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF2F7")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.45, LINE),
                ("PADDING", (0, 0), (-1, 0), 4.5),
                ("PADDING", (0, 1), (-1, 1), 5),
            ]))
            return table

        def page_decor(canvas, _doc):
            canvas.saveState()
            width, height = letter
            seg = width / 3
            canvas.setFillColor(ORANGE); canvas.rect(0, height - 5, seg, 5, stroke=0, fill=1)
            canvas.setFillColor(MAGENTA); canvas.rect(seg, height - 5, seg, 5, stroke=0, fill=1)
            canvas.setFillColor(PERIWINKLE); canvas.rect(seg * 2, height - 5, seg, 5, stroke=0, fill=1)
            canvas.setStrokeColor(colors.HexColor("#E2E8F0")); canvas.setLineWidth(.5)
            canvas.line(30, 24, width - 30, 24)
            canvas.setFont("Helvetica", 6.8); canvas.setFillColor(colors.HexColor("#94A3B8"))
            canvas.drawString(30, 14, "EVT-CLIP · Inspection evidence")
            canvas.drawRightString(width - 30, 14, f"Page {_doc.page}")
            canvas.restoreState()

        if not detection.result_valid:
            status_label, status_key, status_color = "INPUT REJECTED", "invalid", PERIWINKLE
        elif detection.prediction == "Anomalous":
            status_label, status_key, status_color = "ANOMALY DETECTED", "anomaly", RED
        else:
            status_label, status_key, status_color = "NORMAL", "normal", GREEN

        created_str = (
            detection.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            if detection.created_at
            else datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        )
        threshold = 0.267 if detection.threshold is None else float(detection.threshold)

        bbox = None
        if detection.defect_bbox_width and detection.defect_bbox_height:
            bbox = (
                f"x={detection.defect_bbox_x}, y={detection.defect_bbox_y}, "
                f"w={detection.defect_bbox_width}, h={detection.defect_bbox_height}"
            )

        selected_category = (detection.category or "-").replace("_", " ").title()
        closest_category = (detection.predicted_category or "-").replace("_", " ").title()
        coverage = float(detection.defect_area_fraction or 0.0) * 100.0

        elements = [
            Paragraph(f"<b>{safe_text(settings.PROJECT_NAME)}</b>", title_style),
            Paragraph("Industrial Anomaly Inspection · Evidence Report", subtitle_style),
            Spacer(1, 7),
        ]

        status_banner = Table([
            [Paragraph(status_label, white_bold), Paragraph(f"Detection #{detection.id} · {safe_text(selected_category)}", white_small)],
        ], colWidths=[300, 222])
        status_banner.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), status_color),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        elements.extend([status_banner, Spacer(1, 7)])

        metric_cells = [
            ("Decision score", fmt_float(detection.anomaly_score), MAGENTA),
            ("Mask coverage", f"{coverage:.2f}%", ORANGE),
            ("CPU total", fmt_float(detection.inference_time, 2, " s"), CYAN),
            ("Validation", "Accepted" if detection.result_valid else "Rejected", GREEN if detection.result_valid else PERIWINKLE),
        ]
        metric_row = []
        for name, value, accent in metric_cells:
            metric_row.append(Paragraph(f"<font color='{accent.hexval()}'><b>{safe_text(value)}</b></font><br/><font size='6.6' color='#64748B'>{safe_text(name)}</font>", small))
        metric_table = Table([metric_row], colWidths=[130.5] * 4)
        metric_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SOFT),
            ("BOX", (0, 0), (-1, -1), .5, LINE),
            ("INNERGRID", (0, 0), (-1, -1), .4, LINE),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.extend([metric_table, Spacer(1, 7)])

        pipeline = [
            ("01", "Validate", CYAN),
            ("02", "Specialists", PERIWINKLE),
            ("03", "Stage-2", MAGENTA),
            ("04", "Stage-3", ORANGE),
            ("05", "Decision", GREEN),
        ]
        pipeline_row = []
        for number, name, accent in pipeline:
            pipeline_row.append(Paragraph(f"<font color='{accent.hexval()}'><b>{number}</b></font>  <b>{name}</b>", tiny))
        pipeline_table = Table([pipeline_row], colWidths=[104.4] * 5)
        pipeline_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FBFCFE")),
            ("BOX", (0, 0), (-1, -1), .45, LINE),
            ("INNERGRID", (0, 0), (-1, -1), .35, LINE),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.extend([pipeline_table, Spacer(1, 8)])

        friendly_decision_source = (
            "PatchCore specialist decision" if "patchcore" in str(detection.decision_source or "")
            else "EfficientAD specialist decision" if "efficientad" in str(detection.decision_source or "")
            else "Localization fallback decision" if detection.decision_source == "localization_area_fallback"
            else "Recorded backend decision"
        )
        friendly_route = {
            "stage3_stable": "Stable Stage-3 refinement",
            "stage2_fallback": "Stage-2 fallback",
            "specialist_only": "Specialist-only route",
        }.get(detection.route, "Recorded route")
        friendly_localization = (
            "EVT-CLIP Stage-3 localization" if "stage3" in str(detection.localization_source or "")
            else "Stage-2 fused localization" if "stage2" in str(detection.localization_source or "")
            else "Recorded localization path"
        )
        friendly_cache = {
            "cold_pair": "First run - specialist pair loaded",
            "warm_pair": "Warm pair - models reused",
            "partial_warm": "Partially warm",
        }.get(detection.worker_cache, "Runtime cache state")
        friendly_validator = (
            "Reference-centroid category validator" if "centroid" in str(detection.category_validator or "")
            else "Portable OpenCLIP category check + open-set guard" if detection.category_validator
            else "Not recorded"
        )

        summary_rows = [
            ["Report time", created_str, "Operator", user_email],
            ["Inspection profile", detection.dataset_name or "MVTec AD Industrial Inspection", "Selected category", selected_category],
            ["Validated category", closest_category, "Input quality", (detection.image_quality_state or "ok").replace("_", " ").title()],
            ["Primary specialist", "EfficientAD" if detection.primary_specialist == "efficientad" else "PatchCore" if detection.primary_specialist == "patchcore" else detection.primary_specialist, "Decision source", friendly_decision_source],
            ["Route", friendly_route, "Localization", friendly_localization],
            ["Stage-3 threshold", f"{threshold:.3f}", "Worker cache", friendly_cache],
        ]
        meta_data = []
        for lt, lv, rt, rv in summary_rows:
            meta_data.append([
                Paragraph(f"<b>{safe_text(lt)}</b>", label), Paragraph(safe_text(lv), small),
                Paragraph(f"<b>{safe_text(rt)}</b>", label), Paragraph(safe_text(rv), small),
            ])
        meta_table = Table(meta_data, colWidths=[84, 177, 84, 177])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SOFT),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 4.2),
            ("GRID", (0, 0), (-1, -1), 0.38, LINE),
        ]))
        elements.extend([meta_table, Spacer(1, 8)])

        elements.extend([
            Paragraph("Final production output", section_heading),
            image_pair("Original image", detection.original_image_path, "Final anomaly heatmap", detection.heatmap_path if detection.result_valid else None, image_height=132),
            Spacer(1, 6),
            image_pair("Segmentation mask", detection.mask_path if detection.result_valid else None, "Final overlay", detection.overlay_path if detection.result_valid else None, image_height=132),
        ])

        if detection.result_valid:
            elements.extend([
                PageBreak(),
                Paragraph("Model-stage evidence", section_heading),
                Paragraph("Stored worker outputs are shown in pipeline order. These are not browser-generated replacements.", small),
                Spacer(1, 6),
                image_pair("Preprocessed input", detection.preprocessed_path, "EfficientAD heatmap", detection.efficientad_heatmap_path, image_height=145),
                Spacer(1, 6),
                image_pair("PatchCore heatmap", detection.patchcore_heatmap_path, "Stage-2 fusion heatmap", detection.stage2_heatmap_path, image_height=145),
                Spacer(1, 6),
                image_pair("Stage-3 EVT-CLIP heatmap", detection.stage3_heatmap_path, "Accepted final heatmap", detection.heatmap_path, image_height=145),
                Spacer(1, 6),
                image_pair("OpenCV evidence (benchmark-gated)", detection.classical_cv_heatmap_path, "Hybrid map", detection.hybrid_heatmap_path, image_height=145),
                Spacer(1, 6),
                image_pair("YOLO / ROI mask (optional)", detection.yolo_roi_mask_path, "Accepted final heatmap", detection.heatmap_path, image_height=145),
            ])

        elements.extend([
            PageBreak(),
            Paragraph("Localization and runtime evidence", section_heading),
        ])
        if detection.result_valid:
            elements.extend([
                image_pair("Defect location from final mask", detection.bbox_overlay_path, "Final overlay", detection.overlay_path, image_height=137),
                Spacer(1, 8),
            ])

        analysis_rows = [
            ["Mask pixels", detection.defect_area_pixels or 0, "Mask coverage", f"{coverage:.2f}%"],
            ["Connected regions", detection.defect_component_count or 0, "Bounding box", bbox or "No accepted defect pixels"],
            ["EfficientAD score", fmt_float(detection.efficientad_image_score), "PatchCore score", fmt_float(detection.patchcore_image_score)],
            ["Stage-2 peak", fmt_float(detection.stage2_map_score), "Stage-3 peak", fmt_float(detection.stage3_map_score)],
            ["OpenCV evidence", fmt_float(detection.classical_cv_score), "Hybrid map peak", fmt_float(detection.hybrid_map_score)],
            ["Hybrid mode", detection.hybrid_mode or "off", "Fusion applied", "Yes" if detection.hybrid_applied else "No"],
            ["YOLO ROI", detection.yolo_roi_state or "disabled", "YOLO confidence", fmt_float(detection.yolo_roi_confidence)],
            ["CV defect hint", detection.classical_cv_defect_hint or "-", "CV time", fmt_float(detection.classical_cv_seconds, 3, " s")],
            ["Map agreement", fmt_float((detection.map_agreement or 0.0) * 100, 2, "%") if detection.map_agreement is not None else "-", "Threshold", f"{threshold:.3f}"],
            ["Validation time", fmt_float(detection.validation_seconds, 3, " s"), "EfficientAD time", fmt_float(detection.efficientad_seconds, 3, " s")],
            ["PatchCore time", fmt_float(detection.patchcore_seconds, 3, " s"), "EVT-CLIP time", fmt_float(detection.refiner_seconds, 3, " s")],
            ["Image quality", detection.image_quality_state, "Quality notice", detection.image_quality_message],
            ["Category validator", friendly_validator, "Category notice", detection.category_validation_message],
        ]
        analysis_data = []
        for lt, lv, rt, rv in analysis_rows:
            analysis_data.append([
                Paragraph(f"<b>{safe_text(lt)}</b>", label), Paragraph(safe_text(lv), small),
                Paragraph(f"<b>{safe_text(rt)}</b>", label), Paragraph(safe_text(rv), small),
            ])
        analysis_table = Table(analysis_data, colWidths=[84, 177, 84, 177])
        analysis_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), SOFT),
            ("PADDING", (0, 0), (-1, -1), 4.5),
            ("GRID", (0, 0), (-1, -1), 0.38, LINE),
        ]))
        elements.extend([analysis_table, Spacer(1, 6)])
        raw_route = safe_text(detection.route or "-")
        raw_decision = safe_text(detection.decision_source or "-")
        raw_localization = safe_text(detection.localization_source or "-")
        elements.extend([
            Paragraph(
                f"Technical identifiers: route={raw_route} · decision_source={raw_decision} · localization={raw_localization}",
                tiny,
            ),
            Spacer(1, 7),
        ])

        ground_truth_copy = (
            "Ground truth is not included for ordinary uploads or camera images. "
            "IoU, Dice, pixel accuracy, ROC and precision-recall metrics require labelled evaluation data and are reported separately in the research benchmark."
        )
        policy_table = Table([
            [Paragraph("<b>Ground-truth policy</b>", label), Paragraph(ground_truth_copy, small)],
            [Paragraph("<b>System context</b>", label), Paragraph(
                "Production scope: Bottle, Cable, Capsule, Metal Nut and Pill. The live hybrid pipeline uses category specialists, calibrated Stage-2 fusion and EVT-CLIP Stage-3 refinement. Published EVT-CLIP paper metrics and medical zero-shot experiments are kept separate from this inspection record.",
                small,
            )],
        ], colWidths=[105, 417])
        policy_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FCFCFE")),
            ("BOX", (0, 0), (-1, -1), .45, LINE),
            ("INNERGRID", (0, 0), (-1, -1), .35, LINE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.extend([policy_table])

        elements.extend([
            PageBreak(),
            Paragraph("Research benchmark context", section_heading),
            Paragraph(
                "These tables provide evaluation and published research context. They do not replace the current inspection score and they do not create per-image ground truth.",
                small,
            ),
            Spacer(1, 7),
        ])

        project_eval = [
            ["Category", "Known-product Pixel F1", "Unseen/LOCO Pixel F1"],
            ["Bottle", "81.54%", "57.54%"],
            ["Cable", "79.06%", "38.77%"],
            ["Capsule", "59.18%", "30.89%"],
            ["Metal Nut", "93.95%", "76.90%"],
            ["Pill", "87.09%", "55.14%"],
            ["Average", "80.17%", "51.85%"],
        ]
        project_table = Table(project_eval, colWidths=[170, 176, 176])
        project_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NIGHT),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F1F5F9")),
            ("GRID", (0, 0), (-1, -1), 0.4, LINE),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ]))
        elements.extend([
            Paragraph("Our five-category evaluation", label),
            Spacer(1, 4),
            project_table,
            Spacer(1, 12),
        ])

        paper_eval = [
            ["Published EVT-CLIP dataset", "AUROC", "PRO", "AP", "F1-max"],
            ["MVTec-AD", "98.53%", "94.36%", "78.29%", "73.53%"],
            ["VisA", "98.75%", "94.13%", "58.25%", "58.13%"],
        ]
        paper_table = Table(paper_eval, colWidths=[176, 86.5, 86.5, 86.5, 86.5])
        paper_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PERIWINKLE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, LINE),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ]))
        elements.extend([
            Paragraph("Published EVT-CLIP paper benchmark", label),
            Spacer(1, 4),
            paper_table,
            Spacer(1, 7),
            Paragraph(
                "Published paper metrics are research evidence. The deployed five-category hybrid application keeps its own evaluation table separate.",
                small,
            ),
        ])

        note = remarks or "EVT-CLIP inspection report."
        elements.extend([
            Spacer(1, 13),
            Paragraph("Operator note", section_heading),
            Table(
                [[Paragraph(safe_text(note), small)]],
                colWidths=[522],
                style=TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), SOFT),
                    ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                    ("PADDING", (0, 0), (-1, -1), 8),
                ]),
            ),
        ])

        doc.build(elements, onFirstPage=page_decor, onLaterPages=page_decor)
        logger.info("Generated inspection PDF report: %s", pdf_full_path)
        return os.path.join(settings.REPORT_DIR, pdf_filename).replace("\\", "/")
