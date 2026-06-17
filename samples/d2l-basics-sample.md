# Deep learning basics (sample corpus)

Short notes for trying chunking and retrieval before you run `scripts/sync_d2l_en.py`.

## Tensors and storage

Deep learning frameworks represent data as **tensors**: often N-dimensional arrays with a dtype and a device (CPU/GPU). How tensors are **stored** (strides, views, contiguous memory) affects performance when you slice or transpose.

## Automatic differentiation

**Autograd** tracks operations on tensors so gradients can be computed for optimization. In practice you build a computation graph (or use a tape) and call backward on a scalar loss.

## A tiny linear model

A single linear layer maps inputs to outputs with a weight matrix and bias. Training adjusts those parameters to reduce a loss (for example mean squared error on regression tasks).
