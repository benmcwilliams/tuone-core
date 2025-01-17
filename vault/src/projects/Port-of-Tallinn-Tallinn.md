```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "EST-02381-02407") and reject-phase = false
sort location, company asc
```
