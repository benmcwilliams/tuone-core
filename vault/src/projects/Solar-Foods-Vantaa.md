```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FIN-02411-02446") and reject-phase = false
sort location, company asc
```
