```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-01464-09545") and reject-phase = false
sort location, company asc
```
