```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "IRL-10231-02033") and reject-phase = false
sort location, company asc
```
