# AI Assignment – Content Framework Prototype

## Overview
This repository contains a **prototype implementation of a content framework** built as part of an AI assignment. The primary objective of this project is to demonstrate **system design, reasoning flow, and implementation approach** for generating structured content outputs using a Large Language Model (LLM).

The system is intentionally designed to be **model-agnostic and extensible**, allowing easy upgrades to stronger models for improved accuracy and reasoning performance.

---

## Model Used
- **LLM:** `Qwen-3-4B-2507-Instruct`
- **Deployment:** Local (offline)
- **Reasoning Capability:** Limited (lightweight model)

> Note: This model was chosen due to limited system access and time constraints. The architecture supports seamless replacement with more powerful models to significantly enhance accuracy and output quality.

---

## Key Objectives
- Build a structured **content framework generation system**
- Demonstrate **prompt engineering and output formatting**
- Ensure **reproducibility and clarity of results**
- Design a pipeline that performs well even with **low-reasoning LLMs**
- **Feedback** loop for improvements

---

## Features
- Modular and extensible architecture
- Clean separation of:
  - Input parsing
  - Prompt construction
  - LLM inference
  - Output validation
- Generates structured outputs in **Excel format**
- Designed to scale with stronger LLMs without code refactoring
