```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "NLD-03188-10050") and reject-phase = false
sort location, company asc
```
