# Future Plan: Reinforcement Learning from Human Feedback (RLHF)

## Goal
Implement a pipeline to capture the explicit user feedback (thumbs up/down) already present in the UI, and use this data to fine-tune the open-source LLMs (like Llama 3 8B) running via Groq. The goal is to incrementally improve the model's accuracy in generating SQL and answering questions over time through Direct Preference Optimization (DPO).

---

## Phase 1: Data Collection & Curation (The "Preference Dataset")

Before training, we must systematically collect training pairs (chosen vs. rejected responses) from the user interactions.

1. **Feedback Capture Mechanism**:
   - The UI currently has thumbs up/down buttons (`FeedbackButtons.jsx`). We need to ensure that every feedback event logs the full context.
   - **Data Required**:
     - System Prompt / Context (Schema + Definitions)
     - User Text Input (The question)
     - The Generated SQL Query (The response)
     - The Feedback Score (1 for up, -1 for down)

2. **Storage and Extraction (`data_pipeline`)**:
   - The SQLite database already stores chat history and feedback out-of-the-box.
   - Create a new background job or CLI script (e.g., `scripts/export_rlhf_dataset.py`) to query the SQLite logs.
   - For every **Thumbs Down** (-1), we need a corresponding "Good" answer to form a paired preference dataset.
   - **Creating the "Chosen" label**: 
     - When a user gives a thumbs down, how do we know the right answer? We need an administrator workflow to *correct* the bad SQL, or we can use subsequent successful user queries as the "chosen" positive example.

3. **Dataset Format**:
   Format the exported sqlite data into the standard HuggingFace preference dataset JSONL format:
   ```json
   {
     "prompt": "List the top 5 doctors by Rx volume in region X...",
     "chosen": "SELECT hcp_name ...",
     "rejected": "SELECT name FROM ..." 
   }
   ```

---

## Phase 2: Offline Fine-Tuning Pipeline (DPO)

Because LLMs accessed via the Groq API cannot be fine-tuned *live on their servers*, we must fine-tune the model offline and then either deploy the tuned model locally (vLLM/Ollama) or upload the LoRA adapters to a managed inference provider that supports fine-tuned weights.

1. **Direct Preference Optimization (DPO)**:
   - DPO is lighter and more stable than traditional PPO-based RLHF because it doesn't require training a separate reward model.
   - **Framework**: Use [Unsloth](https://github.com/unslothai/unsloth) or HuggingFace `TRL` (Transformer Reinforcement Learning) for rapid LoRA fine-tuning.

2. **Training Script**:
   - Build a `notebooks/dpo_finetuning.ipynb` runbook.
   - Steps:
     1. Load base model (e.g., `meta-llama/Meta-Llama-3-8B-Instruct`).
     2. Load the exported JSONL preference dataset.
     3. Apply DPO configuration (LoRA config, beta=0.1, low learning rate).
     4. Train for 1-3 epochs.
     5. Save the LoRA adapters.

---

## Phase 3: Deployment of the Tuned Model

1. **Inference Hosting**:
   - Groq does not currently support custom fine-tuned LoRA weights.
   - **Alternative A**: Deploy the fine-tuned model via [Together AI](https://www.together.ai/) or [Anyscale](https://www.anyscale.com/), which allow uploading custom LoRA weights and have OpenAI-compatible APIs. 
   - **Alternative B**: Host it locally using `vLLM` or `Ollama` if GPU resources are available.

2. **Updating PharmaIQ**:
   - Update `app/config.py` in the backend to point to the new inference provider.
   - Because we abstract tool calling cleanly, the app will continue to work seamlessly, just with a smarter, fine-tuned underlying generation engine.

---

## Summary of Actionable Steps

- [ ] **Step 1:** Extend `eval_and_metrics/schema.py` to ensure failed SQL is captured cleanly.
- [ ] **Step 2:** Write `export_dpo_dataset.py` to extract positive and negative paired examples.
- [ ] **Step 3:** Set up an Unsloth DPO training script running on a cloud GPU (e.g., Colab/RunPod) to ingest this data.
- [ ] **Step 4:** Deploy the fine-tuned model to Together AI and update the application API keys.
