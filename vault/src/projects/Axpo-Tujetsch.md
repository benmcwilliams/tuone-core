```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "CHE-08043-02161") and reject-phase = false
sort location, company asc
```
