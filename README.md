"# AIOps VirtualBox Agents" 


Quick Start

python3 -m venv myenv
source myenv/bin/activate 
pip install psutil langchain-ollama langchain-core langchain-community
ollama pull llama3.2
python aiops_monitor.py

Running the security auditor
$ ollama pull qwen2.5-coder:1.5b
