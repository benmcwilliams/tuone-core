```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ESP-02167-02075") and reject-phase = false
sort location, company asc
```
