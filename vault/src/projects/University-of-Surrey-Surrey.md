```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GBR-02783-10301") and reject-phase = false
sort location, company asc
```
