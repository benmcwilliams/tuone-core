```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-08063-02164") and reject-phase = false
sort location, company asc
```
