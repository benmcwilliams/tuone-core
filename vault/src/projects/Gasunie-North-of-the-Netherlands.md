```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-03495-02248") and reject-phase = false
sort location, company asc
```
