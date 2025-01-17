```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-03652-02499") and reject-phase = false
sort location, company asc
```
