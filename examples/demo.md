A hash map stores keys and values for fast lookup. First hash the key. Then jump to the bucket. Finally compare the stored key.

Lookup cost is O(1) on average, where load = n / m.

```python
cache = {}
cache["user"] = 42  # store
print(cache["user"])
```
