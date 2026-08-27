class FakeEmbedder:
    """Temporary stub — returns a fixed dummy vector so the pipeline can be
    proven end-to-end while the real Bedrock Titan quota increase is pending.
    Swap back to BedrockEmbeddingClient once quota is granted."""

    model_id = "amazon.titan-embed-text-v2:0"
    embedding_version = "stub-v1"

    async def embed(self, text: str) -> list[float]:
        return [0.0] * 1024
