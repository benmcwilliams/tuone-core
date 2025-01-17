```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GRC-02847-02999") and reject-phase = false
sort location, company asc
```
