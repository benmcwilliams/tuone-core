```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "ESP-05071-02345") and reject-phase = false
sort location, company asc
```
