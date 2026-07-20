Add support for exporting reports in **Markdown** format.

The system already exports reports in text and CSV. Keep existing behavior
unchanged and add support for format key `markdown`.

Markdown output should look like this:

```text
# Quarterly Metrics

| Name | Value |
| --- | --- |
| Latency | 120ms |
| Errors | 3 |
```
