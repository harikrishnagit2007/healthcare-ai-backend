from huggingface_hub import snapshot_download

local_path = snapshot_download(
    repo_id="bert-base-uncased"
)

print("Model downloaded to:", local_path)