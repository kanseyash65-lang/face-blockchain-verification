# Face Identification & Blockchain Verification

A pipeline that takes a face photo, identifies who it's likely of, searches the open web for a real matching post, verifies that the candidate image genuinely shows the same face, and writes a tamper-evident record of that finding to a public blockchain.

## Pipeline

```
Face image
  → Face detection & encoding (DeepFace + MTCNN)
  → Reverse image search (Google Cloud Vision Web Detection API)
  → Entity identification (who Google's own recognition says the photo is of)
  → Candidate matches re-checked with face verification (DeepFace)
    + a name-corroboration check against the page title/URL
  → Metadata (matched URL, platform, timestamp, match status) hashed with SHA-256
  → Hash written to a smart contract on Polygon Amoy (testnet)
  → Hash read back from the contract and compared to the original
```

Every result is labeled **VERIFIED** (face check + name corroboration both passed) or **UNVERIFIED** (no candidate passed both checks, falling back to the closest available result) — this status is recorded honestly inside the hashed metadata itself, not just printed to the console.

## Blockchain used

**Polygon Amoy** (public testnet). A minimal Solidity smart contract (`HashRegistry.sol`) stores each submitted hash along with a timestamp and the submitting wallet address, and exposes a read function to fetch any record back by ID.

Deployed contract address: `0x5342811Cb7fd60a79Fe9F2219AcC5914679275aa`
Explorer: https://amoy.polygonscan.com/address/0x5342811Cb7fd60a79Fe9F2219AcC5914679275aa

## Project structure

```
face_module/       — face detection & encoding (DeepFace, MTCNN)
search_module/      — Google Vision web search, entity ID, candidate extraction
hash_module/        — metadata building + SHA-256 hashing
chain_module/       — web3.py client: writes to and reads from the contract
blockchain_module/  — Hardhat project used to write and deploy HashRegistry.sol
main.py             — CLI entry point, runs the full pipeline end-to-end
app.py              — small Flask API exposing the pipeline over HTTP
index.html          — standalone dashboard UI (drag-and-drop demo front end)
```

## How to run it

### Prerequisites
- Python 3.11 (3.14 is not yet compatible with the DeepFace/TensorFlow dependency chain)
- Node.js (only needed if you want to redeploy the contract yourself; not required to run the pipeline)
- A Google Cloud account with the Cloud Vision API enabled and an API key
- A funded wallet on Polygon Amoy testnet (free test POL from https://faucet.polygon.technology/)

### Setup

1. Clone the repo and create a Python virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # macOS/Linux
   ```

2. Install dependencies:
   ```bash
   pip install deepface requests python-dotenv web3 flask flask-cors
   ```

3. Create a `.env` file in the project root with:
   ```
   GOOGLE_VISION_API_KEY=your_google_vision_api_key
   WALLET_PRIVATE_KEY=your_wallet_private_key
   ```

4. The smart contract is already deployed (address above), so no redeployment is needed. To deploy your own instance instead, see `blockchain_module/` (a Hardhat project) and update `CONTRACT_ADDRESS` in `chain_module/chain_writer.py`.

### Running the pipeline (command line)

```bash
python main.py <path_to_face_image>
```

Runs all five stages end-to-end and prints progress for each step, ending with a summary and an on-chain verification result.

### Running the dashboard (optional)

The dashboard is a bonus front end, not required by the task, but shows the same pipeline running through a browser UI with drag-and-drop upload.

1. Start the API server (leave it running):
   ```bash
   python app.py
   ```
2. Open `index.html` directly in a browser (no build step, no separate server needed for the page itself).
3. Drop a photo — it calls the real pipeline via the local API and displays the genuine result (identified entity, match status, hash, and a link to the matched page).

## Known limitations

- **Depends on the photo being indexed online.** Since this relies on reverse image search, it can only find results for photos already published somewhere Google has indexed. It cannot say anything about a person with no public photo footprint.
- **Verification reduces false positives but doesn't eliminate them.** Face verification (DeepFace) combined with a name-corroboration check (does the identified name appear in the candidate page's title/URL) substantially cuts down on false matches compared to search results alone, but automated face verification on low-resolution crawled thumbnails is not perfect — an unverified fallback is used honestly whenever nothing clears both checks, rather than forcing a weak result through as confirmed.
- **"Identified" means Google's own entity recognition, not a proprietary model.** The person's name comes from Google Cloud Vision's `webEntities` field; this project does not train or run its own identity-classification model.
- **Testnet only.** The blockchain component runs on Polygon Amoy, a public testnet, not mainnet — a deliberate choice for a free, fully reproducible hackathon demo. The verification mechanism (write, then independently read back and compare) works identically on mainnet with the same contract code.
