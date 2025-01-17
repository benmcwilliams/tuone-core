```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ESP-02319-08052") and reject-phase = false
sort location, company asc
```
