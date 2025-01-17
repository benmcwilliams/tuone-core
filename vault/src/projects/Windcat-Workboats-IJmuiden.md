```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-06441-10435") and reject-phase = false
sort location, company asc
```
