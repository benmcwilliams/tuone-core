```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "CHE-04747-02263") and reject-phase = false
sort location, company asc
```
