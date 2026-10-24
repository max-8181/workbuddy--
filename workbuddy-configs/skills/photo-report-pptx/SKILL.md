---
name: photo-report-pptx
description: Generate a standard editable .pptx presentation from user-provided photos or images, especially for school/project reports. Trigger when the user uploads/reference image files (JPG/PNG) and asks to create a slideshow, report PPT, or presentation based on the photo content.
---

# Photo Report PPTX

Generate a PowerPoint presentation from uploaded photos/images using the `pptx-generator` skill.

## Workflow

1. **Read all images**
   - Use the `Read` tool on every image path the user provides.
   - Extract text, diagrams, tables, measurements, names, and any handwritten notes.

2. **Design the slide outline**
   - Typical structure for a school project report:
     - Cover (title + subtitle)
     - Agenda/table of contents
     - Project background / problem
     - Team & roles
     - Design concept
     - Experiment / investigation
     - Data table
     - Product/result photos
     - Findings & conclusion
     - Future improvements
     - Thank you / Q&A
   - Adapt the outline to whatever the photos actually show.

3. **Write `slides.json`**
   - Save it under `<workspace>/output/slides.json`.
   - Use absolute paths for any `image` slide `image_path` entries.
   - Pick a style suited for the audience (`academic_white` for school reports, `creative_purple` for lighter topics, `business_blue` for formal reports).
   - Leave placeholders for missing data (e.g., blank decibel values) so the user can fill them in.

4. **Generate the PPTX**
   - Use the managed Python runtime preferred by the environment.
   - If `pptx` module is missing, create a venv and install `python-pptx`:
     ```bash
     <managed_python> -m venv <python_root>/envs/pptx
     <venv>/Scripts/pip.exe install python-pptx
     <venv>/Scripts/python.exe <pptx-generator>/scripts/generate_pptx.py slides.json --out <output_dir>/report.pptx
     ```

5. **Verify output**
   - Check that the file exists and has a reasonable size.
   - Count slides and embedded images with python-pptx if needed.

6. **Present**
   - Call `present_files` with the final `.pptx` path.
   - Mention the page count and any placeholders the user still needs to fill.

## Common Pitfalls

- **Relative `output` field in JSON**: pass `--out <absolute_path>` to control where the file is saved.
- **Missing `pptx` module**: always install into an isolated venv; do not pollute the global environment.
- **Unreadable handwriting**: transcribe the best you can and flag uncertain names/numbers for the user to verify.
- **Too much text per slide**: keep bullet points short; use tables and image slides for dense information.
