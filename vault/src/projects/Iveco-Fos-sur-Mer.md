```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FRA-02623-02324") and reject-phase = false
sort location, company asc
```
