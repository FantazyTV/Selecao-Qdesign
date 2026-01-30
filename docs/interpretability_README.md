# Interpretability

As we said in [XQdrant](./XQdrant_README.md), now we have the dimensions contributing the most to similarity. The interpretabilty folder documents the work we did to reach a real, semantic biological meaning from these dimensions.

## Before we dive in

Embedders aren't random. There's a whole science to finding the meaning behind embedded dimensions. We wanted to see what ESM2 really "knows" about proteins.

## Our Journey

We started by grabbing protein sequences from CIF files. Then we ran them through ESM2 to get embeddings. Next, we pulled out biological properties like secondary structure, surface exposure, and flexibility from the structures.

We trained simple probes—linear models—to predict these properties from the embeddings. This showed us which dimensions mattered for each property. We looked at overlaps between properties and plotted correlations.

In the end, we mapped dimensions to biological meanings and saved the results. 

All the work here was inspired by this paper: https://www.biorxiv.org/content/10.1101/2024.11.14.623630v1.full.pdf , we wouldn't have been able to do this without it.

Check the notebook for the full story. 