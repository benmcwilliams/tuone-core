```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "CHE-02881-07131") and reject-phase = false
sort location, company asc
```
