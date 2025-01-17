```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "DNK-00220-02506") and reject-phase = false
sort location, company asc
```
