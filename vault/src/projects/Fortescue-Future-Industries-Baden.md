```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "DEU-00054-02236") and reject-phase = false
sort location, company asc
```
