```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "IRL-08682-01626") and reject-phase = false
sort location, company asc
```
