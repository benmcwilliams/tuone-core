```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-01570-08650") and reject-phase = false
sort location, company asc
```
