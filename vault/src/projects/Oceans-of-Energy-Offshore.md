```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-02274-09634") and reject-phase = false
sort location, company asc
```
