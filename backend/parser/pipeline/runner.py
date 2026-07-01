import json
import os
import uuid
from parser.pipeline.stage1_ingestion import detect_pdf_type
from parser.pipeline.stage2_extract import extract
from parser.pipeline.stage3_merge import merge
from parser.pipeline.stage4_llm import extract_structured
from parser.pipeline.stage5_validate import validate
from parser.pipeline.stage6_store import store, init_db
from parser import config


async def run_pipeline(pdf_path: str) -> dict:
    # 0. Initialize database tables asynchronously before parsing starts
    await init_db()

    print("--- Stage 1: Ingestion & Type Detection ---")
    print(f"Ingesting file: {pdf_path}")

    stage1_result = detect_pdf_type(pdf_path)

    if not stage1_result["success"]:
        print("Classification Failed!")
        print(f"  Error Type: {stage1_result['error_type']}")
        print(f"  Details: {stage1_result['message']}")
        return {"stage1": stage1_result}

    print("Classification Succeeded!")
    print(f"  Is Digital PDF: {stage1_result['is_digital']}")

    pipeline_result = {"stage1": stage1_result}

    if stage1_result["is_digital"]:
        print("\n--- Stage 2: Digital PDF Extraction ---")
        stage2_result = extract(pdf_path)
        pipeline_result["stage2"] = stage2_result

        warnings = stage2_result.get("extraction_warnings", [])
        if warnings:
            print(f"  Warnings: {warnings}")

        text_len = len(stage2_result["raw_text"]) if stage2_result["raw_text"] else 0
        links_count = (
            len(stage2_result["raw_links"]) if stage2_result["raw_links"] else 0
        )
        meta = stage2_result["metadata"]

        print(f"  Extracted Text Length: {text_len} characters")
        print(f"  Extracted Raw Links: {links_count} links found")

        print("\n--- Stage 3: Pre-merge & Link Enrichment ---")
        stage3_result = merge(stage2_result, pdf_path)
        pipeline_result["stage3"] = stage3_result

        print("  Enriched Embedded Links:")
        for el in stage3_result["embedded_links"]:
            print(
                f"    - URL: {el['url']} | Anchor: '{el['anchor_text']}' | Type: {el['type']} | Page: {el['page_number']}"
            )

        print("  Plain-text URLs Detected (Deduplicated):")
        for tu in stage3_result["text_urls"]:
            print(
                f"    - URL: {tu['url']} | Type: {tu['type']} | Source: {tu['source']}"
            )

        print("\n--- Stage 4: LLM Structured Extraction ---")
        stage4_result = await extract_structured(stage3_result)
        pipeline_result["stage4"] = stage4_result

        if stage4_result["parse_status"] == "success":
            print(f"  Extraction Succeeded! (Provider: {stage4_result['provider']})")
            print("  Stage 4 Parsed JSON:")
            print(json.dumps(stage4_result["parsed"], indent=2, ensure_ascii=False))
        else:
            print(f"  Extraction Failed! Status: {stage4_result['parse_status']}")
            print(f"  Reason: {stage4_result.get('reason')}")

        print("\n--- Stage 5: Validation & Confidence Scoring ---")
        stage5_result = await validate(
            stage4_result, stage3_result["text"], stage3_result
        )
        pipeline_result["stage5"] = stage5_result

        print(f"  Validation Status: {stage5_result['parse_status']}")

        if stage5_result["parse_status"] == "success":
            parsed = stage5_result["validated"]
            personal = parsed.get("personal") or {}
            print(f"    Name: {personal.get('name')}")
            print(f"    Email: {personal.get('email')}")
            skills = parsed.get("skills") or {}
            print(f"    Skills (first 5 technical): {skills.get('technical', [])[:5]}")
            print(f"    Experience: {len(parsed.get('experience', []))} entries")
            print(f"    Education:  {len(parsed.get('education', []))} entries")
            print(f"    Projects:   {len(parsed.get('projects', []))} entries")
        else:
            print(f"    Error: {stage5_result.get('error_details')}")

        print("\n--- Stage 6: Database Storage ---")
        candidate_uuid = str(uuid.uuid4())
        print(f"  Storing Candidate ID: {candidate_uuid}")

        stage6_result = await store(stage5_result, candidate_uuid)
        pipeline_result["stage6"] = stage6_result

        if stage6_result["parse_status"] == "store_failed":
            print(f"  Storage Failed! Reason: {stage6_result.get('reason')}")
        else:
            print("  Storage Succeeded!")
            print(f"    Record ID: {stage6_result['record_id']}")
            print(f"    Database URL: {config.DATABASE_URL}")
            print(f"    Stored At: {stage6_result['stored_at']}")

        doc_title = meta.get("title") if meta else None
        if not doc_title or not doc_title.strip():
            doc_title = os.path.basename(pdf_path)
        print(f"\n  Document Title: {doc_title}")
    else:
        print("\n--- Stage 2: Scanned PDF Extraction ---")
        print("  Scanned PDF detected. OCR path (Tesseract) will run here.")
        pipeline_result["stage2"] = {
            "raw_text": None,
            "raw_links": [],
            "metadata": None,
            "extraction_warnings": ["OCR extraction path not yet implemented"],
        }
        pipeline_result["stage3"] = {
            "text": "",
            "embedded_links": [],
            "text_urls": [],
            "metadata": None,
        }

    return pipeline_result
