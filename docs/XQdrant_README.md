# XQdrant

## Objective

By default, qdrant doesn't explain why a certain entry is similar to another entry with cosine similarity, right ? Well for biology, knowing the biological features making two proteins similar is a huge boost and an actual necessity. The main point is to explain why is this protein similar to this, in biology vocab.

## Implementation

that's why we forked the Qdrant repo and introduced a new rust module called **explainabilty.rs** that takes two vectors and a similarity search function (like cosine similarity) and returns the top 10 dimensions that contributed to these two proteins being similar. Then I added an optionnal field in the requests input and an output. the optional field is:

**with_explanation = False**

when set to True, here is a sample output:

{
"result":[{"id":0,"version":1,"score":0.9999999,"score_explanation":{"top_dimensions":[{"dimension":1160,"contribution":0.87828344},{"dimension":234,"contribution":0.059287537},{"dimension":736,"contribution":0.0019410067},{"dimension":381,"contribution":0.00095407123},{"dimension":786,"contribution":0.0006379474},{"dimension":836,"contribution":0.0006314053},{"dimension":683,"contribution":0.0006029652},{"dimension":644,"contribution":0.000539327},{"dimension":145,"contribution":0.0005284306},{"dimension":967,"contribution":0.0005145053}]}}, ...]
... }

So now we know which dimensions contribute the most ! but these dimensions are still just numbers, but not random numbers. continue to [Interpretability](./interpretability_README.md) readme for the followup.

## Reproducing

reproducing is not hard if you worked with rust before. just clone the repo and run
cargo build --release 

or just
cargo build

for quick testing. Once built, run this:

./target/release/qdrant-server.exe

and there you go, you can try ingesting your own data and send a request like this one:

curl -X POST "http://localhost:6333/collections/structures/points/search" \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [...]
    "limit": 10,
    "with_explanation": true
  }'
