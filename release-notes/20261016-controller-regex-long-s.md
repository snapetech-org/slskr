---
category: fixed
audience: users, operators
area: controller-parity
action: none
breaking: false
---
Case-insensitive regex filters now follow each controller profile's upstream Unicode behavior: the native profile matches long s with ASCII `s`, while legacy behavior is preserved.
