```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ESP-04906-02101") and reject-phase = false
sort location, company asc
```
