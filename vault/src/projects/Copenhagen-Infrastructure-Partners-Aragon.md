```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ESP-02237-01555") and reject-phase = false
sort location, company asc
```
