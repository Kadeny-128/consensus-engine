AI Lead Identification Engine (Drug Discovery)

A V1 prototype of an agentic swarm for identifying and verifying pharmaceutical drug targets.

Link to project: [https://consensus-engine.streamlit.app](https://consensus-engine.streamlit.app)

# How It's Made

Tech used: Python, Streamlit, Cerebras Inference API, Llama 3.1-70b, RDKit, Git/GitHub.

I built this engine to solve a specific problem in early-stage drug discovery: hallucination. Standard LLMs will happily invent molecules that violate the laws of physics. The industry needs a system that could "fact-check" itself before presenting a candidate.

To achieve this, I architected a multi-agent swarm system**:
1.  The Discovery Agent: Scours for potential protein targets and mechanisms of action.
2.  The Audit Agent: Acts as an adversarial "Skeptic." It cross-references claims against known chemical constraints (using RDKit logic) to catch errors.
3.  The Synthesis Agent: Merges the findings into a verified consensus report.

The backend uses a Directed Acyclic Graph (DAG) workflow in Python. I chose Cerebras Inference for the LLM backend because the extreme speed allows for multiple "research loops" in seconds rather than minutes, which is critical for high-velocity iteration. The frontend is built in Streamlit for rapid deployment and easy visualization of the agent logs.

# Optimizations

One major challenge was the "Cold Start" problem on the cloud. The chemistry library (RDKit) requires specific Linux system dependencies (`libxrender1`) which aren't present on standard serverless containers.
* System-Level Dependency Injection: I implemented a `packages.txt` configuration to inject the required Linux graphics libraries into the container at build time, preventing runtime crashes.
* Secret Management: I secured the API keys using environment variables and a strict `.gitignore` policy to prevent leaking credentials, while using Streamlit's secrets management for the production deployment.
* Agent Partitioning: I separated the logic into distinct modules (`phases/`) to allow for independent scaling—I can upgrade the "Audit" logic without breaking the "Discovery" logic.

# Lessons Learned

This project taught me the importance of infrastructure-as-code. Getting the code to run on my local Mac was easy, but deploying it to the cloud exposed hidden dependencies (like the Linux graphics drivers for RDKit) that I hadn't anticipated.

I also learned that more agents ≠ better results. Initially, I thought about adding more complex loops, but I found that a tight, linear consensus loop (Discovery -> Audit -> Synthesis) produced higher quality output than a messy "brainstorming" swarm. It reinforced that structure is just as important as the model itself in agentic AI.
