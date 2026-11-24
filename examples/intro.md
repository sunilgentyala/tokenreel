A hash map stores keys and values. First we hash the key. Then we jump to a bucket. Lookup cost is O(1) on average, where load = n / m.

```python
d = {}
d["a"] = 1
```
